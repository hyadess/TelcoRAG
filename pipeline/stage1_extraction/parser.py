"""
PDF -> Markdown via LlamaParse, page by page.

We split the PDF into single-page PDFs first, then parse each individually.
This is slower than batch but is more resilient to per-page failures and
lets the API key rotator distribute load.
"""

import logging
import os
from typing import Optional

from PyPDF2 import PdfReader, PdfWriter
from llama_cloud_services import LlamaParse

from utils.key_rotator import rotate_llamaparse_key

logger = logging.getLogger("PDFParser")


class Parser:
    def __init__(self, base_output_dir: str = "./knowledge_base/documents"):
        self.base_output_dir = base_output_dir

    def _get_llama_parser(self) -> LlamaParse:
        api_key = rotate_llamaparse_key()
        return LlamaParse(api_key=api_key, num_workers=4, verbose=True, language="en")

    def _split_pdf(self, file_path: str, pdf_output_folder: str) -> int:
        """Split a PDF into per-page PDFs. Returns total page count."""
        reader = PdfReader(file_path)
        total = len(reader.pages)
        logger.info(f"Splitting '{file_path}' into {total} pages...")

        for i, page in enumerate(reader.pages):
            writer = PdfWriter()
            writer.add_page(page)
            out_path = os.path.join(pdf_output_folder, f"page_{i + 1}.pdf")
            with open(out_path, "wb") as f:
                writer.write(f)
        return total

    def _parse_single_page(self, root_doc_name: str, pdf_page_path: str, page_number: int):
        markdown_folder = os.path.join(self.base_output_dir, root_doc_name, "markdowns")
        os.makedirs(markdown_folder, exist_ok=True)
        md_path = os.path.join(markdown_folder, f"page_{page_number}.md")

        if os.path.exists(md_path):
            logger.debug(f"Markdown already exists: {md_path}")
            return

        logger.info(f"Parsing page {page_number} of {root_doc_name}...")
        try:
            parser = self._get_llama_parser()
            result = parser.parse(pdf_page_path)
            if not result:
                logger.warning(f"No result for {pdf_page_path}")
                return

            # Handle SDK version differences
            text_content = ""
            if hasattr(result, "get_markdown_documents"):
                docs = result.get_markdown_documents(split_by_page=True)
                if docs and docs[0].text_resource:
                    text_content = docs[0].text_resource.text
            elif isinstance(result, list) and len(result) > 0:
                text_content = result[0].text

            with open(md_path, "w", encoding="utf-8") as f:
                f.write(text_content)
            logger.info(f"Saved {md_path}")

        except Exception as e:
            logger.error(f"Failed to parse page {page_number} of {root_doc_name}: {e}")

    def process_document(self, file_path: str):
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return

        filename = os.path.basename(file_path)
        folder_name = os.path.splitext(filename)[0]
        doc_root = os.path.join(self.base_output_dir, folder_name)
        pdf_chunks_dir = os.path.join(doc_root, "pdfs")
        os.makedirs(pdf_chunks_dir, exist_ok=True)

        logger.info(f"Starting parsing for: {folder_name}")
        try:
            total = self._split_pdf(file_path, pdf_chunks_dir)
            for i in range(total):
                page_pdf = os.path.join(pdf_chunks_dir, f"page_{i + 1}.pdf")
                self._parse_single_page(folder_name, page_pdf, i + 1)
            logger.info(f"Parsing complete for {folder_name}")
        except Exception as e:
            logger.critical(f"Critical error parsing {file_path}: {e}")
