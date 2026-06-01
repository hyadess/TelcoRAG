"""Passthrough reranker — sort by vector score, return top_k."""

from typing import Any, Dict, List

from core.registry import RERANKERS

from .base import BaseReranker


@RERANKERS.register("none")
class NoneReranker(BaseReranker):
    """Useful as a baseline to measure reranker impact."""

    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        if not documents:
            return []
        sorted_docs = sorted(documents, key=lambda d: d.get("score", 0), reverse=True)[:top_k]
        return [
            self._carry_fields(d, d.get("score", 0.0), 0) for d in sorted_docs
        ]
