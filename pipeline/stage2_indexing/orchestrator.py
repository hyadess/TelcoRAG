"""
Stage 2 orchestrator — turns structured-output JSON into:
  1. Chunks (cached in <doc>_chunks__<chunker>.json), each carrying its
     reading-order neighbours (for stage-3 neighbour expansion).
  2. Vectors stored in Pinecone via the chosen embedder.
  3. A BM25 index saved to .cache/bm25_index__<chunker>.pkl.

There is a single chunker (``baseline``), so the per-chunker namespace / index
file simply isolate this system's data under one stable name. The helpers are
kept so a second indexing convention could be added without code changes here.

Run this for each document; the BM25 index accumulates across runs.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

from config.settings import (
    SETTINGS,
    bm25_index_path,
    chunk_namespace,
    get_chunker_name,
)
from core.registry import CHUNKERS, EMBEDDERS, discover_plugins

from .bm25_index import BM25Index
from .ingestion_tracker import IngestionTracker, chunk_fingerprint, document_key
from .sequencing import assign_neighbors

logger = logging.getLogger("IngestionPipeline")


def _load_structured_data(path: str) -> List[Dict]:
    if not os.path.exists(path):
        logger.error(f"File not found: {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _chunks_path_for(json_path: str, chunker_name: str) -> str:
    base = os.path.splitext(json_path)[0]
    return f"{base}_chunks__{chunker_name}.json"


def chunk_document(
    json_path: str,
    chunker,
    chunker_name: str,
    neighbor_window: int = 2,
) -> List[Dict]:
    """
    Chunk a single document with the given chunker, then assign reading-order
    neighbours. Caches the result next to the input JSON, keyed by chunker name.
    Returns the chunk list (loaded from cache if it already exists).
    """
    cache_path = _chunks_path_for(json_path, chunker_name)

    if os.path.exists(cache_path):
        logger.info(f"Loading existing chunks from {cache_path}")
        with open(cache_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)
        # Older caches may predate neighbour metadata — backfill defensively.
        if chunks and "seq" not in chunks[0].get("metadata", {}):
            assign_neighbors(chunks, window=neighbor_window)
        return chunks

    data = _load_structured_data(json_path)
    if not data:
        logger.warning(f"No data in {json_path}")
        return []

    logger.info(f"Chunking {len(data)} subsections with [{chunker_name}]...")
    chunks: List[Dict] = []
    for i, item in enumerate(data):
        try:
            chunks.extend(chunker.process_subsection(item))
        except Exception as e:
            logger.error(f"Error on subsection {item.get('subsection_id', '?')}: {e}")
        if (i + 1) % 25 == 0:
            logger.info(f"  Chunked {i + 1}/{len(data)}")

    # Assign reading-order neighbours for stage-3 neighbour expansion.
    assign_neighbors(chunks, window=neighbor_window)

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(chunks)} chunks to {cache_path}")
    return chunks


def run_ingestion(
    json_path: str,
    embedder_name: Optional[str] = None,
    chunker_name: Optional[str] = None,
    update_bm25: bool = True,
) -> List[Dict]:
    """
    End-to-end stage-2 for a single document.

    Args:
        json_path: path to the structured-output JSON file from stage 1.
        embedder_name: which embedder to use. Defaults to pipeline.yaml setting.
        chunker_name: chunker name. Defaults to pipeline.yaml setting (baseline).
        update_bm25: if True, append this doc's chunks to the BM25 index.

    Returns: the chunk list.
    """
    discover_plugins(include_judges=False)
    pipeline_cfg = SETTINGS.pipeline
    chunk_cfg = pipeline_cfg.get("chunking", {})
    embedder_name = embedder_name or pipeline_cfg["embedder"]
    chunker_name = (chunker_name or get_chunker_name()).strip().lower()
    namespace = chunk_namespace(chunker_name)
    neighbor_window = int(chunk_cfg.get("neighbor_window", 2))

    logger.info(
        f"Stage 2 ingestion: {json_path} | embedder=[{embedder_name}] "
        f"chunker=[{chunker_name}] namespace=[{namespace or 'default'}]"
    )

    embedder = EMBEDDERS.build(embedder_name)
    embedder.set_namespace(namespace)
    index_created = embedder.initialize_db()
    index_name = embedder.vector_db.index_name
    tracker = IngestionTracker()
    if index_created:
        removed = tracker.clear_index(index_name)
        if removed:
            logger.info(
                "Pinecone index [%s] was newly created; cleared %d stale "
                "tracker record(s)",
                index_name,
                removed,
            )

    chunker = CHUNKERS.build(
        chunker_name,
        max_chunk_size=chunk_cfg.get("max_size", 2048),
        overlap=chunk_cfg.get("overlap", 204),
    )
    chunks = chunk_document(json_path, chunker, chunker_name, neighbor_window=neighbor_window)
    if not chunks:
        return []

    doc_key = document_key(json_path)
    fingerprint = chunk_fingerprint(chunks)
    already_indexed = tracker.is_indexed(
        index_name=index_name,
        namespace=namespace,
        document=doc_key,
        fingerprint=fingerprint,
        chunk_count=len(chunks),
        embedder=embedder_name,
        model=embedder.model,
        dimension=embedder.dimension,
    )

    if already_indexed:
        logger.info(
            "Embedding skipped: tracker confirms all %d chunks are already in "
            "index=[%s], namespace=[%s]",
            len(chunks),
            index_name,
            namespace or "default",
        )
    else:
        # Keep sparse retrieval conservative while dense ingestion is retried:
        # if Pinecone is not confirmed complete, this document must not remain
        # searchable in BM25. It is added back only after the dense upload.
        if update_bm25:
            removed = _remove_bm25_chunk_ids(
                {chunk.get("id", "") for chunk in chunks if chunk.get("id")},
                bm25_index_path(chunker_name),
            )
            if removed:
                logger.info(
                    "BM25: removed %d chunks for incomplete document before retry",
                    removed,
                )

        # A previous run can fail after Pinecone accepted only some upsert
        # batches but before the tracker was marked complete. Cached chunks keep
        # stable IDs, so remove every current ID first to make the retry clean
        # and document-atomic. Pinecone ignores IDs that do not exist. A newly
        # created index is already empty and needs no cleanup.
        if not index_created:
            logger.info(
                "Tracker has no matching completed ingestion; cleaning up %d "
                "possible partial vectors before retrying",
                len(chunks),
            )
            embedder.delete_documents(chunks)
        logger.info(f"Embedding and storing {len(chunks)} chunks...")
        embedder.store_documents(chunks)
        # Never mark a document before store_documents completes: a failed
        # embedding or partial Pinecone upsert must be retried on the next run.
        tracker.mark_indexed(
            index_name=index_name,
            namespace=namespace,
            document=doc_key,
            fingerprint=fingerprint,
            chunk_count=len(chunks),
            embedder=embedder_name,
            model=embedder.model,
            dimension=embedder.dimension,
        )
        logger.info("Recorded successful Pinecone ingestion in %s", tracker.path)

    if update_bm25:
        _update_bm25_index(chunks, bm25_index_path(chunker_name))

    logger.info(f"Stage 2 complete for {json_path} [{chunker_name}]")
    return chunks


def _update_bm25_index(new_chunks: List[Dict], index_file: Path) -> None:
    """Merge new chunks into the BM25 index file."""
    bm25 = BM25Index()
    existing_loaded = bm25.load(index_file)

    if existing_loaded:
        existing_chunks = [{"id": m.get("id", ""), "metadata": m} for m in bm25._metadatas]
        existing_ids = {c["id"] for c in existing_chunks}
        new_only = [c for c in new_chunks if c.get("id") not in existing_ids]
        merged = existing_chunks + new_only
        logger.info(f"BM25: {len(existing_chunks)} existing + {len(new_only)} new = {len(merged)} total")
    else:
        merged = new_chunks
        logger.info(f"BM25: building fresh index over {len(merged)} chunks")

    fresh = BM25Index()
    fresh.build(merged)
    fresh.save(index_file)


def _remove_bm25_chunk_ids(chunk_ids: set[str], index_file: Path) -> int:
    """Remove a document's current chunk IDs from BM25 and return the count."""
    if not chunk_ids:
        return 0

    bm25 = BM25Index()
    if not bm25.load(index_file):
        return 0

    existing_chunks = [
        {"id": metadata.get("id", ""), "metadata": metadata}
        for metadata in bm25._metadatas
    ]
    remaining = [chunk for chunk in existing_chunks if chunk.get("id") not in chunk_ids]
    removed = len(existing_chunks) - len(remaining)
    if not removed:
        return 0

    fresh = BM25Index()
    fresh.build(remaining)
    fresh.save(index_file)
    return removed
