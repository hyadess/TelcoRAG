"""
Pure, network-free helpers for the hierarchical retriever.

Keeping these as standalone functions (no embedder, no Pinecone) makes the
coarse-to-fine filtering and the neighbour-expansion decision logic trivially
unit-testable, which is where the subtle bugs live.

Two independent concerns:

  * MULTI-LEVEL FILTERING  — group candidates by document, then chapter, then
    section (any configured subset, outermost first), keep the top groups at
    each level, and add a small decaying score bonus reflecting how highly the
    kept groups ranked. ``apply_levels`` does this generically.

  * NEIGHBOUR EXPANSION    — decide, from a hit's relevance, whether to look at
    its reading-order neighbours, and which contiguous neighbours to splice in.
    ``classify_relevance`` / ``select_passing_neighbors`` / ``build_continuation``
    are the pure pieces; the retriever supplies the actual neighbour scores.
"""

import math
from typing import Any, Dict, List, Tuple

# Canonical containment order. A level key is always qualified by its parents
# so that, e.g., "Licensing" in two different chapters are distinct sections.
HIERARCHY_ORDER = ["doc_name", "chapter", "section"]


# =============================================================================
# Grouping / ranking
# =============================================================================

def level_key(chunk: Dict[str, Any], field: str) -> Tuple[str, ...]:
    """Cumulative, parent-qualified key for a chunk at the given level field.

    e.g. field='section' -> (doc_name, chapter, section);
         field='chapter' -> (doc_name, chapter);
         field='doc_name' -> (doc_name,).
    Falls back to keying on just ``field`` if it isn't in HIERARCHY_ORDER.
    """
    if field in HIERARCHY_ORDER:
        fields = HIERARCHY_ORDER[: HIERARCHY_ORDER.index(field) + 1]
    else:
        fields = [field]
    return tuple(str(chunk.get(f, "")) for f in fields)


def group_by(chunks: List[Dict[str, Any]], field: str) -> Dict[Tuple[str, ...], List[Dict[str, Any]]]:
    """Group chunks by their cumulative key at ``field``."""
    groups: Dict[Tuple[str, ...], List[Dict[str, Any]]] = {}
    for c in chunks:
        groups.setdefault(level_key(c, field), []).append(c)
    return groups


def rank_groups(
    groups: Dict[Tuple[str, ...], List[Dict[str, Any]]],
    count_bonus: float = 0.25,
    score_field: str = "score",
) -> List[Tuple[Tuple[str, ...], float]]:
    """Rank groups by ``max(member) + count_bonus * mean(member)`` descending."""
    ranked = []
    for key, members in groups.items():
        scores = [float(m.get(score_field, 0.0)) for m in members]
        if not scores:
            continue
        s = max(scores) + count_bonus * (sum(scores) / len(scores))
        ranked.append((key, s))
    ranked.sort(key=lambda kv: kv[1], reverse=True)
    return ranked


def apply_levels(
    candidates: List[Dict[str, Any]],
    levels: List[Dict[str, Any]],
    count_bonus: float = 0.25,
    level_bonus: float = 0.10,
    score_field: str = "score",
) -> List[Dict[str, Any]]:
    """Coarse-to-fine filtering across a configurable list of levels.

    Args:
        candidates: already-scored chunk dicts.
        levels: ordered (outermost first) list of ``{"field": str, "top_n": int}``.
            e.g. ``[{"field":"doc_name","top_n":3}, {"field":"chapter","top_n":4},
                    {"field":"section","top_n":5}]``.
        count_bonus: weight on a group's mean member score when ranking groups.
        level_bonus: per-level score bonus, decaying with the group's rank.

    Returns the surviving chunks, ordered by boosted score. Each chunk keeps its
    raw score under ``base_score`` and records its per-level rank under
    ``hier_<field>_rank``.
    """
    if not candidates:
        return []

    survivors = list(candidates)
    # Preserve the raw retrieval score before we start boosting.
    for c in survivors:
        c.setdefault("base_score", float(c.get(score_field, 0.0)))

    for level in levels:
        field = level.get("field", "section")
        top_n = int(level.get("top_n", 5))
        groups = group_by(survivors, field)
        ranked = rank_groups(groups, count_bonus=count_bonus, score_field="base_score")
        keep = ranked[:top_n]
        keep_keys = {k for k, _ in keep}
        rank_of = {k: i for i, (k, _) in enumerate(keep)}

        kept: List[Dict[str, Any]] = []
        for c in survivors:
            k = level_key(c, field)
            if k not in keep_keys:
                continue
            decay = 1.0 / (1 + rank_of.get(k, 0))
            c[score_field] = float(c.get(score_field, 0.0)) + level_bonus * decay
            c[f"hier_{field}_rank"] = rank_of.get(k, 0)
            kept.append(c)
        survivors = kept

    survivors.sort(key=lambda d: d.get(score_field, 0.0), reverse=True)
    return survivors


# ---- Back-compat shims (section-only) used by older call sites/tests --------

def section_key(chunk: Dict[str, Any]) -> Tuple[str, str, str]:
    return (chunk.get("doc_name", ""), chunk.get("chapter", ""), chunk.get("section", ""))


def group_by_section(chunks):
    return group_by(chunks, "section")


def rank_sections(groups, count_bonus: float = 0.25):
    return rank_groups(groups, count_bonus=count_bonus, score_field="score")


def apply_hierarchy(candidates, top_sections: int = 5, count_bonus: float = 0.25, section_bonus: float = 0.10):
    return apply_levels(
        candidates,
        levels=[{"field": "section", "top_n": top_sections}],
        count_bonus=count_bonus,
        level_bonus=section_bonus,
    )


# =============================================================================
# Neighbour expansion (pure decision logic)
# =============================================================================

def cosine(a: List[float], b: List[float]) -> float:
    """Cosine similarity between two equal-length vectors. 0 on degenerate input."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def classify_relevance(score: float, high: float, low: float) -> str:
    """Bucket a hit's relevance.

    >= high   -> "high"   : the answer is already in this chunk; no expansion.
    <= low    -> "low"    : the answer is not here at all; no expansion.
    otherwise -> "medium" : neighbours may complete the answer; expand.
    """
    if score >= high:
        return "high"
    if score <= low:
        return "low"
    return "medium"


def select_passing_neighbors(neighbor_scores: List[float], moderate: float) -> int:
    """Number of contiguous neighbours (nearest first) clearing ``moderate``.

    Expansion is a *standard continuation*: it stops at the first neighbour that
    fails the threshold, so the spliced context stays contiguous with the hit.
    """
    n = 0
    for s in neighbor_scores:
        if s >= moderate:
            n += 1
        else:
            break
    return n


def build_continuation(
    actual_text: str,
    prev_texts_nearest_first: List[str],
    next_texts_nearest_first: List[str],
) -> str:
    """Splice prev + actual + next into reading order (prev2, prev1, actual, next1, next2)."""
    parts = list(reversed(prev_texts_nearest_first)) + [actual_text] + list(next_texts_nearest_first)
    return "\n\n".join(p for p in parts if p)
