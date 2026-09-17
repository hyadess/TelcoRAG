"""
Evidence resolution — chunk metadata to the page files it came from.

Retrieved chunks carry ``doc_name`` (the full document title) and
``page_numbers`` (a comma-separated string of 1-indexed pages). Neither points
at a file. This module closes that gap:

    doc_name     -> knowledge_base/documents/<FOLDER>/
    page_numbers -> <FOLDER>/pdfs/page_<n>.pdf  +  <FOLDER>/markdowns/page_<n>.md

The mapping is built by scanning the chunk JSONs once and cached in
``authorTool/.cache/document_index.json``. It is rebuilt automatically when any
chunk file is newer than the cache, because a stale index silently resolves
pages to the wrong document — the worst failure this tool could have.

See DESIGN.md §2.4 and §5.2/§5.3.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.settings import KNOWLEDGE_BASE_DIR, PROJECT_ROOT, get_chunker_name

logger = logging.getLogger("authorTool.evidence")

CACHE_DIR = Path(__file__).resolve().parent / ".cache"
INDEX_FILE = CACHE_DIR / "document_index.json"
RESOURCES_DIR = PROJECT_ROOT / "resources"


# =============================================================================
# Page number parsing
# =============================================================================

def parse_page_numbers(value: Any) -> List[int]:
    """Parse the ``page_numbers`` metadata field into sorted unique ints.

    The field is a string for every chunk in this corpus, usually a single
    number but sometimes a long, *non-contiguous* list ("51, 52, 53, ... 114").
    Never expand a span into ``range()`` — the gaps are real, and filling them
    fabricates provenance.
    """
    if value is None:
        return []
    if isinstance(value, int):
        return [value]
    if isinstance(value, (list, tuple)):
        parts = [str(v) for v in value]
    else:
        parts = str(value).split(",")

    pages = set()
    for part in parts:
        part = part.strip()
        if part.isdigit():
            n = int(part)
            if n > 0:
                pages.add(n)
    return sorted(pages)


# =============================================================================
# Index construction
# =============================================================================

def _chunk_files(chunker: str, kb_dir: Path) -> List[Path]:
    return sorted(kb_dir.glob(f"*/structured_output_chunks__{chunker}.json"))


def _page_numbers_in_dir(directory: Path, suffix: str) -> List[int]:
    pages = []
    for p in directory.glob(f"page_*{suffix}"):
        stem = p.stem[len("page_"):]
        if stem.isdigit():
            pages.append(int(stem))
    return sorted(pages)


def build_index(chunker: Optional[str] = None, kb_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Scan every chunk file and build the ``doc_name -> folder`` index.

    Asserts ``max(page_numbers) <= page_count`` per document. A failure is
    recorded in ``warnings`` and surfaced in the UI rather than raised — one bad
    document must not block the whole tool.
    """
    chunker = (chunker or get_chunker_name()).strip().lower()
    kb_dir = Path(kb_dir or KNOWLEDGE_BASE_DIR)

    documents: Dict[str, Any] = {}
    warnings: List[str] = []
    sources: Dict[str, float] = {}

    for chunk_file in _chunk_files(chunker, kb_dir):
        folder = chunk_file.parent.name
        sources[folder] = chunk_file.stat().st_mtime
        try:
            chunks = json.loads(chunk_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            warnings.append(f"{folder}: cannot read chunk file ({exc})")
            continue

        names = set()
        max_page = 0
        for chunk in chunks:
            meta = chunk.get("metadata", {}) or {}
            name = meta.get("doc_name")
            if name:
                names.add(str(name))
            pages = parse_page_numbers(meta.get("page_numbers"))
            if pages:
                max_page = max(max_page, pages[-1])

        if not names:
            warnings.append(f"{folder}: no doc_name in any chunk — chunks from it cannot be resolved")
            continue
        if len(names) > 1:
            # The 1:1 assumption is what makes the whole index well-defined.
            warnings.append(
                f"{folder}: {len(names)} distinct doc_name values; only the first is indexed"
            )

        pdf_dir = chunk_file.parent / "pdfs"
        md_dir = chunk_file.parent / "markdowns"
        pdf_pages = _page_numbers_in_dir(pdf_dir, ".pdf") if pdf_dir.exists() else []
        md_pages = _page_numbers_in_dir(md_dir, ".md") if md_dir.exists() else []
        page_count = len(pdf_pages)

        if max_page > page_count:
            warnings.append(
                f"{folder}: metadata references page {max_page} but only {page_count} page PDFs "
                f"exist — set page_offset for this document before trusting its pages"
            )

        doc_name = sorted(names)[0]
        if doc_name in documents:
            warnings.append(
                f"doc_name {doc_name!r} appears in both {documents[doc_name]['folder']} "
                f"and {folder}; pages will resolve to the first"
            )
            continue

        source_pdf = RESOURCES_DIR / f"{folder}.pdf"
        documents[doc_name] = {
            "folder": folder,
            "page_count": page_count,
            "pdf_dir": str(pdf_dir.relative_to(PROJECT_ROOT)),
            "markdown_dir": str(md_dir.relative_to(PROJECT_ROOT)),
            "page_offset": 0,
            "source_pdf": str(source_pdf.relative_to(PROJECT_ROOT)) if source_pdf.exists() else None,
            "max_metadata_page": max_page,
            "n_chunks": len(chunks),
            "missing_markdown_pages": sorted(set(pdf_pages) - set(md_pages)),
        }

    index = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "chunker": chunker,
        "knowledge_base_dir": str(kb_dir),
        "documents": documents,
        "sources": sources,
        "warnings": warnings,
    }
    logger.info("Built document index: %d documents, %d warnings", len(documents), len(warnings))
    return index


