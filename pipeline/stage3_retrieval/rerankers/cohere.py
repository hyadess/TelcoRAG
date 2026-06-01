"""Cohere reranker."""

from typing import Any, Dict, List, Optional

from clients.cohere_client import get_client
from config.settings import COHERE_CACHE_FILE, get_reranker_model
from core.registry import RERANKERS
from utils.cache_manager import RerankCacheManager

from .base import BaseReranker


@RERANKERS.register("cohere")
class CohereReranker(BaseReranker):
    def __init__(self, cache_manager: Optional[RerankCacheManager] = None):
        self.client = get_client()
        self.model = get_reranker_model("cohere")
        self.cache = cache_manager or RerankCacheManager(COHERE_CACHE_FILE)

    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        if not documents:
            return []

        cached = self.cache.get(query, documents)
        if cached:
            return cached

        contents = [self._format_doc_for_rerank(d) for d in documents]
        doc_map = dict(enumerate(documents))

        response = self.client.rerank(
            model=self.model,
            query=query,
            documents=contents,
            top_n=top_k,
        )

        results = [
            self._carry_fields(doc_map[r.index], r.relevance_score, r.index)
            for r in response.results
        ]
        self.cache.set(query, documents, results)
        return results
