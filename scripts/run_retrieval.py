"""
Retrieval entry script.

Reads queries from data/good_queries.csv (or --queries), runs each through the
pipeline configured in config/pipeline.yaml, and saves:

  - data/responses.csv                 — query + final answer (flat, easy to read)
  - data/runs/run_<timestamp>.json     — the FULL run trace: config, and per
                                         query the reformulations, per-variant
                                         retrieved chunks, gap analysis + 2nd
                                         round (two-call mode), reranked chunks,
                                         final chunks, and the answer.
  - data/retrieved_chunks.json         — last query's final chunks (back-compat)

The run JSON is what the Streamlit viewer (app.py) reads.

Usage:
    python -m scripts.run_retrieval
    python -m scripts.run_retrieval --queries data/my_queries.csv
    python -m scripts.run_retrieval --label hierarchical_twocall
"""

import argparse
import csv
import json
import logging

from config.settings import (
    CHUNKS_DUMP_FILE,
    QUERIES_FILE,
    REFERENCE_FILE,
    RESPONSES_FILE,
    SETTINGS,
)
from pipeline.stage3_retrieval.orchestrator import RetrievalPipeline
from scripts.common import load_queries, load_references, run_queries
from utils.logging_setup import setup_logging

setup_logging()
logger = logging.getLogger("RetrievalScript")


def save_responses(recorder, path: str):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["query", "response"])
        for t in recorder.traces:
            writer.writerow([t.query, t.answer])


def main():
    parser = argparse.ArgumentParser(description="Run retrieval + response generation")
    parser.add_argument("--queries", default=str(QUERIES_FILE))
    parser.add_argument("--responses", default=str(RESPONSES_FILE))
    parser.add_argument("--chunks-dump", default=str(CHUNKS_DUMP_FILE))
    parser.add_argument("--label", default="retrieval", help="Label for the saved run JSON.")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    cfg = SETTINGS.pipeline
    retr = cfg["retrieval"]
    logger.info(
        f"Config: embedder={cfg['embedder']}, query={cfg['query_strategy']}, "
        f"retriever={cfg['retriever']}, reranker={cfg['reranker']}, "
        f"two_call={cfg.get('two_call', {}).get('enabled', False)}"
    )

    pipeline = RetrievalPipeline()
    queries = load_queries(args.queries, args.limit)
    logger.info(f"Loaded {len(queries)} queries from {args.queries}")

    references = load_references(str(REFERENCE_FILE))
    recorder = run_queries(
        pipeline, queries,
        retrieval_top_k=retr["top_k"],
        rerank_top_k=retr["rerank_top_k"],
        references=references,
        label=args.label,
    )

    run_path = recorder.save()
    save_responses(recorder, args.responses)
    last = recorder.traces[-1].final_chunks if recorder.traces else []
    with open(args.chunks_dump, "w", encoding="utf-8") as f:
        json.dump(last, f, indent=2, ensure_ascii=False)

    logger.info(f"Wrote {len(recorder.traces)} responses to {args.responses}")
    logger.info(f"Full run trace: {run_path}")
    logger.info(f"View it with:  streamlit run app.py")


if __name__ == "__main__":
    main()
