"""
RRF reranker — when the retrieval stage produces multiple ranked lists (one
per sub-query), fuse them via Reciprocal Rank Fusion instead of using a
cross-encoder.

This is faster and free, and works particularly well when query reformulation
already produces high-quality rankings — the cross-encoder has less to add.
"""

from typing import Any, Dict, List

from config.settings import SETTINGS
from core.registry import RERANKERS
from pipeline.stage3_retrieval.retrievers.hybrid import reciprocal_rank_fusion

from .base import BaseReranker


@RERANKERS.register("rrf")
class RRFReranker(BaseReranker):
    """
    Treats the input list as a single ranking and re-scores via RRF position.
    For multi-ranking RRF, the orchestrator must pass them in via `rerank_multi`.
    """

    def __init__(self, k: int = None):
        cfg = SETTINGS.pipeline.get("hybrid", {})
        self.k = k if k is not None else cfg.get("rrf_k", 60)

    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        if not documents:
            return []

        # Single-list mode: just use ranks from the input order.
        # The score becomes 1/(k+rank+1).
        scored = []
        for rank, d in enumerate(documents):
            entry = self._carry_fields(d, 1.0 / (self.k + rank + 1), rank)
            scored.append(entry)
        # Already in rank order, but be explicit
        scored.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored[:top_k]

    def rerank_multi(
        self,
        rankings: List[List[Dict[str, Any]]],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Multi-ranking RRF (preferred entry point).

        Args:
            rankings: list of ranked candidate lists.
        """
        fused = reciprocal_rank_fusion(rankings, k=self.k)
        out = [self._carry_fields(d, d["score"], i) for i, d in enumerate(fused[:top_k])]
        return out
