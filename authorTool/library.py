"""
Knowledge base viewer — the corpus itself, independent of any run.

Every other tab enters the corpus through a *retrieved chunk*: the author sees
only the pages that retrieval happened to surface. This tab inverts that. It
opens any ingested document directly — page by page, and chunk by chunk — so an
author can answer the two questions retrieval cannot:

    Is the answer even in the knowledge base?
    If it is, how was that page chunked — and would retrieval ever see it?

Three views:

  Pages     the page PDFs as ingested, or the parsed markdown behind them
  Chunks    every chunk of this document in ingestion order, with its metadata
  Search    a plain substring sweep over all chunk text in the corpus

Reads local files only — no API calls, no database, nothing persisted. A
document that produced no chunks cannot appear here at all, which is itself the
finding: ``evidence.build_index`` lists it under warnings instead.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

from config.settings import KNOWLEDGE_BASE_DIR, PROJECT_ROOT

from . import evidence as ev
from . import viewer

PAGE_KEY = "library_page"
DOC_KEY = "library_doc"
JUMP_KEY = "library_jump"


# =============================================================================
# Loading — cached on the chunk file's mtime so re-ingestion invalidates it
# =============================================================================

def _chunk_file(folder: str, chunker: str) -> Path:
    return KNOWLEDGE_BASE_DIR / folder / f"structured_output_chunks__{chunker}.json"


@st.cache_data(show_spinner=False)
def _load_chunks(folder: str, chunker: str, _mtime: float) -> List[Dict[str, Any]]:
    """One document's chunks, flattened the way the retrievers return them.

    ``_mtime`` is part of the cache key and nothing else: re-ingesting a
    document changes it, so the cached copy is dropped rather than quietly
    showing the previous chunking next to the new answers.
    """
    path = _chunk_file(folder, chunker)
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))

    flattened: List[Dict[str, Any]] = []
    for chunk in raw:
        record = dict(chunk.get("metadata", {}) or {})
        record["id"] = chunk.get("id", "")
        record["text"] = chunk.get("text", "")
        flattened.append(record)
    return flattened


def document_chunks(folder: str, chunker: str) -> List[Dict[str, Any]]:
    path = _chunk_file(folder, chunker)
    mtime = path.stat().st_mtime if path.exists() else 0.0
    return _load_chunks(folder, chunker, mtime)


@st.cache_data(show_spinner=False)
def _page_files(pdf_dir: str) -> List[int]:
    directory = PROJECT_ROOT / pdf_dir
    if not directory.exists():
        return []
    pages = []
    for path in directory.glob("page_*.pdf"):
        stem = path.stem[len("page_"):]
        if stem.isdigit():
            pages.append(int(stem))
    return sorted(pages)


# =============================================================================
# Corpus search
# =============================================================================

@st.cache_data(show_spinner="Searching the corpus…")
def search_corpus(
    needle: str, chunker: str, _signature: Tuple[Tuple[str, float], ...], limit: int = 200
) -> List[Dict[str, Any]]:
    """Case-insensitive substring sweep over every chunk's text.

    Deliberately not the retriever: this is the control. When an author suspects
    retrieval missed something, the useful question is whether the words are in
    the corpus at all — a literal match answers that without the embedder, the
    reranker, or any of the knobs that could be the cause.
    """
    needle = needle.strip().lower()
    if not needle:
        return []

    hits: List[Dict[str, Any]] = []
    for folder, _ in _signature:
        for i, chunk in enumerate(document_chunks(folder, chunker)):
            haystack = " ".join(
                str(chunk.get(field, "") or "")
                for field in ("text", "subsection_text", "full_subsection_text")
            ).lower()
            if needle in haystack:
                hits.append({"folder": folder, "position": i, "chunk": chunk})
                if len(hits) >= limit:
                    return hits
    return hits


def _corpus_signature(index: Dict[str, Any]) -> Tuple[Tuple[str, float], ...]:
    """Folder + mtime per document — the cache key for a corpus-wide search."""
    return tuple(sorted((folder, mtime) for folder, mtime in (index.get("sources") or {}).items()))


# =============================================================================
# Pages
# =============================================================================

def _page_key(folder: str) -> str:
    return f"{PAGE_KEY}::{folder}"


def _goto(folder: str, page: Optional[int]) -> None:
    """Queue a jump to (document, page). ``render`` applies it on the next run.

    Streamlit forbids writing a widget's key once that widget has been
    instantiated in the same run, and the jump buttons live in the Chunks and
    Search tabs — which execute *after* the document selectbox and the page
    slider, because every tab body runs on every rerun. Queueing the jump under
    a key of our own and applying it at the top of the next run is what makes a
    jump legal from anywhere in this tab.
    """
    st.session_state[JUMP_KEY] = (folder, page)


def _apply_pending_jump() -> None:
    """Consume a queued jump. Must run before any widget in this tab."""
    jump = st.session_state.pop(JUMP_KEY, None)
    if not jump:
        return
    folder, page = jump
    st.session_state[DOC_KEY] = folder
    if page is not None:
        st.session_state[_page_key(folder)] = page


def _page_view(entry: Dict[str, Any], folder: str, chunks: List[Dict[str, Any]]) -> None:
    pages = _page_files(entry["pdf_dir"])
    if not pages:
        st.warning(
            f"No page PDFs under {entry['pdf_dir']} — this document was ingested "
            "without its page files, so its chunks cannot be checked against a source page."
        )
        return

    # The slider's own key is the single source of truth for the current page,
    # so the arrows and the slider can never disagree about where the author is.
    page_key = _page_key(folder)
    if st.session_state.get(page_key) not in pages:
        st.session_state[page_key] = pages[0]
    position = pages.index(st.session_state[page_key])

    prev_col, next_col, pick_col = st.columns([0.08, 0.08, 0.84], vertical_alignment="center")
    if prev_col.button("←", key=f"lib_prev::{folder}", disabled=position == 0, width="stretch"):
        _goto(folder, pages[position - 1])
        st.rerun()
    if next_col.button(
        "→", key=f"lib_next::{folder}", disabled=position >= len(pages) - 1, width="stretch"
    ):
        _goto(folder, pages[position + 1])
        st.rerun()
    current = pick_col.select_slider(
        "page", options=pages, key=page_key, label_visibility="collapsed"
    )

    # Which chunks claim this page — the point of reading a page in this tool.
    on_page = [
        chunk for chunk in chunks if current in ev.parse_page_numbers(chunk.get("page_numbers"))
    ]
    st.caption(
        f"page {current} of {entry.get('page_count', len(pages))} · "
        f"{len(on_page)} chunk(s) reference this page"
    )

    as_markdown = st.toggle(
        "Markdown",
        key=f"lib_md::{folder}",
        help="Show the parsed page text instead of the PDF — this is what was chunked and embedded.",
    )

    if as_markdown:
        md_path = PROJECT_ROOT / entry["markdown_dir"] / f"page_{current}.md"
        if not md_path.exists():
            st.warning(f"No markdown page file for p.{current} — the PDF is still available.")
        else:
            body = md_path.read_text(encoding="utf-8")
            # Highlighting the first chunk on the page shows where one chunk
            # ends inside a page the author is reading whole.
            marked = (
                viewer.highlight_markdown(body, str(on_page[0].get("subsection_text") or ""))
                if on_page
                else html.escape(body).replace("\n", "<br>")
            )
            st.markdown(
                "<div style='max-height:760px;overflow:auto;font-size:13px;line-height:1.55'>"
                + marked
                + "</div>",
                unsafe_allow_html=True,
            )
    else:
        pdf_path = PROJECT_ROOT / entry["pdf_dir"] / f"page_{current}.pdf"
        if not pdf_path.exists():
            st.warning(f"Page file for p.{current} is missing.")
        elif viewer.pdf_component_available():
            st.pdf(str(pdf_path), height=760)
        else:
            st.warning(
                "Inline PDF rendering needs the `streamlit-pdf` package "
                "(`pip install -r authorTool/requirements.txt`). Use the Markdown toggle, "
                "or download the page below."
            )
            st.download_button(
                f"Download page_{current}.pdf",
                pdf_path.read_bytes(),
                file_name=f"{folder}_page_{current}.pdf",
                mime="application/pdf",
                key=f"lib_dl::{folder}::{current}",
            )

    if on_page:
        with st.expander(f"Chunks on this page ({len(on_page)})", expanded=False):
            for chunk in on_page:
                _chunk_card(chunk, folder, key=f"onpage::{folder}::{chunk.get('id')}", show_goto=False)

    source_pdf = PROJECT_ROOT / entry["source_pdf"] if entry.get("source_pdf") else None
    if source_pdf and source_pdf.exists():
        st.download_button(
            f"Open full document ({source_pdf.name})",
            source_pdf.read_bytes(),
            file_name=source_pdf.name,
            mime="application/pdf",
            key=f"lib_full::{folder}",
        )


# =============================================================================
# Chunks
# =============================================================================

def _chunk_card(chunk: Dict[str, Any], folder: str, key: str, show_goto: bool = True) -> None:
    pages = ev.parse_page_numbers(chunk.get("page_numbers"))
    head, button = st.columns([0.88, 0.12], vertical_alignment="center")
    head.markdown(
        f"**{chunk.get('section') or chunk.get('chapter') or '(no section)'}** "
        f"· §{chunk.get('subsection_id') or '—'}"
    )
    head.caption(
        f"p.{chunk.get('page_numbers') or '—'} · seq {chunk.get('seq', '—')} · "
        f"{'split' if str(chunk.get('is_split')).lower() == 'true' else 'whole'} · "
        f"`{str(chunk.get('id', ''))[:8]}`"
    )
    if show_goto and pages and button.button("Page", key=f"goto::{key}", width="stretch"):
        _goto(folder, pages[0])
        st.rerun()

    body = str(chunk.get("text") or chunk.get("subsection_text") or "")
    st.markdown(
        f"<div style='max-height:260px;overflow:auto;white-space:pre-wrap;"
        f"font-size:13px;line-height:1.5'>{html.escape(body)}</div>",
        unsafe_allow_html=True,
    )
    st.divider()


def _chunk_view(folder: str, chunks: List[Dict[str, Any]]) -> None:
    if not chunks:
        st.info("This document produced no chunks.")
        return

    needle = st.text_input(
        "filter chunks", key=f"lib_filter::{folder}", placeholder="substring in text, section or chapter"
    ).strip().lower()
    shown = [
        chunk for chunk in chunks
        if not needle
        or needle in " ".join(
            str(chunk.get(field, "") or "")
            for field in ("text", "subsection_text", "section", "chapter")
        ).lower()
    ]
    st.caption(f"{len(shown)} of {len(chunks)} chunks · ingestion order")

    page_size = 25
    total_pages = max(1, (len(shown) + page_size - 1) // page_size)
    block = 0
    if total_pages > 1:
        block = st.number_input(
            "batch", min_value=1, max_value=total_pages, value=1, key=f"lib_block::{folder}"
        ) - 1
    for chunk in shown[block * page_size : (block + 1) * page_size]:
        _chunk_card(chunk, folder, key=f"chunk::{folder}::{chunk.get('id')}")


# =============================================================================
# Search
# =============================================================================

def _search_view(index: Dict[str, Any], chunker: str) -> None:
    needle = st.text_input(
        "search every chunk in the corpus",
        key="lib_search",
        placeholder="exact words, e.g. spectrum assignment fee",
    )
    if not needle.strip():
        st.caption(
            "A literal substring match over all chunk text — the control for "
            "*did retrieval miss it, or is it simply not in the corpus?*"
        )
        return

    hits = search_corpus(needle, chunker, _corpus_signature(index))
    if not hits:
        st.info(f"No chunk in the corpus contains {needle!r}.")
        return

    by_folder: Dict[str, int] = {}
    for hit in hits:
        by_folder[hit["folder"]] = by_folder.get(hit["folder"], 0) + 1
    st.caption(
        f"{len(hits)} chunk(s) in {len(by_folder)} document(s): "
        + " · ".join(f"{folder} ({n})" for folder, n in sorted(by_folder.items()))
    )

    for hit in hits[:50]:
        chunk, folder = hit["chunk"], hit["folder"]
        head, button = st.columns([0.88, 0.12], vertical_alignment="center")
        head.markdown(f"**{folder}** · {chunk.get('section') or chunk.get('chapter') or ''}")
        head.caption(f"p.{chunk.get('page_numbers') or '—'} · §{chunk.get('subsection_id') or '—'}")
        pages = ev.parse_page_numbers(chunk.get("page_numbers"))
        if button.button("Open", key=f"hit::{folder}::{hit['position']}", width="stretch"):
            _goto(folder, pages[0] if pages else None)
            st.rerun()
        st.markdown(_excerpt(str(chunk.get("text") or ""), needle), unsafe_allow_html=True)
    if len(hits) > 50:
        st.caption(f"…and {len(hits) - 50} more; narrow the search to see them.")


def _excerpt(text: str, needle: str, width: int = 240) -> str:
    """The matched words in context, with the match marked."""
    position = text.lower().find(needle.strip().lower())
    if position < 0:
        return f"<div style='font-size:13px'>{html.escape(text[:width])}…</div>"
    start = max(0, position - width // 2)
    end = min(len(text), position + len(needle) + width // 2)
    snippet = html.escape(text[start:end])
    marked = re.sub(
        f"({re.escape(html.escape(needle.strip()))})", r"<mark>\1</mark>", snippet, flags=re.IGNORECASE
    )
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(text) else ""
    return f"<div style='font-size:13px;line-height:1.5'>{prefix}{marked}{suffix}</div>"


# =============================================================================
# The tab
# =============================================================================

def render(index: Dict[str, Any]) -> None:
    _apply_pending_jump()

    documents = index.get("documents") or {}
    if not documents:
        st.info(
            f"No documents in the index. The knowledge base at {KNOWLEDGE_BASE_DIR} has no "
            f"`structured_output_chunks__{index.get('chunker')}.json` files — ingest it first."
        )
        return

    # The index is keyed by doc_name; the folder is what an author recognises.
    by_folder = {
        entry["folder"]: {**entry, "_doc_name": doc_name} for doc_name, entry in documents.items()
    }
    folders = sorted(by_folder)

    picked = st.selectbox(
        "document",
        folders,
        key=DOC_KEY,
        format_func=lambda f: f"{f} · {by_folder[f]['page_count']} pages · "
                              f"{by_folder[f]['n_chunks']} chunks",
    )
    entry = by_folder[picked]
    chunks = document_chunks(picked, index.get("chunker", ""))

    st.caption(entry["_doc_name"])
    summary = next((c.get("document_summary") for c in chunks if c.get("document_summary")), None)
    if summary:
        with st.expander("Document summary (as ingested)", expanded=False):
            st.markdown(str(summary))

    if entry.get("missing_markdown_pages"):
        st.warning(
            f"{len(entry['missing_markdown_pages'])} page(s) have a PDF but no parsed markdown: "
            f"p.{', '.join(str(p) for p in entry['missing_markdown_pages'][:20])}"
            f"{' …' if len(entry['missing_markdown_pages']) > 20 else ''}. "
            "Nothing on those pages was chunked or embedded."
        )

    pages_tab, chunks_tab, search_tab = st.tabs(
        [f"Pages ({entry['page_count']})", f"Chunks ({len(chunks)})", "Search corpus"]
    )
    with pages_tab:
        _page_view(entry, picked, chunks)
    with chunks_tab:
        _chunk_view(picked, chunks)
    with search_tab:
        _search_view(index, index.get("chunker", ""))
