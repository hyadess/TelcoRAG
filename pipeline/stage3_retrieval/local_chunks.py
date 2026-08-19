"""Lazy ID-based enrichment from the local per-document chunk JSON files."""

import json
import logging
import threading
from pathlib import Path
from typing import Any, Dict, Optional, Union

from config.settings import KNOWLEDGE_BASE_DIR, get_chunker_name


logger = logging.getLogger("LocalChunkStore")

LOCAL_TEXT_FIELDS = ("subsection_text", "full_subsection_text", "bm25_text")


class LocalChunkStore:
    """Resolve Pinecone vector IDs to text kept only in local chunk caches."""

    def __init__(
        self,
        chunker: Optional[str] = None,
        root: Optional[Union[str, Path]] = None,
    ):
        self.chunker = (chunker or get_chunker_name()).strip().lower().replace("/", "_")
        self.root = Path(root) if root is not None else KNOWLEDGE_BASE_DIR
        self._texts_by_id: Optional[Dict[str, Dict[str, str]]] = None
        self._lock = threading.Lock()

    def _load(self) -> Dict[str, Dict[str, str]]:
        pattern = f"**/structured_output_chunks__{self.chunker}.json"
        paths = sorted(self.root.glob(pattern))
        if not paths:
            raise FileNotFoundError(
                f"No local chunk caches matching {pattern!r} under {self.root}"
            )

        texts_by_id: Dict[str, Dict[str, str]] = {}
        for path in paths:
            try:
                with path.open("r", encoding="utf-8") as handle:
                    chunks = json.load(handle)
            except (OSError, json.JSONDecodeError) as exc:
                raise RuntimeError(f"Cannot load local chunk cache {path}: {exc}") from exc

            for chunk in chunks:
                chunk_id = str(chunk.get("id", ""))
                if not chunk_id:
                    continue
                metadata = chunk.get("metadata", {}) or {}
                subsection_text = str(metadata.get("subsection_text", "") or "")
                texts_by_id[chunk_id] = {
                    "subsection_text": subsection_text,
                    # Unsplit chunks do not carry this field; their chunk text is
                    # already the complete subsection.
                    "full_subsection_text": str(
                        metadata.get("full_subsection_text") or subsection_text
                    ),
                    "bm25_text": str(metadata.get("bm25_text", "") or subsection_text),
                }

        logger.info(
            "Loaded %d local chunk text records from %d cache file(s) for [%s]",
            len(texts_by_id),
            len(paths),
            self.chunker,
        )
        return texts_by_id

    def _ensure_loaded(self) -> Dict[str, Dict[str, str]]:
        if self._texts_by_id is None:
            with self._lock:
                if self._texts_by_id is None:
                    self._texts_by_id = self._load()
        return self._texts_by_id

    def enrich(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Return a copy with locally stored text fields merged by vector ID."""
        enriched = dict(chunk)
        chunk_id = str(enriched.get("id", ""))
        local = self._ensure_loaded().get(chunk_id)
        if local is None:
            logger.warning("No local chunk text found for Pinecone vector id=%s", chunk_id)
            return enriched
        enriched.update(local)
        return enriched

