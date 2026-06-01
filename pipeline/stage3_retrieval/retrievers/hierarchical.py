"""
Hierarchical (coarse-to-fine) retriever.

Legal/regulatory documents are deeply structured: document -> chapter ->
section -> subsection. An answer is usually concentrated in one part of that
tree and often spans adjacent subsections. A flat top-k vector search ignores
this. This retriever exploits the hierarchy in three modular stages:

  1. COARSE POOL — embed the query once, pull a broad candidate pool.

  2. MULTI-LEVEL FILTERING (modular) — filter the pool down the hierarchy:
     keep the top documents, then the top chapters within them, then the top
     sections within those. The levels (and how many to keep at each) are fully
     configurable; drop or reorder them in ``pipeline.yaml -> hierarchical.levels``.

  3. EXPANSION — two independent, configurable mechanisms:
       * SIBLING expansion: per surviving section, run a metadata-filtered query
         to surface relevant subsections the flat pool missed.
       * NEIGHBOUR expansion: for a hit whose relevance is *medium* (not clearly
         answered, not clearly irrelevant), score its reading-order neighbours
         (prev/next, up to N hops) and splice the contiguous ones that clear a
         moderate threshold into the hit (standard continuation). High-scoring
         hits already contain the answer; very low ones don't, so neither is
         expanded.

All scoring/grouping/decision logic lives in ``hierarchical_ops`` as pure
functions; this class only adds the embedder/Pinecone I/O.

Config (pipeline.yaml -> hierarchical):
    pool_factor          : broad-pool size = pool_factor * top_k
    count_bonus          : weight on a group's mean member score when ranking
    level_bonus          : score bonus added to chunks in a kept group (decays by rank)
    levels               : ordered list of {field, top_n} (outermost first)
    expand_siblings      : run filtered per-section queries
    sibling_level        : metadata field siblings are filtered on (default 'section')
    siblings_per_section : cap on siblings pulled per group
    expand_neighbors     : enable neighbour expansion
    neighbor_high        : >= -> answer already present, skip expansion
    neighbor_low         : <= -> answer absent, skip expansion
    neighbor_moderate    : neighbour must clear this to be spliced in
    neighbor_max_hops    : expand at most this many neighbours each side (prev/next)
"""

import logging
from typing import Any, Dict, List, Optional

from config.settings import SETTINGS
from core.registry import EMBEDDERS, RETRIEVERS

from .base import BaseRetriever
from .hierarchical_ops import (
    apply_levels,
    build_continuation,
    classify_relevance,
    cosine,
    group_by,
    rank_groups,
    select_passing_neighbors,
)
# Back-compat re-exports (older imports / docs referenced these names).
from .hierarchical_ops import (  # noqa: F401
    apply_hierarchy,
    group_by_section,
    rank_sections,
    section_key,
)

logger = logging.getLogger("HierarchicalRetriever")

_DEFAULT_LEVELS = [
    {"field": "doc_name", "top_n": 3},
    {"field": "chapter", "top_n": 4},
    {"field": "section", "top_n": 5},
]


