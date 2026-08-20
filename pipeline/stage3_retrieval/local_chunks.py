"""Lazy ID-based enrichment from the local per-document chunk JSON files."""

import json
import logging
import os
import threading
from pathlib import Path
from typing import Any, Dict, Optional, Union

from config.settings import KNOWLEDGE_BASE_DIR, get_chunker_name


logger = logging.getLogger("LocalChunkStore")

LOCAL_TEXT_FIELDS = ("subsection_text", "full_subsection_text", "bm25_text")


class LocalChunkStore:
    """Resolve Pinecone vector IDs to local JSON or a PostgreSQL chunk table."""

    def __init__(
        self,
        chunker: Optional[str] = None,
        root: Optional[Union[str, Path]] = None,
    ):
        self.chunker = (chunker or get_chunker_name()).strip().lower().replace("/", "_")
        self.root = Path(root) if root is not None else KNOWLEDGE_BASE_DIR
        self.backend = os.getenv("TELCORAG_CHUNK_STORE", "local").strip().lower()
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
        """Return one enriched chunk (batch callers should use enrich_many)."""
        return self.enrich_many([chunk])[0]

    def _load_database(self, chunk_ids: list[str]) -> Dict[str, Dict[str, str]]:
        if not chunk_ids:
            return {}
        database_url = os.getenv("DATABASE_URL", "").strip()
        if not database_url:
            raise RuntimeError("DATABASE_URL is required for TELCORAG_CHUNK_STORE=database")
        if database_url.startswith("postgresql+psycopg://"):
            database_url = "postgresql://" + database_url.removeprefix(
                "postgresql+psycopg://"
            )
        elif database_url.startswith("postgres://"):
            database_url = "postgresql://" + database_url.removeprefix("postgres://")

        import psycopg

        sql = """
            SELECT chunk_id, subsection_text, full_subsection_text, bm25_text
            FROM rag_chunks
            WHERE chunker = %s AND chunk_id = ANY(%s)
        """
        with psycopg.connect(database_url, prepare_threshold=None) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, (self.chunker, chunk_ids))
                rows = cursor.fetchall()
        return {
            row[0]: {
                "subsection_text": row[1] or "",
                "full_subsection_text": row[2] or row[1] or "",
                "bm25_text": row[3] or row[1] or "",
            }
            for row in rows
        }

    def enrich_many(self, chunks: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        """Merge text for many matches with one local load or database query."""
        chunk_ids = [str(chunk.get("id", "")) for chunk in chunks if chunk.get("id")]
        if self.backend == "database":
            texts_by_id = self._load_database(chunk_ids)
        elif self.backend == "local":
            texts_by_id = self._ensure_loaded()
        else:
            raise ValueError(
                "TELCORAG_CHUNK_STORE must be either 'local' or 'database', "
                f"not {self.backend!r}"
            )

        output = []
        for chunk in chunks:
            enriched = dict(chunk)
            chunk_id = str(enriched.get("id", ""))
            local = texts_by_id.get(chunk_id)
            if local is None:
                logger.warning("No chunk text found for Pinecone vector id=%s", chunk_id)
            else:
                enriched.update(local)
            output.append(enriched)
        return output