def _current_sources(chunker: str, kb_dir: Path) -> Dict[str, float]:
    return {p.parent.name: p.stat().st_mtime for p in _chunk_files(chunker, kb_dir)}


def index_is_stale(index: Dict[str, Any]) -> bool:
    """True when chunks were re-ingested, added, or removed since the build."""
    chunker = index.get("chunker") or get_chunker_name()
    kb_dir = Path(index.get("knowledge_base_dir") or KNOWLEDGE_BASE_DIR)
    if chunker != get_chunker_name():
        return True
    cached = index.get("sources") or {}
    current = _current_sources(chunker, kb_dir)
    if set(cached) != set(current):
        return True
    return any(current[f] > cached.get(f, 0) for f in current)


def load_index(force_rebuild: bool = False) -> Dict[str, Any]:
    """Return the document index, rebuilding it when missing or stale."""
    if not force_rebuild and INDEX_FILE.exists():
        try:
            index = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
            if not index_is_stale(index):
                return index
            logger.info("Document index is stale — rebuilding")
        except (OSError, json.JSONDecodeError):
            logger.warning("Document index unreadable — rebuilding")

    index = build_index()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    return index


# =============================================================================
# Chunk -> pages
# =============================================================================

@dataclass
class Evidence:
    """Where one retrieved chunk came from, as far as it can be resolved."""

    doc_name: str
    folder: Optional[str] = None
    page_count: int = 0
    pages: List[int] = field(default_factory=list)          # as recorded in metadata
    available_pages: List[int] = field(default_factory=list)  # page PDFs that exist
    missing_pages: List[int] = field(default_factory=list)
    source_pdf: Optional[Path] = None
    note: Optional[str] = None

    @property
    def resolved(self) -> bool:
        return bool(self.available_pages)


def resolve(chunk: Dict[str, Any], index: Dict[str, Any]) -> Evidence:
    """Resolve one retrieved chunk to its page files.

    Chunks arrive flattened (metadata merged into the top level) from the
    retrievers, but nested ``metadata`` is accepted too so saved run JSON and
    raw chunk files work the same way.
    """
    meta = chunk.get("metadata") if isinstance(chunk.get("metadata"), dict) else chunk
    doc_name = str(meta.get("doc_name") or chunk.get("doc_name") or "").strip()
    entry = (index.get("documents") or {}).get(doc_name)

    if entry is None:
        return Evidence(
            doc_name=doc_name or "(no doc_name)",
            note=(
                f"doc_name {doc_name!r} is not in the document index — rebuild the index "
                "if chunks were re-ingested"
                if doc_name
                else "chunk carries no doc_name; its source page cannot be located"
            ),
        )

    raw_pages = parse_page_numbers(meta.get("page_numbers", chunk.get("page_numbers")))
    offset = int(entry.get("page_offset", 0) or 0)
    pages = [p + offset for p in raw_pages]

    folder = entry["folder"]
    pdf_dir = PROJECT_ROOT / entry["pdf_dir"]
    available = [p for p in pages if (pdf_dir / f"page_{p}.pdf").exists()]
    missing = [p for p in pages if p not in available]

    note = None
    if not raw_pages:
        note = "no page reference recorded for this chunk"
    elif missing:
        note = f"page file missing for p.{', '.join(str(p) for p in missing)}"

    source_pdf = PROJECT_ROOT / entry["source_pdf"] if entry.get("source_pdf") else None
    return Evidence(
        doc_name=doc_name,
        folder=folder,
        page_count=int(entry.get("page_count", 0)),
        pages=pages,
        available_pages=available,
        missing_pages=missing,
        source_pdf=source_pdf,
        note=note,
    )


def page_pdf_path(index: Dict[str, Any], doc_name: str, page: int) -> Optional[Path]:
    entry = (index.get("documents") or {}).get(doc_name)
    if not entry:
        return None
    path = PROJECT_ROOT / entry["pdf_dir"] / f"page_{page}.pdf"
    return path if path.exists() else None


def page_markdown_path(index: Dict[str, Any], doc_name: str, page: int) -> Optional[Path]:
    entry = (index.get("documents") or {}).get(doc_name)
    if not entry:
        return None
    path = PROJECT_ROOT / entry["markdown_dir"] / f"page_{page}.md"
    return path if path.exists() else None


# =============================================================================
# The flattened page deck (DESIGN §5.4)
# =============================================================================

@dataclass
class DeckItem:
    """One position in the evidence deck: a (chunk, page) pair."""

    chunk_index: int      # 0-based index into the displayed chunk list
    rank: int             # 1-based rank shown to the author
    doc_name: str
    folder: Optional[str]
    page: Optional[int]   # None when the chunk has no resolvable page
    page_count: int = 0


def build_deck(chunks: List[Dict[str, Any]], index: Dict[str, Any]) -> List[DeckItem]:
    """Flatten chunks into one linear list of (chunk, page) positions.

    Chunks whose pages cannot be resolved still get exactly one position, so
    every chunk stays reachable with the arrow keys and none is silently
    dropped from the evidence walk.
    """
    deck: List[DeckItem] = []
    for i, chunk in enumerate(chunks):
        ev = resolve(chunk, index)
        if ev.available_pages:
            for page in ev.available_pages:
                deck.append(
                    DeckItem(i, i + 1, ev.doc_name, ev.folder, page, ev.page_count)
                )
        else:
            deck.append(DeckItem(i, i + 1, ev.doc_name, ev.folder, None, ev.page_count))
    return deck


def first_position_of_chunk(deck: List[DeckItem], chunk_index: int) -> int:
    for pos, item in enumerate(deck):
        if item.chunk_index == chunk_index:
            return pos
    return 0
