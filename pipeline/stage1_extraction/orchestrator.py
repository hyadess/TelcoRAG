"""
Stage 1 orchestrator: PDF -> markdown -> structured JSON.

Pipeline:
  1. Parser splits the PDF and renders each page as markdown via LlamaParse.
  2. Extractor walks the markdowns and produces a structured JSON of subsections
     (chapter / section / subsection / text / page numbers).

The structured JSON is what stage 2 consumes. There is no LLM enrichment step:
chunks are built directly from the structured subsections, with the dense and
sparse indexes derived purely from the subsection text (and its headers).
"""

import logging
import os
from pathlib import Path
from typing import Optional

from config.settings import SETTINGS

from .extractor import Extractor
from .parser import Parser

logger = logging.getLogger("DocumentProcessor")


class DocumentProcessor:
    def __init__(self, root_doc_path: str):
        self.root_doc_path = root_doc_path
        domain = SETTINGS.domain
        document_type = domain.get("document_type", "legal documents")

        self.parser = Parser(base_output_dir=root_doc_path)
        self.extractor = Extractor(base_path=root_doc_path, document_type=document_type)

    def process_document(self, file_path: str) -> Optional[Path]:
        """
        Run the full stage-1 pipeline for a single PDF.
        Returns the path to the structured JSON.
        """
        logger.info(f"Stage 1 start: {file_path}")
        if not os.path.exists(file_path):
            logger.error(f"File does not exist: {file_path}")
            return None

        # 1. Parse PDF -> markdowns
        try:
            self.parser.process_document(file_path)
        except Exception as e:
            logger.critical(f"Parsing failed: {e}")
            return None

        # 2. Markdowns -> structured JSON
        filename = os.path.basename(file_path)
        doc_folder_name = os.path.splitext(filename)[0]

        try:
            structured_path = self.extractor.process_document(doc_folder_name)
        except Exception as e:
            logger.critical(f"Extraction failed: {e}")
            return None

        if structured_path is None:
            return None

        logger.info(f"Stage 1 done: {structured_path}")
        return structured_path
