"""
Base chunker — shared subsection-to-chunks logic.

A chunker turns one structured subsection into one or more chunk dicts of the
shape ``{"id", "text", "metadata"}`` where:

  - ``text``  is the string the dense embedder encodes (the "embed text").
  - ``metadata["bm25_text"]`` is the string the BM25 index tokenizes.
  - ``metadata`` carries everything the retriever / generator / judge may need.

There is a single indexing convention (the baseline), with no enrichment:

  - Dense embed text = document summary + chapter/section headers + subsection text.
  - BM25 corpus text = subsection text only.

Splitting (for oversized subsections), per-subsection context summaries, and
metadata assembly all live here. A concrete chunker subclasses this and is
registered in the plugin registry; see ``baseline.py``.
"""

import logging
import uuid
from typing import Any, Dict, List

from clients.gemini import general_response
from core.prompt_loader import get_loader

logger = logging.getLogger("Chunker")


class BaseChunker:
    """Shared chunking machinery used by the registered chunker(s)."""

    def __init__(self, max_chunk_size: int = 2048, overlap: int = 204):
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
        self.prompts = get_loader()
        self._splitter = None  # lazy — only built when a large subsection appears

    # ------------------------------------------------------------------
    # Shared internals
    # ------------------------------------------------------------------
    @property
    def splitter(self):
        if self._splitter is None:
            from langchain_text_splitters import RecursiveCharacterTextSplitter

            self._splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.max_chunk_size,
                chunk_overlap=self.overlap,
                separators=["\n\n", "\n", ". ", " ", ""],
            )
        return self._splitter

    def _generate_context_summary(self, subsection_text: str, document_summary: str) -> str:
        """Use the LLM to summarize what this subsection is about (1-2 sentences)."""
        prompt = self.prompts.render(
            "extraction/subsection_summary.j2",
            document_summary=document_summary,
            subsection_text=subsection_text,
        )
        return general_response(prompt)

    def _build_metadata(
        self,
        subsection_data: Dict[str, Any],
        page_numbers_str: str,
        bm25_text: str,
    ) -> Dict[str, Any]:
        """Assemble the metadata dict that travels with every chunk."""
        return {
            "doc_name": subsection_data.get("document_name", "Unknown Document"),
            "document_summary": subsection_data.get("document_summary", ""),
            "chapter": subsection_data.get("chapter", ""),
            "section": subsection_data.get("section", ""),
            "subsection_id": subsection_data.get("subsection_id", ""),
            "page_numbers": page_numbers_str,
            # The exact string the BM25 index should tokenize for this chunk
            # (baseline = subsection text only).
            "bm25_text": bm25_text,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def process_subsection(self, subsection_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert a single structured subsection into one or more chunks."""
        subsection_text = subsection_data.get("subsection_text", "")
        document_summary = subsection_data.get("document_summary", "")
        chapter = subsection_data.get("chapter", "")
        section = subsection_data.get("section", "")
        page_numbers_str = ", ".join(map(str, subsection_data.get("page_numbers", [])))

        if not subsection_text.strip():
            return []

        # BM25 corpus text = subsection text only.
        bm25_text = subsection_text

        # ---- Small subsection: one chunk ----
        if len(subsection_text) <= self.max_chunk_size:
            embed_text = (
                f"Document: {document_summary}\n"
                f"Chapter: {chapter}\nSection: {section}\n"
                f"{subsection_text}"
            )
            metadata = self._build_metadata(subsection_data, page_numbers_str, bm25_text)
            metadata["subsection_text"] = subsection_text
            metadata["is_split"] = False
            return [{"id": str(uuid.uuid4()), "text": embed_text, "metadata": metadata}]

        # ---- Large subsection: generate context once, split into chunks ----
        logger.info(
            f"Subsection {subsection_data.get('subsection_id')} is large "
            f"({len(subsection_text)} chars). Splitting..."
        )
        local_context = self._generate_context_summary(subsection_text, document_summary)
        raw_chunks = self.splitter.split_text(subsection_text)

        result = []
        for idx, chunk_text in enumerate(raw_chunks):
            embed_text = (
                f"Context: {local_context}\n"
                f"Chapter: {chapter}\nSection: {section}\n"
                f"Content: {chunk_text}"
            )
            # For split subsections the BM25 corpus text is the chunk's own text
            # (so sparse matches localize to the right piece).
            metadata = self._build_metadata(subsection_data, page_numbers_str, chunk_text)
            metadata["subsection_text"] = chunk_text  # the retrievable unit is this chunk
            metadata["full_subsection_text"] = subsection_text  # keep the whole for reference
            metadata["chunk_index"] = idx
            metadata["total_chunks"] = len(raw_chunks)
            metadata["context_summary"] = local_context
            metadata["is_split"] = True
            result.append({"id": str(uuid.uuid4()), "text": embed_text, "metadata": metadata})

        return result