@RETRIEVERS.register("hierarchical")
class HierarchicalRetriever(BaseRetriever):
    """Coarse-to-fine, structure-aware dense retriever with sibling + neighbour expansion."""

    def __init__(self, embedder_name: Optional[str] = None, chunker: Optional[str] = None):
        cfg = SETTINGS.pipeline.get("hierarchical", {})
        self.pool_factor = int(cfg.get("pool_factor", 3))
        self.count_bonus = float(cfg.get("count_bonus", 0.25))
        self.level_bonus = float(cfg.get("level_bonus", cfg.get("section_bonus", 0.10)))
        self.levels = cfg.get("levels", _DEFAULT_LEVELS)

        # Sibling expansion
        self.expand_siblings = bool(cfg.get("expand_siblings", True))
        self.sibling_level = str(cfg.get("sibling_level", "section"))
        self.siblings_per_section = int(cfg.get("siblings_per_section", 5))

        # Neighbour expansion
        self.expand_neighbors = bool(cfg.get("expand_neighbors", True))
        self.neighbor_high = float(cfg.get("neighbor_high", 0.65))
        self.neighbor_low = float(cfg.get("neighbor_low", 0.30))
        self.neighbor_moderate = float(cfg.get("neighbor_moderate", 0.40))
        self.neighbor_max_hops = int(cfg.get("neighbor_max_hops", 2))

        self._embedder = None
        if embedder_name:
            self._embedder = EMBEDDERS.build(embedder_name)
            self._embedder.initialize_db()

    def set_embedder(self, embedder) -> None:
        self._embedder = embedder

    # ------------------------------------------------------------------
    def _matches_to_dicts(self, result) -> List[Dict[str, Any]]:
        out = []
        for match in result["matches"]:
            entry = dict(match["metadata"])
            entry["id"] = match.get("id", entry.get("id", ""))
            entry["score"] = float(match["score"])
            out.append(entry)
        return out

    # ------------------------------------------------------------------
    # Sibling expansion (modular)
    # ------------------------------------------------------------------
    def _expand_siblings(self, query_vec, pool, top_keys) -> List[Dict[str, Any]]:
        """Pull missed subsections from each surviving group via a filtered query."""
        added: List[Dict[str, Any]] = []
        seen_ids = {c.get("id") for c in pool if c.get("id")}
        field = self.sibling_level
        # The kept-group keys are cumulative tuples; the filter value is the
        # innermost field component.
        for key in top_keys:
            value = key[-1] if isinstance(key, tuple) else key
            if not value:
                continue
            try:
                sibs = self._matches_to_dicts(
                    self._embedder.search_by_vector(
                        query_vec,
                        top_k=self.siblings_per_section,
                        filters={field: {"$eq": value}},
                    )
                )
            except Exception as e:
                logger.debug(f"Sibling expansion failed for {field}='{value}': {e}")
                continue
            for s in sibs:
                sid = s.get("id")
                if sid and sid in seen_ids:
                    continue
                if sid:
                    seen_ids.add(sid)
                s["sibling_expanded"] = True
                added.append(s)
        return added

    # ------------------------------------------------------------------
    # Neighbour expansion (modular)
    # ------------------------------------------------------------------
    def _expand_one_neighbor(self, chunk: Dict[str, Any], query_vec) -> Dict[str, Any]:
        """Splice contiguous, moderately-relevant prev/next chunks into a medium hit."""
        base = float(chunk.get("base_score", chunk.get("score", 0.0)))
        bucket = classify_relevance(base, self.neighbor_high, self.neighbor_low)
        chunk["neighbor_decision"] = bucket
        if bucket != "medium":
            return chunk

        prev_ids = list(chunk.get("prev_ids", []) or [])[: self.neighbor_max_hops]
        next_ids = list(chunk.get("next_ids", []) or [])[: self.neighbor_max_hops]
        if not prev_ids and not next_ids:
            return chunk

        fetched = {}
        try:
            fetched = self._embedder.fetch_vectors(prev_ids + next_ids)
        except Exception as e:
            logger.debug(f"Neighbour fetch failed: {e}")
            return chunk

        def score_side(ids):
            scores, texts = [], []
            for nid in ids:
                rec = fetched.get(nid)
                if not rec:
                    break
                scores.append(cosine(query_vec, rec.get("values", [])))
                texts.append(rec.get("metadata", {}).get("subsection_text", ""))
            return scores, texts

        prev_scores, prev_texts = score_side(prev_ids)
        next_scores, next_texts = score_side(next_ids)

        n_prev = select_passing_neighbors(prev_scores, self.neighbor_moderate)
        n_next = select_passing_neighbors(next_scores, self.neighbor_moderate)
        if n_prev == 0 and n_next == 0:
            return chunk

        merged = build_continuation(
            chunk.get("subsection_text", ""),
            prev_texts[:n_prev],
            next_texts[:n_next],
        )
        out = dict(chunk)
        out["subsection_text"] = merged
        out["neighbor_expanded"] = True
        out["neighbor_added"] = {
            "prev": prev_scores[:n_prev],
            "next": next_scores[:n_next],
        }
        return out

    # ------------------------------------------------------------------
    def search(self, query: str, top_k: int = 30) -> List[Dict[str, Any]]:
        if self._embedder is None:
            raise RuntimeError(
                "HierarchicalRetriever has no embedder. Pass `embedder_name` or call `set_embedder()`."
            )

        # 1. COARSE POOL
        pool_size = max(top_k * self.pool_factor, 60)
        query_vec = self._embedder.embed_query(query)
        pool = self._matches_to_dicts(
            self._embedder.search_by_vector(query_vec, top_k=pool_size)
        )
        if not pool:
            return []

        # 2. SIBLING expansion — needs the surviving innermost-level group keys.
        if self.expand_siblings:
            innermost = self.levels[-1]["field"] if self.levels else "section"
            ranked = rank_groups(group_by(pool, innermost), count_bonus=self.count_bonus)
            keep_n = next(
                (lvl["top_n"] for lvl in self.levels if lvl["field"] == innermost),
                5,
            )
            top_keys = [k for k, _ in ranked[:keep_n]]
            pool.extend(self._expand_siblings(query_vec, pool, top_keys))

        # 3. MULTI-LEVEL FILTERING (doc -> chapter -> section, configurable)
        ordered = apply_levels(
            pool,
            levels=self.levels,
            count_bonus=self.count_bonus,
            level_bonus=self.level_bonus,
        )
        ordered = ordered[:top_k]

        # 4. NEIGHBOUR expansion on the surviving hits
        if self.expand_neighbors:
            ordered = [self._expand_one_neighbor(c, query_vec) for c in ordered]

        return ordered
