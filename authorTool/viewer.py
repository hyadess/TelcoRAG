"""
The evidence overlay — a retrieved chunk beside the PDF page it came from.

The navigation model (DESIGN.md §5.4) is a **flattened deck**: one linear list
of ``(chunk, page)`` positions across every displayed chunk. ``←`` / ``→`` walk
that list, crossing chunk boundaries, and a chunk switcher jumps to the first
page of any chunk. Two denominators are always on screen —

    Chunk 3 of 20 · ISP · page 16 of 47 · deck 7 of 58

— because *page 16 of 47* locates the reader in the document and *deck 7 of 58*
locates them in the evidence. The ends do not wrap: running out of evidence is
information, and wrapping hides it.
"""

from __future__ import annotations

import csv
import html
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

from config.settings import PROJECT_ROOT

from . import evidence as ev

GOLD_PROVENANCE_FILE = PROJECT_ROOT / "humanEvaluation" / "pool" / "gold_provenance.csv"
GOLD_PROVENANCE_FIELDS = [
    "question_id",
    "doc_folder",
    "doc_name",
    "chapter",
    "section",
    "subsection_id",
    "page_numbers",
    "marked_by",
    "marked_at",
]

# Metadata text variants, best-first. The composed `text` is the default because
# it is what was embedded and what the generator saw; showing a cleaner variant
# by default would misrepresent the retrieval.
TEXT_VARIANTS = ["text", "subsection_text", "full_subsection_text", "bm25_text", "context_summary"]


# =============================================================================
# Opening / closing
# =============================================================================

def open_inspector(run_key: str, chunks: List[Dict[str, Any]], chunk_index: int, question: str = "") -> None:
    st.session_state["inspector"] = {
        "run_key": run_key,
        "chunks": chunks,
        "question": question,
        "jump_to_chunk": chunk_index,
    }


def close_inspector() -> None:
    st.session_state.pop("inspector", None)


def is_open() -> bool:
    return "inspector" in st.session_state


def _pos_key(run_key: str) -> str:
    return f"deck_pos::{run_key}"


# =============================================================================
# Rendering helpers
# =============================================================================

@st.cache_data(show_spinner=False)
def pdf_component_available() -> bool:
    """``st.pdf`` needs the streamlit-pdf frontend package to actually render."""
    try:
        import streamlit_pdf  # noqa: F401
        return True
    except Exception:
        return False


def _score_line(chunk: Dict[str, Any]) -> str:
    bits = []
    if chunk.get("score") is not None:
        bits.append(f"retrieval {float(chunk['score']):.4f}")
    if chunk.get("relevance_score") is not None:
        bits.append(f"rerank {float(chunk['relevance_score']):.4f}")
    for extra in ("boosted_score", "hierarchy_rank"):
        if chunk.get(extra) is not None:
            bits.append(f"{extra} {chunk[extra]}")
    return " · ".join(bits) or "no score recorded"


def highlight_markdown(page_text: str, chunk_text: str) -> str:
    """Mark the chunk's own lines inside the page markdown.

    A string match on whole lines, not a text-layer search of the PDF: it needs
    no extra dependency and answers the question the author is actually asking —
    *which part of this page is the chunk?*
    """
    chunk = re.sub(r"\s+", " ", chunk_text).strip()
    if len(chunk) < 25:
        return html.escape(page_text).replace("\n", "<br>")

    out = []
    for line in page_text.splitlines():
        normalised = re.sub(r"\s+", " ", line).strip()
        # Either direction: a page line that is part of the chunk, or a line
        # that contains the whole chunk. Page text and chunk text are the same
        # extraction, so containment is reliable; reflowed lines simply do not
        # match, and an unmarked page is a visible, honest outcome.
        matched = len(normalised) > 25 and (normalised in chunk or chunk in normalised)
        out.append(f"<mark>{html.escape(line)}</mark>" if matched else html.escape(line))
    return "<br>".join(out)


