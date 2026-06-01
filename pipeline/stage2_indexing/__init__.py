"""
Stage 2: indexing (chunk -> embed -> upsert + BM25).

Minimal __init__ to avoid pulling in heavyweight client deps.
Use explicit imports:
    from pipeline.stage2_indexing.orchestrator import run_ingestion
    from pipeline.stage2_indexing.chunker import Chunker
    from pipeline.stage2_indexing.bm25_index import BM25Index
"""
