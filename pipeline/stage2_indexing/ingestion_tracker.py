"""Persistent ledger of documents successfully embedded into Pinecone.

The tracker deliberately records completion only after every vector for a
document has been upserted. A deterministic fingerprint makes cached chunk
changes invalidate the record automatically without storing every chunk in the
ledger.
"""

import hashlib
import json
import os
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.settings import CACHE_DIR, PROJECT_ROOT


INGESTION_TRACKER_FILE = CACHE_DIR / "pinecone_ingestion_tracker.json"
_DEFAULT_NAMESPACE = "__default__"
_SCHEMA_VERSION = 1


def chunk_fingerprint(chunks: List[Dict[str, Any]]) -> str:
    """Return an order-sensitive digest of chunk IDs, text, and metadata."""
    digest = hashlib.sha256()
    for chunk in chunks:
        encoded = json.dumps(
            chunk,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest.update(len(encoded).to_bytes(8, byteorder="big"))
        digest.update(encoded)
    return digest.hexdigest()


def document_key(json_path: str) -> str:
    """Create a stable, human-readable key for a structured document."""
    resolved = Path(json_path).resolve()
    try:
        return resolved.relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


class IngestionTracker:
    """Read and atomically update the per-index ingestion ledger."""

    _lock = threading.Lock()

    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path) if path is not None else INGESTION_TRACKER_FILE

    @staticmethod
    def _empty() -> Dict[str, Any]:
        return {"version": _SCHEMA_VERSION, "indexes": {}}

    def _load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return self._empty()
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(
                f"Cannot read ingestion tracker {self.path}: {exc}"
            ) from exc
        if not isinstance(data, dict) or data.get("version") != _SCHEMA_VERSION:
            raise RuntimeError(
                f"Unsupported ingestion tracker format in {self.path}; "
                "move or delete the tracker file before retrying"
            )
        data.setdefault("indexes", {})
        return data

    def _save(self, data: Dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_name = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temp_name = handle.name
                json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.path)
        finally:
            if temp_name and os.path.exists(temp_name):
                os.unlink(temp_name)

    @staticmethod
    def _namespace_key(namespace: str) -> str:
        return namespace or _DEFAULT_NAMESPACE

    def get_record(
        self,
        *,
        index_name: str,
        namespace: str,
        document: str,
    ) -> Optional[Dict[str, Any]]:
        with self._lock:
            data = self._load()
        return (
            data.get("indexes", {})
            .get(index_name, {})
            .get("namespaces", {})
            .get(self._namespace_key(namespace), {})
            .get("documents", {})
            .get(document)
        )

    def is_indexed(
        self,
        *,
        index_name: str,
        namespace: str,
        document: str,
        fingerprint: str,
        chunk_count: int,
        embedder: str,
        model: str,
        dimension: int,
    ) -> bool:
        record = self.get_record(
            index_name=index_name,
            namespace=namespace,
            document=document,
        )
        expected = {
            "chunk_fingerprint": fingerprint,
            "chunk_count": chunk_count,
            "embedder": embedder,
            "model": model,
            "dimension": dimension,
        }
        return bool(record) and all(
            record.get(key) == value for key, value in expected.items()
        )

    def mark_indexed(
        self,
        *,
        index_name: str,
        namespace: str,
        document: str,
        fingerprint: str,
        chunk_count: int,
        embedder: str,
        model: str,
        dimension: int,
    ) -> None:
        record = {
            "chunk_count": chunk_count,
            "chunk_fingerprint": fingerprint,
            "dimension": dimension,
            "embedder": embedder,
            "indexed_at": datetime.now(timezone.utc).isoformat(),
            "model": model,
        }
        with self._lock:
            data = self._load()
            namespace_data = (
                data["indexes"]
                .setdefault(index_name, {"namespaces": {}})["namespaces"]
                .setdefault(self._namespace_key(namespace), {"documents": {}})
            )
            namespace_data["documents"][document] = record
            self._save(data)

    def clear_index(self, index_name: str) -> int:
        """Forget all documents for an index and return the removed count."""
        with self._lock:
            data = self._load()
            index_data = data.get("indexes", {}).pop(index_name, None)
            if index_data is None:
                return 0
            removed = sum(
                len(namespace.get("documents", {}))
                for namespace in index_data.get("namespaces", {}).values()
            )
            self._save(data)
            return removed
