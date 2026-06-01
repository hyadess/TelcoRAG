"""Pickle-backed cache for reranker results, keyed by (query, doc-set) hash."""

import hashlib
import json
import logging
import os
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Union

logger = logging.getLogger("CacheManager")


class RerankCacheManager:
    """
    Saves rerank results to disk so re-running the same query+chunks combo
    is free. The hash key includes the query string and the sorted doc IDs
    (so reordering chunks doesn't cause a miss, but a different chunk set does).
    """

    def __init__(self, cache_file: Union[str, Path]):
        self.file_path = Path(cache_file).resolve()
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, List[Dict]] = self._load()

    def _load(self) -> Dict:
        if not self.file_path.exists():
            return {}
        try:
            with open(self.file_path, "rb") as f:
                return pickle.load(f)
        except (EOFError, pickle.UnpicklingError) as e:
            logger.warning(f"Cache file corrupted ({e}); starting fresh.")
            return {}

    def _save(self):
        with open(self.file_path, "wb") as f:
            pickle.dump(self._cache, f)

    def _key(self, query: str, documents: List[Dict]) -> str:
        # Sort docs so the key is deterministic regardless of input order
        docs_sorted = sorted(documents, key=lambda d: d.get("id", ""))
        payload = json.dumps({"q": query, "d": docs_sorted}, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def get(self, query: str, documents: List[Dict]) -> Optional[List[Dict]]:
        return self._cache.get(self._key(query, documents))

    def set(self, query: str, documents: List[Dict], results: List[Dict]):
        self._cache[self._key(query, documents)] = results
        self._save()
