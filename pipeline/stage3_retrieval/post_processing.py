"""
Post-processing on retrieved (and reranked) chunks.

These run AFTER reranking, in the order specified by `pipeline.yaml`'s
`post_processing` list. Each function takes a list of chunk dicts and returns
a (possibly shorter, possibly reordered) list of chunk dicts.

Three steps available:
  - dedupe: collapse duplicates by subsection_text, keeping the highest score.
  - relevance_filter: drop chunks below a relevance threshold.
  - mmr: Maximal Marginal Relevance — promote diverse top chunks.

MMR is optional and a bit slower (it embeds candidate texts using a simple
character-overlap distance to avoid an extra LLM call). Enable it only when
you see redundant chunks in your top results.
"""

import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger("PostProcessing")


# =============================================================================
# Dedupe
# =============================================================================

def dedupe_by_text(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Keep the highest-scoring entry per unique subsection_text."""
    if not chunks:
        return chunks

    best: Dict[str, Dict[str, Any]] = {}
    for c in chunks:
        text = c.get("subsection_text", "")
        if not text:
            continue
        # Compare on whichever score field is present
        score = c.get("relevance_score", c.get("score", 0))
        existing = best.get(text)
        existing_score = existing and (existing.get("relevance_score", existing.get("score", 0)))
        if existing is None or score > existing_score:
            best[text] = c

    out = list(best.values())
    removed = len(chunks) - len(out)
    if removed > 0:
        logger.info(f"Dedupe: removed {removed} duplicate chunks ({len(chunks)} → {len(out)})")
    return out


# =============================================================================
# Relevance filter
# =============================================================================

def filter_by_relevance(
    chunks: List[Dict[str, Any]],
    threshold: float = 0.01,
) -> List[Dict[str, Any]]:
    """Drop chunks whose `relevance_score` is below `threshold`."""
    if threshold <= 0:
        return chunks
    filtered = [c for c in chunks if c.get("relevance_score", 0) >= threshold]
    removed = len(chunks) - len(filtered)
    if removed > 0:
        logger.info(f"Relevance filter: removed {removed} chunks below {threshold}")
    return filtered


# =============================================================================
# MMR
# =============================================================================

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def _tokens(text: str) -> set:
    return set(_TOKEN_RE.findall((text or "").lower()))


def _jaccard(a: set, b: set) -> float:
    """Jaccard similarity between two token sets, in [0, 1]."""
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def maximal_marginal_relevance(
    chunks: List[Dict[str, Any]],
    lambda_: float = 0.7,
    top_k: int = None,
) -> List[Dict[str, Any]]:
    """
    Greedy MMR re-selection using token-Jaccard similarity for the diversity term.

    Args:
        chunks: chunks already sorted by relevance_score descending.
        lambda_: 0..1; weight on relevance vs diversity. 1.0 → pure relevance
            (no diversity), 0.0 → pure diversity (ignore relevance). Default 0.7.
        top_k: how many to keep. If None, keep all but reorder.

    Note: we use Jaccard here (not embeddings) to avoid a second model call.
    Good enough to break up near-duplicate chunks; not as principled as cosine
    similarity over embeddings but free.
    """
    if not chunks:
        return chunks
    if top_k is None or top_k > len(chunks):
        top_k = len(chunks)

    # Pre-tokenize once
    candidates = [
        {"chunk": c, "tokens": _tokens(c.get("subsection_text", "")),
         "score": c.get("relevance_score", c.get("score", 0))}
        for c in chunks
    ]

    selected: List[Dict[str, Any]] = []

    while candidates and len(selected) < top_k:
        best_i = 0
        best_score = -float("inf")
        for i, cand in enumerate(candidates):
            relevance = cand["score"]
            if not selected:
                mmr_score = relevance
            else:
                max_sim = max(_jaccard(cand["tokens"], s["tokens"]) for s in selected)
                mmr_score = lambda_ * relevance - (1 - lambda_) * max_sim
            if mmr_score > best_score:
                best_score = mmr_score
                best_i = i
        selected.append(candidates.pop(best_i))

    out = [s["chunk"] for s in selected]
    logger.info(f"MMR: selected {len(out)} chunks (λ={lambda_})")
    return out


# =============================================================================
# Pipeline runner
# =============================================================================

def run_post_processing(
    chunks: List[Dict[str, Any]],
    steps: List[str],
    relevance_threshold: float = 0.01,
    mmr_lambda: float = 0.7,
    mmr_top_k: int = None,
) -> List[Dict[str, Any]]:
    """
    Run the configured post-processing steps in order.

    Args:
        chunks: reranked candidate chunks.
        steps: ordered list of step names from pipeline.yaml. Unknown names are
            logged and skipped (so a typo doesn't kill the pipeline).
    """
    for step in steps:
        if step == "dedupe":
            chunks = dedupe_by_text(chunks)
        elif step == "relevance_filter":
            chunks = filter_by_relevance(chunks, relevance_threshold)
        elif step == "mmr":
            chunks = maximal_marginal_relevance(chunks, lambda_=mmr_lambda, top_k=mmr_top_k)
        else:
            logger.warning(f"Unknown post_processing step: '{step}' — skipping")
    return chunks
