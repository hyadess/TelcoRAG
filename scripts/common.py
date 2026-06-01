"""
Shared helpers for the entry scripts.

Keeping query loading and the per-query run loop here (rather than duplicated in
run_retrieval.py and run_experiments.py) means the retrieval flow — process each
query into a full QueryTrace, generate the answer, record it — is defined once.
Scripts compose these pieces.
"""

import csv
import logging
from typing import Dict, List, Optional

from pipeline.stage3_retrieval.generator import generate_response
from pipeline.stage3_retrieval.orchestrator import RetrievalPipeline
from pipeline.tracing import RunRecorder

logger = logging.getLogger("scripts.common")


def load_queries(path: str, limit: Optional[int] = None) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        queries = [row[0] for row in reader if row]
    return queries[:limit] if limit else queries


def load_references(path: str) -> Dict[str, str]:
    """Map query -> reference answer from a 2-column CSV (query, reference)."""
    refs: Dict[str, str] = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) >= 2 and row[0].strip():
                    refs[row[0].strip()] = row[1]
    except FileNotFoundError:
        pass
    return refs


def run_queries(
    pipeline: RetrievalPipeline,
    queries: List[str],
    retrieval_top_k: int,
    rerank_top_k: int,
    references: Optional[Dict[str, str]] = None,
    generate: bool = True,
    label: Optional[str] = None,
) -> RunRecorder:
    """Run every query through the pipeline, generate answers, record traces.

    Returns the (unsaved) RunRecorder — the caller decides where/whether to save.
    """
    references = references or {}
    recorder = RunRecorder(config=pipeline.config_snapshot(), label=label)

    for i, query in enumerate(queries):
        logger.info(f"[{i + 1}/{len(queries)}] {query[:90]}")
        trace = pipeline.process_query(
            query, retrieval_top_k=retrieval_top_k, rerank_top_k=rerank_top_k
        )
        if generate:
            trace.answer = generate_response(query, trace.final_chunks)
            logger.info(f"  answer: {trace.answer[:140]}...")
        trace.reference = references.get(query.strip())
        recorder.add(trace)

    return recorder
