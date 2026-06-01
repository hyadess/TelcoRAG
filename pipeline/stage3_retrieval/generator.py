"""Generates the final answer from a list of retrieved/reranked chunks."""

import logging
from typing import Any, Dict, List

from clients.gemini import general_response
from config.settings import SETTINGS
from core.prompt_loader import get_loader

logger = logging.getLogger("ResponseGenerator")


def build_context_window(chunks: List[Dict[str, Any]]) -> str:
    """Formats chunks into a single context string for the LLM."""
    parts = []
    for i, chunk in enumerate(chunks):
        doc_name = chunk.get("doc_name", "Unknown")
        chapter = chunk.get("chapter", "")
        section = chunk.get("section", "")
        subsection_id = chunk.get("subsection_id", "")
        page_numbers = chunk.get("page_numbers", "")
        text = chunk.get("subsection_text", "")

        header = f"[Chunk {i + 1}] Document: {doc_name}"
        if chapter:
            header += f" | Chapter: {chapter}"
        if section:
            header += f" | Section: {section}"
        if subsection_id and subsection_id != "N/A":
            header += f" | Subsection: {subsection_id}"
        if page_numbers:
            header += f" | Pages: {page_numbers}"

        parts.append(f"{header}\n{text}")

    return "\n\n---\n\n".join(parts)


def generate_response(query: str, chunks: List[Dict[str, Any]]) -> str:
    """Render the answer prompt and call the LLM."""
    if not chunks:
        return "I don't have enough information in the knowledge base to answer this question."

    context_window = build_context_window(chunks)
    prompts = get_loader()
    domain = SETTINGS.domain

    prompt = prompts.render(
        "generation/answer.j2",
        query=query,
        context_window=context_window,
        domain=domain.get("domain", "the relevant legal area"),
    )
    return general_response(prompt)
