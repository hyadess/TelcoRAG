"""Lazy, process-wide adapter around the repository's RAG pipeline."""

import threading
from typing import TYPE_CHECKING, Any

from tool.settings import (
    CHUNKER_NAME,
    EMBEDDER_NAME,
    QUERY_STRATEGY,
    RERANKER_NAME,
    RETRIEVER_NAME,
    SETTINGS,
)

if TYPE_CHECKING:
    from pipeline.stage3_retrieval.orchestrator import RetrievalPipeline


_pipeline: "RetrievalPipeline | None" = None
_pipeline_lock = threading.Lock()
_query_lock = threading.Lock()


def get_pipeline() -> "RetrievalPipeline":
    global _pipeline
    if _pipeline is None:
        with _pipeline_lock:
            if _pipeline is None:
                from pipeline.stage3_retrieval.orchestrator import RetrievalPipeline

                _pipeline = RetrievalPipeline(
                    embedder_name=EMBEDDER_NAME,
                    query_strategy=QUERY_STRATEGY,
                    retriever_name=RETRIEVER_NAME,
                    reranker_name=RERANKER_NAME,
                    chunker_name=CHUNKER_NAME,
                )
    return _pipeline


def _score(chunk: dict[str, Any]) -> float | None:
    for key in ("relevance_score", "score", "base_score"):
        value = chunk.get(key)
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                return None
    return None


def serialize_subsections(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "rank": rank,
            "document": chunk.get("doc_name") or chunk.get("document_name") or "Unknown",
            "chapter": chunk.get("chapter", "") or "",
            "section": chunk.get("section", "") or "",
            "subsection_id": chunk.get("subsection_id", "") or "",
            "page_numbers": chunk.get("page_numbers"),
            "text": chunk.get("subsection_text", "") or "",
            "score": _score(chunk),
        }
        for rank, chunk in enumerate(chunks, start=1)
    ]


def answer_question(question: str) -> tuple[str, list[dict[str, Any]]]:
    from pipeline.stage3_retrieval.generator import generate_response

    # Several provider SDK clients are not guaranteed to be thread-safe. The
    # lock keeps a multi-threaded ASGI worker from interleaving pipeline calls.
    with _query_lock:
        trace = get_pipeline().process_query(
            question,
            retrieval_top_k=SETTINGS.retrieval_top_k,
            rerank_top_k=SETTINGS.rerank_top_k,
        )
        chunks = trace.final_chunks
        answer = generate_response(question, chunks)
    if not answer:
        answer = "The answer service returned no text. Please try again."
    return answer, serialize_subsections(chunks)
