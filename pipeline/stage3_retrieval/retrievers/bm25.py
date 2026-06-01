"""
BM25 keyword retriever.

Loads the persisted BM25 index from disk (built at ingestion time) and
returns top_k chunks for a query. Loading is lazy and cached on the instance.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from config.settings import BM25_INDEX_FILE, bm25_index_path
from core.registry import RETRIEVERS
from pipeline.stage2_indexing.bm25_index import BM25Index

from .base import BaseRetriever

logger = logging.getLogger("BM25Retriever")


@RETRIEVERS.register("bm25")
class BM25Retriever(BaseRetriever):
    def __init__(
        self,
        index_path: Optional[Union[str, Path]] = None,
        chunker: Optional[str] = None,
    ):
        # Explicit index_path wins; otherwise resolve from the chunker variant
        # (each chunker has its own BM25 corpus). Falls back to the legacy
        # global index file when neither is given.
        if index_path is not None:
            self.index_path = Path(index_path)
        elif chunker:
            self.index_path = bm25_index_path(chunker)
        else:
            self.index_path = BM25_INDEX_FILE
        self._index: Optional[BM25Index] = None

    def _ensure_loaded(self):
        if self._index is None:
            idx = BM25Index()
            ok = idx.load(self.index_path)
            if not ok:
                raise FileNotFoundError(
                    f"BM25 index not found at {self.index_path}. "
                    f"Run ingestion to build it."
                )
            self._index = idx

    def search(self, query: str, top_k: int = 30) -> List[Dict[str, Any]]:
        self._ensure_loaded()
        return self._index.search(query, top_k=top_k)
