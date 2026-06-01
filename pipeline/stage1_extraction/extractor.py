"""
Markdown pages -> structured subsection JSON.

Walks page-by-page through `<doc_folder>/markdowns/page_*.md`, asks the LLM
to classify each block (chapter header, section header, subsection, continuation),
buffers items, flushes on boundary changes, and finally cleans up consecutive
duplicates / empty headers.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional

from clients.gemini import structured_response
from core.prompt_loader import get_loader
from core.schemas import (
    DocumentMetadata,
    FinalSubsection,
    PageAnalysisResponse,
    PageItemType,
)

logger = logging.getLogger("Extractor")


class Extractor:
    def __init__(self, base_path: str, document_type: str = "telecommunications legal documents"):
        self.base_path = Path(base_path)
        self.document_type = document_type
        self.prompts = get_loader()

        # Per-document state — reset by `process_document`
        self.current_doc_meta: Optional[DocumentMetadata] = None
        self.current_chapter: str = "Preamble"
        self.current_section: str = "General"
        self.active_subsection: Optional[dict] = None
        self.final_results: List[FinalSubsection] = []

    # ---------- helpers ----------

    def _reset(self):
        self.current_doc_meta = None
        self.current_chapter = "Preamble"
        self.current_section = "General"
        self.active_subsection = None
        self.final_results = []

    def _extract_metadata(self, combined_text: str):
        prompt = self.prompts.render(
            "extraction/document_metadata.j2",
            text_content=combined_text[:5000],
            document_type=self.document_type,
        )
        result = structured_response(prompt, DocumentMetadata)
        if result:
            self.current_doc_meta = result
            logger.info(f"Document metadata extracted: {result.document_name}")
        else:
            self.current_doc_meta = DocumentMetadata(
                document_name="Unknown Document",
                document_summary="Extraction failed.",
            )

    def _flush_active_subsection(self):
        if self.active_subsection and self.active_subsection["text"].strip():
            entry = FinalSubsection(
                document_name=self.current_doc_meta.document_name,
                document_summary=self.current_doc_meta.document_summary,
                chapter=self.active_subsection["chapter"],
                section=self.active_subsection["section"],
                subsection_id=self.active_subsection["subsection_id"],
                subsection_text=self.active_subsection["text"].strip(),
                page_numbers=sorted(set(self.active_subsection["page_numbers"])),
            )
            self.final_results.append(entry)
        self.active_subsection = None

    def _clean_final_results(self):
        """Two passes over self.final_results to merge accidental duplicates."""
        # Pass 1: merge consecutive entries with the same subsection_id
        merged = []
        i = 0
        while i < len(self.final_results):
            curr = self.final_results[i]
            if (
                merged
                and merged[-1].subsection_id == curr.subsection_id
                and curr.subsection_id not in ("N/A", "")
            ):
                prev = merged[-1]
                prev_text = prev.subsection_text + " " + curr.subsection_text
                prev_pages = sorted(set(prev.page_numbers + curr.page_numbers))
                merged[-1] = FinalSubsection(
                    document_name=prev.document_name,
                    document_summary=prev.document_summary,
                    chapter=prev.chapter,
                    section=prev.section,
                    subsection_id=prev.subsection_id,
                    subsection_text=prev_text.strip(),
                    page_numbers=prev_pages,
                )
            else:
                merged.append(curr)
            i += 1
        self.final_results = merged

        # Pass 2: merge consecutive header-only (empty text) entries
        cleaned = []
        i = 0
        while i < len(self.final_results):
            curr = self.final_results[i]
            if (
                cleaned
                and not cleaned[-1].subsection_text.strip()
                and not curr.subsection_text.strip()
            ):
                prev = cleaned[-1]
                same_chapter = prev.chapter.strip() == curr.chapter.strip()
                cleaned[-1] = FinalSubsection(
                    document_name=prev.document_name,
                    document_summary=prev.document_summary,
                    chapter=prev.chapter if same_chapter else f"{prev.chapter} {curr.chapter}".strip(),
                    section=f"{prev.section} {curr.section}".strip(),
                    subsection_id=curr.subsection_id,
                    subsection_text="",
                    page_numbers=sorted(set(prev.page_numbers + curr.page_numbers)),
                )
            else:
                cleaned.append(curr)
            i += 1
        self.final_results = cleaned

    # ---------- main entry ----------

    def process_document(self, doc_folder_name: str) -> Optional[Path]:
        """
        Process a single document folder. Returns the path to the saved structured JSON.
        Path: base_path / doc_folder_name / markdowns / page_*.md
        """
        self._reset()

        md_folder = self.base_path / doc_folder_name / "markdowns"
        if not md_folder.exists():
            logger.warning(f"Markdown folder not found: {md_folder}")
            return None

        page_files = sorted(
            md_folder.glob("*.md"),
            key=lambda p: int(p.stem.split("_")[-1]) if p.stem.split("_")[-1].isdigit() else 10**9,
        )
        if not page_files:
            logger.warning(f"No markdown files in {md_folder}")
            return None

        # Metadata from first 3 pages
        initial_text = "\n".join(p.read_text(encoding="utf-8") for p in page_files[:3])
        self._extract_metadata(initial_text)

        # Per-page parsing
        for i, page_path in enumerate(page_files):
            page_num = i + 1
            page_text = page_path.read_text(encoding="utf-8")
            logger.info(f"Processing {doc_folder_name} - page {page_num}/{len(page_files)}")

            prompt = self.prompts.render("extraction/page_analysis.j2", page_text=page_text)
            response = structured_response(prompt, PageAnalysisResponse)
            if not response:
                logger.error(f"Skipping page {page_num} (parse failure)")
                continue

            for item in response.items:
                if item.type == PageItemType.CHAPTER_HEADER:
                    self._flush_active_subsection()
                    self.current_chapter = item.content
                    self.current_section = "General"
                    self.active_subsection = {
                        "chapter": self.current_chapter,
                        "section": self.current_section,
                        "subsection_id": "N/A",
                        "text": "",
                        "page_numbers": [page_num],
                    }
                elif item.type == PageItemType.SECTION_HEADER:
                    self._flush_active_subsection()
                    self.current_section = item.content
                    self.active_subsection = {
                        "chapter": self.current_chapter,
                        "section": self.current_section,
                        "subsection_id": "N/A",
                        "text": "",
                        "page_numbers": [page_num],
                    }
                elif item.type == PageItemType.NEW_SUBSECTION:
                    self._flush_active_subsection()
                    self.active_subsection = {
                        "chapter": self.current_chapter,
                        "section": self.current_section,
                        "subsection_id": item.id or "N/A",
                        "text": item.content,
                        "page_numbers": [page_num],
                    }
                elif item.type == PageItemType.CONTINUATION:
                    if self.active_subsection:
                        self.active_subsection["text"] += " " + item.content
                        self.active_subsection["page_numbers"].append(page_num)
                    else:
                        self.active_subsection = {
                            "chapter": self.current_chapter,
                            "section": self.current_section,
                            "subsection_id": "Introduction/Continuation",
                            "text": item.content,
                            "page_numbers": [page_num],
                        }

        self._flush_active_subsection()
        self._clean_final_results()

        output_path = self.base_path / doc_folder_name / "structured_output.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([e.model_dump() for e in self.final_results], f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(self.final_results)} subsections to {output_path}")
        return output_path
