"""Dense vector retriever — wraps an embedder's .search() method."""

from typing import Any, Dict, List, Optional

from core.registry import EMBEDDERS, RETRIEVERS

from .base import BaseRetriever
from ..local_chunks import LocalChunkStore


@RETRIEVERS.register("vector")
class VectorRetriever(BaseRetriever):
    def __init__(
        self,
        embedder_name: Optional[str] = None,
        chunker: Optional[str] = None,
        local_store: Optional[LocalChunkStore] = None,
    ):
        """
        Args:
            embedder_name: which embedder to use. If None, the orchestrator must
                inject the embedder via `set_embedder()` before calling search().
            chunker: selects both the Pinecone namespace (on the injected
                embedder) and matching local chunk JSON used for enrichment.
        """
        self._embedder = None
        self.local_store = local_store or LocalChunkStore(chunker=chunker)
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
        matches = getattr(result, "matches", None)
        if matches is None and isinstance(result, dict):
            matches = result.get("matches", [])
        for match in matches or []:
            metadata = getattr(match, "metadata", None)
            match_id = getattr(match, "id", None)
            score = getattr(match, "score", None)
            if isinstance(match, dict):
                metadata = match.get("metadata", metadata)
                match_id = match.get("id", match_id)
                score = match.get("score", score)
            entry = dict(metadata or {})
            entry["id"] = match_id or entry.get("id", "")
            entry["score"] = float(score or 0.0)
            out.append(self.local_store.enrich(entry))
        return out
