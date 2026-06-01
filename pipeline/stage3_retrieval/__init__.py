"""
Stage 3: retrieval pipeline.

This package's __init__ is intentionally minimal so that importing one
sub-module (e.g. `pipeline.stage3_retrieval.query_strategies`) does NOT pull
in the full pipeline dependency chain (clients, retrievers, etc.).

Use explicit imports:
    from pipeline.stage3_retrieval.orchestrator import RetrievalPipeline
    from pipeline.stage3_retrieval.generator import generate_response
"""
