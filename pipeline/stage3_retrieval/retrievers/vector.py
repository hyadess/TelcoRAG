"""Dense vector retriever — wraps an embedder's .search() method."""

from typing import Any, Dict, List, Optional

from core.registry import EMBEDDERS, RETRIEVERS

from .base import BaseRetriever


@RETRIEVERS.register("vector")
class VectorRetriever(BaseRetriever):
    def __init__(self, embedder_name: Optional[str] = None, chunker: Optional[str] = None):
        """
        Args:
            embedder_name: which embedder to use. If None, the orchestrator must
                inject the embedder via `set_embedder()` before calling search().
            chunker: accepted for a uniform constructor signature across
                retrievers; unused here (the embedder already carries the
                chunker's namespace).
        """
        self._embedder = None
        if embedder_name:
            self._embedder = EMBEDDERS.build(embedder_name)
            self._embedder.initialize_db()

    def set_embedder(self, embedder) -> None:
        """Inject an already-built embedder (so it isn't re-initialized)."""
        self._embedder = embedder

    def search(self, query: str, top_k: int = 30) -> List[Dict[str, Any]]:
        if self._embedder is None:
            raise RuntimeError("VectorRetriever has no embedder. Pass `embedder_name` or call `set_embedder()`.")

        result = self._embedder.search(query, top_k=top_k)
        out = []
        for match in result["matches"]:
            entry = dict(match["metadata"])
            entry["score"] = float(match["score"])
            out.append(entry)
        return out