def _append_gold_provenance(chunk: Dict[str, Any], folder: Optional[str], question_id: str, marked_by: str) -> Path:
    """Append one row to humanEvaluation/pool/gold_provenance.csv.

    Capture is a by-product of reading the page rather than a separate
    transcription chore — transcription is where provenance errors come from.
    Rows are appended, never overwritten, so a second verifier's pass stays
    comparable with the first.
    """
    GOLD_PROVENANCE_FILE.parent.mkdir(parents=True, exist_ok=True)
    new_file = not GOLD_PROVENANCE_FILE.exists()
    row = {
        "question_id": question_id,
        "doc_folder": folder or "",
        "doc_name": chunk.get("doc_name", ""),
        "chapter": chunk.get("chapter", ""),
        "section": chunk.get("section", ""),
        "subsection_id": chunk.get("subsection_id", ""),
        "page_numbers": chunk.get("page_numbers", ""),
        "marked_by": marked_by,
        "marked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    with GOLD_PROVENANCE_FILE.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=GOLD_PROVENANCE_FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow(row)
    return GOLD_PROVENANCE_FILE


# =============================================================================
# The overlay
# =============================================================================

@st.dialog("Evidence", width="large")
def _dialog(index: Dict[str, Any]) -> None:
    state = st.session_state["inspector"]
    chunks: List[Dict[str, Any]] = state["chunks"]
    run_key: str = state["run_key"]

    deck = ev.build_deck(chunks, index)
    if not deck:
        st.info("This run returned no chunks to inspect.")
        return

    pos_key = _pos_key(run_key)
    pos = st.session_state.get(pos_key, 0)
    if state.get("jump_to_chunk") is not None:
        pos = ev.first_position_of_chunk(deck, state.pop("jump_to_chunk"))
    pos = max(0, min(pos, len(deck) - 1))

    item = deck[pos]
    chunk = chunks[item.chunk_index]
    resolved = ev.resolve(chunk, index)

    left, right = st.columns([0.42, 0.58], gap="medium")

    # ---------------- Left: what the retriever returned -------------------
    with left:
        st.markdown(f"**#{item.rank}** · {_score_line(chunk)}")
        st.caption(
            " · ".join(
                x for x in [
                    resolved.folder or "unresolved document",
                    chunk.get("chapter") or "",
                    chunk.get("section") or "",
                    f"§{chunk.get('subsection_id')}" if chunk.get("subsection_id") not in (None, "", "N/A") else "",
                    f"p.{chunk.get('page_numbers')}" if chunk.get("page_numbers") else "",
                ] if x
            )
        )
        st.caption(resolved.doc_name)

        available = [v for v in TEXT_VARIANTS if chunk.get(v)]
        variant = available[0] if available else None
        if len(available) > 1:
            variant = st.radio(
                "text shown",
                available,
                horizontal=True,
                key=f"variant::{run_key}",
                help="`text` is what was embedded and what the generator saw. The others are for debugging.",
            )
        body = str(chunk.get(variant, "")) if variant else "(no text on this chunk)"
        st.markdown(
            f"<div style='max-height:520px;overflow:auto;white-space:pre-wrap;"
            f"font-size:13px;line-height:1.5'>{html.escape(body)}</div>",
            unsafe_allow_html=True,
        )

        with st.expander("Mark as gold provenance"):
            question_id = st.text_input("question_id", key=f"gp_qid::{run_key}")
            marked_by = st.text_input("marked_by", key=f"gp_by::{run_key}")
            if st.button("Append row", key=f"gp_go::{run_key}", disabled=not (question_id and marked_by)):
                path = _append_gold_provenance(chunk, resolved.folder, question_id, marked_by)
                st.success(f"Appended to {path.relative_to(PROJECT_ROOT)}")

    # ---------------- Right: the source of truth --------------------------
    with right:
        nav_prev, nav_next, crumb = st.columns([0.1, 0.1, 0.8], vertical_alignment="center")
        if nav_prev.button("←", key=f"prev::{run_key}", disabled=pos == 0, width="stretch"):
            st.session_state[pos_key] = pos - 1
            st.rerun()
        if nav_next.button("→", key=f"next::{run_key}", disabled=pos >= len(deck) - 1, width="stretch"):
            st.session_state[pos_key] = pos + 1
            st.rerun()

        page_part = (
            f"page {item.page} of {item.page_count}" if item.page else "no page reference"
        )
        crumb.markdown(
            f"Chunk {item.rank} of {len(chunks)} · {item.folder or '—'} · {page_part} "
            f"· deck {pos + 1} of {len(deck)}"
        )

        ranks = [str(i + 1) for i in range(len(chunks))]
        picked = st.segmented_control(
            "jump to chunk", ranks, default=str(item.rank), key=f"jump::{run_key}"
        )
        if picked and int(picked) != item.rank:
            st.session_state[pos_key] = ev.first_position_of_chunk(deck, int(picked) - 1)
            st.rerun()

        if resolved.note:
            st.warning(resolved.note)

        as_markdown = st.toggle(
            "Markdown", key=f"md::{run_key}", help="Show the parsed page text instead of the PDF, with the chunk highlighted."
        )

        if item.page is None:
            st.info("No page to show for this chunk.")
        elif as_markdown:
            md_path = ev.page_markdown_path(index, item.doc_name, item.page)
            if md_path is None:
                st.warning(f"No markdown page file for p.{item.page} — the PDF is still available.")
            else:
                page_text = md_path.read_text(encoding="utf-8")
                variant_text = str(chunk.get("subsection_text") or chunk.get("text") or "")
                if len(variant_text) < 25:
                    variant_text = str(chunk.get("text") or variant_text)
                st.markdown(
                    "<div style='max-height:760px;overflow:auto;font-size:13px;line-height:1.55'>"
                    + highlight_markdown(page_text, variant_text)
                    + "</div>",
                    unsafe_allow_html=True,
                )
        else:
            pdf_path = ev.page_pdf_path(index, item.doc_name, item.page)
            if pdf_path is None:
                st.warning(f"Page file for p.{item.page} is missing.")
            elif pdf_component_available():
                st.pdf(str(pdf_path), height=760)
            else:
                st.warning(
                    "Inline PDF rendering needs the `streamlit-pdf` package "
                    "(`pip install -r authorTool/requirements.txt`). Use the Markdown "
                    "toggle, or download the page below."
                )
                st.download_button(
                    f"Download page_{item.page}.pdf",
                    pdf_path.read_bytes(),
                    file_name=f"{item.folder}_page_{item.page}.pdf",
                    mime="application/pdf",
                    key=f"dl::{run_key}::{pos}",
                )

        if resolved.source_pdf and resolved.source_pdf.exists():
            with open(resolved.source_pdf, "rb") as handle:
                st.download_button(
                    f"Open full document ({resolved.source_pdf.name})",
                    handle.read(),
                    file_name=resolved.source_pdf.name,
                    mime="application/pdf",
                    key=f"full::{run_key}::{item.chunk_index}",
                )

    st.session_state[pos_key] = pos


def render_if_open(index: Dict[str, Any]) -> None:
    """Call once at the end of the script — a dialog stays open only while it
    is re-invoked on every rerun."""
    if is_open():
        _dialog(index)
