"""Metadata policy for vectors stored in the remote dense index."""

import json
from typing import Any, Dict


PINECONE_METADATA_LIMIT_BYTES = 40 * 1024
LOCAL_ONLY_METADATA_FIELDS = frozenset(
    {"subsection_text", "full_subsection_text", "bm25_text"}
)


def pinecone_metadata(chunk: Dict[str, Any]) -> Dict[str, Any]:
    """Return compact metadata; large text remains in the local chunk JSON."""
    metadata = {
        key: value
        for key, value in (chunk.get("metadata", {}) or {}).items()
        if key not in LOCAL_ONLY_METADATA_FIELDS
    }
    size = len(
        json.dumps(metadata, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    )
    if size > PINECONE_METADATA_LIMIT_BYTES:
        raise ValueError(
            f"Compact Pinecone metadata for chunk {chunk.get('id', '')!r} is "
            f"{size} bytes; limit is {PINECONE_METADATA_LIMIT_BYTES} bytes"
        )
    return metadata
