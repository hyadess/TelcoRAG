"""
Ingestion entry script.

For every PDF in ./resources, runs:
  Stage 1: PDF -> markdown -> structured JSON
  Stage 2: chunks (+ reading-order neighbours) -> embeddings (Pinecone) + BM25 index

Re-running on the same PDF skips stage 1 if a structured_output.json already
exists, and stage 2 reuses cached chunks. Embeddings are re-upserted (Pinecone
deduplicates by id); BM25 dedupes by id.

Usage:
    python -m scripts.run_ingestion
    python -m scripts.run_ingestion --pdf-dir ./my_pdfs --embedder voyage
"""

import argparse
import logging
import os

from config.settings import KNOWLEDGE_BASE_DIR, SETTINGS, get_chunker_name
from pipeline.stage1_extraction.orchestrator import DocumentProcessor
from pipeline.stage2_indexing.orchestrator import run_ingestion
from utils.logging_setup import setup_logging

setup_logging()
logger = logging.getLogger("IngestionScript")


def kb_creation_pipeline(pdf_path: str, embedder_name: str, chunker_name: str):
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    structured_output = os.path.join(str(KNOWLEDGE_BASE_DIR), pdf_name, "structured_output.json")

    # ---- Stage 1 (parse + extract once per document) ----
    if os.path.exists(structured_output):
        logger.info(f"Stage 1 skipped: {structured_output} already exists")
    else:
        logger.info(f"Running stage 1 on {pdf_path}")
        processor = DocumentProcessor(root_doc_path=str(KNOWLEDGE_BASE_DIR))
        processor.process_document(pdf_path)

    # ---- Stage 2 ----
    if not os.path.exists(structured_output):
        logger.error(f"No structured output for {pdf_path}; stage 2 skipped.")
        return

    logger.info(f"--- Stage 2 [{chunker_name}] ---")
    run_ingestion(
        json_path=structured_output,
        embedder_name=embedder_name,
        chunker_name=chunker_name,
    )


def main():
    parser = argparse.ArgumentParser(description="Run the full ingestion pipeline")
    parser.add_argument("--pdf-dir", default="./resources",
                        help="Folder containing PDFs to ingest (default: ./resources)")
    parser.add_argument("--embedder", default=None,
                        help="Embedder name (overrides pipeline.yaml).")
    parser.add_argument("--chunker", default=None,
                        help="Chunker name (defaults to pipeline.yaml -> chunker, i.e. baseline).")
    args = parser.parse_args()

    embedder_name = args.embedder or SETTINGS.pipeline["embedder"]
    chunker_name = (args.chunker or get_chunker_name()).strip().lower()
    pdf_dir = args.pdf_dir

    if not os.path.isdir(pdf_dir):
        logger.error(f"PDF directory not found: {pdf_dir}")
        return

    pdfs = [f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")]
    if not pdfs:
        logger.warning(f"No PDFs found in {pdf_dir}")
        return

    logger.info(f"Found {len(pdfs)} PDFs. embedder='{embedder_name}', chunker='{chunker_name}'.")
    for pdf in pdfs:
        path = os.path.join(pdf_dir, pdf)
        logger.info(f"\n{'=' * 70}\nProcessing: {pdf}\n{'=' * 70}")
        kb_creation_pipeline(path, embedder_name, chunker_name)


if __name__ == "__main__":
    main()
