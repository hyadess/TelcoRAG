"""
Chunk sequencing — assigns each chunk its reading-order position and the ids of
its nearest neighbours, so the retriever's *neighbour expansion* (stage 3) can
fetch the previous/next chunks of a partially-relevant hit.

Chunks arrive in document order (subsection order, and chunk_index order within
a split subsection). We record, per chunk:

  - ``seq``       : global 0-based position within its document.
  - ``prev_ids``  : ids of the up-to-``window`` preceding chunks, nearest first.
  - ``next_ids``  : ids of the up-to-``window`` following chunks, nearest first.

Neighbours never cross a document boundary. The function is pure and operates
in place on the chunk metadata, so it is trivially unit-testable offline.
"""

from typing import Any, Dict, List


def assign_neighbors(chunks: List[Dict[str, Any]], window: int = 2) -> List[Dict[str, Any]]:
    """Populate seq / prev_ids / next_ids on each chunk's metadata.

    Chunks are grouped by ``metadata['doc_name']`` and ordered as given (the
    ingestion pipeline produces them in reading order). Returns the same list
    (mutated in place) for convenience.
    """
    # Stable grouping by document, preserving input order within each doc.
    by_doc: Dict[str, List[Dict[str, Any]]] = {}
    for c in chunks:
        doc = c.get("metadata", {}).get("doc_name", "")
        by_doc.setdefault(doc, []).append(c)

    for doc_chunks in by_doc.values():
        n = len(doc_chunks)
        for i, c in enumerate(doc_chunks):
            md = c.setdefault("metadata", {})
            md["seq"] = i
            # nearest first: prev1, prev2, ...
            prev_ids = [doc_chunks[i - d]["id"] for d in range(1, window + 1) if i - d >= 0]
            next_ids = [doc_chunks[i + d]["id"] for d in range(1, window + 1) if i + d < n]
            md["prev_ids"] = prev_ids
            md["next_ids"] = next_ids
    return chunks
