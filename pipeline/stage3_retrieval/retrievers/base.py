"""
Base class for retrievers.

A retriever takes a query string and returns a list of metadata dicts, each
with at least a `score` field. The retrieval pipeline fans out across query
variants, calls one retriever per variant, then merges and dedupes.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseRetriever(ABC):
    """All retrievers (vector, BM25, hybrid) implement this interface."""

    @abstractmethod
    def search(self, query: str, top_k: int = 30) -> List[Dict[str, Any]]:
        """
        Returns a list of metadata dicts, ordered by score descending.
        Each dict should contain the chunk's metadata fields plus a `score` field.
        """
        ...
