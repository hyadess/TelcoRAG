"""
TelcoRAG author workbench — run the pipeline under any configuration, read the
answer, and inspect the exact evidence behind it.

    streamlit run authorTool/app.py --server.address=127.0.0.1

Offline and unauthenticated **by design** (DESIGN.md §1.2): it reads the local
knowledge base with the author's own API keys and must never be deployed.

Four tabs:
  Ask             one question under the sidebar configuration, with the full trace
  Compare         the same question with one configuration key varied
  Knowledge base  the ingested corpus itself — pages, chunks, and a literal search
  Saved runs      any run JSON on disk, in the same evidence viewer, at no API cost

It talks to no database. ``authorTool/__init__`` pins the chunk store to the
local knowledge base, so the Supabase settings in ``.env`` — which exist for the
deployed ``tool/`` app — are ignored here.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

# Allow `streamlit run authorTool/app.py` from the repository root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import QUERIES_FILE, REFERENCE_FILE, RUNS_DIR  # noqa: E402
from authorTool import (  # noqa: E402
    compare,
    config_panel,
    config_resolver as cr,
    evidence as ev,
    library,
    runner,
    viewer,
)

st.set_page_config(page_title="TelcoRAG · Author workbench", page_icon="🔬", layout="wide")

QUESTION_POOL = PROJECT_ROOT / "humanEvaluation" / "pool" / "questions.csv"


# =============================================================================
# Cached loads
# =============================================================================

@st.cache_data(show_spinner="Building the document index…")
def _index(rebuild_token: int = 0) -> Dict[str, Any]:
    return ev.load_index(force_rebuild=bool(rebuild_token))


@st.cache_data(show_spinner=False)
def _references() -> Dict[str, str]:
    from scripts.common import load_references

    return load_references(str(REFERENCE_FILE))


@st.cache_data(show_spinner=False)
def _question_bank() -> List[str]:
    """Questions from data/good_queries.csv and the human-evaluation pool."""
    questions: List[str] = []
    for path in (QUERIES_FILE, QUESTION_POOL):
        if not Path(path).exists():
            continue
        with open(path, "r", encoding="utf-8") as handle:
            reader = csv.reader(handle)
            header = next(reader, None)
            column = 0
            if header:
                lowered = [h.strip().lower() for h in header]
                column = lowered.index("question") if "question" in lowered else 0
            for row in reader:
                if len(row) > column and row[column].strip():
                    questions.append(row[column].strip())
    return list(dict.fromkeys(questions))


# =============================================================================
# Sidebar — configuration
# =============================================================================

def sidebar(base: Dict[str, Any]) -> Dict[str, Any]:
    st.sidebar.title("Configuration")
    st.sidebar.caption(
        "Every axis of `config/pipeline.yaml`, in any combination. "
        "Changes are an overlay — the file is never written."
    )

    overrides = config_panel.render(base)
    effective = cr.resolve(base, overrides)

    st.sidebar.divider()
    if st.sidebar.button("Reset to pipeline.yaml", width="stretch"):
        config_panel.reset_widgets()
        st.rerun()

    diffs = cr.diff_paths(base, effective)
    with st.sidebar.expander(f"Effective config · {len(diffs)} changed", expanded=False):
        st.code(f"sha256 {cr.config_hash(effective)}", language=None)
        if diffs:
            st.dataframe(
                {
                    "key": [d[0] for d in diffs],
                    "pipeline.yaml": [str(d[1]) for d in diffs],
                    "this run": [str(d[2]) for d in diffs],
                },
                width="stretch",
                hide_index=True,
            )
        else:
            st.caption("Identical to config/pipeline.yaml.")
        st.json(effective, expanded=False)

    counters = st.session_state.setdefault("counters", {"runs": 0, "llm_calls": 0, "seconds": 0.0})
    st.sidebar.caption(
        f"This session: {counters['runs']} runs · {counters['llm_calls']} LLM calls · "
        f"{counters['seconds']:.0f} s. Every run spends API credit."
    )
    return effective


# =============================================================================
# Chunk lists
# =============================================================================

def chunk_list(
    chunks: List[Dict[str, Any]],
    index: Dict[str, Any],
    run_key: str,
    question: str,
    *,
    limit: Optional[int] = None,
) -> None:
    """Render chunks with an Inspect button each. Used at every pipeline stage,
    not only the final ones — watching a chunk survive retrieval, survive
    reranking, then get dropped by relevance_filter is the whole diagnostic."""
    shown = chunks[:limit] if limit else chunks
    for i, chunk in enumerate(shown):
        resolved = ev.resolve(chunk, index)
        head, button = st.columns([0.88, 0.12], vertical_alignment="center")
        score = chunk.get("relevance_score", chunk.get("score"))
        pages = chunk.get("page_numbers") or "—"
        head.markdown(
            f"**#{i + 1}** {resolved.folder or resolved.doc_name} · "
            f"{chunk.get('section') or chunk.get('chapter') or ''}"
        )
        head.caption(
            f"p.{pages} · score {float(score):.4f}" if score is not None else f"p.{pages}"
        )
        if button.button("Inspect", key=f"inspect::{run_key}::{i}", width="stretch"):
            viewer.open_inspector(run_key, chunks, i, question)
            st.rerun()
    if limit and len(chunks) > limit:
        st.caption(f"…and {len(chunks) - limit} more")


def trace_panel(result: runner.RunResult, index: Dict[str, Any]) -> None:
    """Everything QueryTrace recorded, collapsed by default (DESIGN §6.2)."""
    trace = result.trace
    if trace is None:
        return
    key = result.config_hash

    with st.expander("Pipeline trace", expanded=False):
        st.caption(
            f"{trace.merged_candidates} candidates → {trace.deduped_candidates} unique → "
            f"{len(trace.reranked_chunks)} reranked → {len(trace.final_chunks)} final"
        )

        if trace.reformulated_queries:
            st.markdown("**Query fan-out**")
            for record in trace.round1_variants:
                st.markdown(f"- `{record['variant_query']}` → {record['n_results']} hits")

        if trace.two_call_enabled:
            st.markdown("**Gap analysis**")
            if trace.gap_analysis:
                st.json(trace.gap_analysis, expanded=False)
            else:
                st.caption("No gap analysis recorded (no round-1 candidates).")
            if trace.round2_variants:
                for record in trace.round2_variants:
                    st.markdown(f"- round 2: `{record['variant_query']}` → {record['n_results']} hits")
                st.caption(f"round 2 added {trace.round2_added} chunks")

        stages = [(f"round 1 · {r['variant_query'][:60]}", r["results"]) for r in trace.round1_variants]
        stages += [(f"round 2 · {r['variant_query'][:60]}", r["results"]) for r in trace.round2_variants]
        stages += [("reranked", trace.reranked_chunks), ("final", trace.final_chunks)]
        names = [name for name, chunks in stages if chunks]
        if names:
            stage = st.selectbox("chunks at stage", names, key=f"stage::{key}")
            chunks = dict((name, chunks) for name, chunks in stages)[stage]
            chunk_list(chunks, index, f"{key}::{stage}", result.question, limit=30)


# =============================================================================
# Tabs
# =============================================================================

def ask_tab(effective: Dict[str, Any], index: Dict[str, Any]) -> None:
    bank = _question_bank()
    picked = st.selectbox(
        "question",
        ["— type your own —"] + bank,
        key="picked_question",
        label_visibility="collapsed",
    )
    default = "" if picked.startswith("—") else picked
    question = st.text_area("question", value=default, key="question_text", height=80, label_visibility="collapsed")

    run_col, hash_col = st.columns([0.2, 0.8], vertical_alignment="center")
    go = run_col.button("Run", type="primary", disabled=not question.strip(), width="stretch")
    hash_col.caption(f"{cr.summarise(effective)} · `{cr.config_hash(effective)[:12]}`")

    if go:
        with st.spinner("Retrieving and generating…"):
            result = runner.run_question(question, effective, label="ask", references=_references())
        st.session_state["last_result"] = result

    result: Optional[runner.RunResult] = st.session_state.get("last_result")
    if result is None:
        return

    if not result.ok:
        st.error(result.error)
        return

    st.subheader("Answer")
    st.markdown(result.answer or "_(the model returned an empty answer)_")
    st.caption(
        f"{result.elapsed_seconds:.1f} s · {result.llm_calls} LLM calls · "
        f"{len(result.chunks)} chunks · `{result.config_hash[:12]}`"
    )

    references = _references()
    with st.expander("Reference answer", expanded=False):
        if result.trace.reference:
            st.markdown(result.trace.reference)
        elif references:
            # Matching trims whitespace but is otherwise exact: one stray
            # character yields no match, and downstream that silently scores 0.
            st.caption("No reference found for this exact question text.")
        else:
            st.caption(f"No reference file at {REFERENCE_FILE.relative_to(PROJECT_ROOT)}.")

    st.subheader(f"Retrieved chunks ({len(result.chunks)})")
    if result.chunks:
        chunk_list(result.chunks, index, result.config_hash, result.question)
    else:
        st.info("This configuration returned no chunks.")

    trace_panel(result, index)

    if st.button("Save this run to data/runs/"):
        path = runner.save_results([result])
        st.success(f"Saved {path.relative_to(PROJECT_ROOT)}" if path else "Nothing to save.")


def compare_tab(base: Dict[str, Any], overrides: Dict[str, Any], index: Dict[str, Any]) -> None:
    question = st.text_area(
        "question", value=st.session_state.get("question_text", ""), key="compare_question", height=80
    )
    results = compare.render(base, overrides, question, references=_references())
    compare.render_results(results, index, question)
    if results and st.button("Save comparison to data/runs/", key="save_compare"):
        path = runner.save_results(results, label="author_compare")
        st.success(f"Saved {path.relative_to(PROJECT_ROOT)}" if path else "Nothing to save.")


def saved_runs_tab(index: Dict[str, Any]) -> None:
    """Open any run JSON on disk in the same evidence viewer — no API calls."""
    paths = sorted(RUNS_DIR.glob("*.json"), reverse=True) if RUNS_DIR.exists() else []
    paths += sorted((PROJECT_ROOT / "data" / "experiments").glob("*/run.json"))
    if not paths:
        st.info(f"No run JSON under {RUNS_DIR.relative_to(PROJECT_ROOT)} yet.")
        return

    picked = st.selectbox("run", paths, format_func=lambda p: p.stem if p.name != "run.json" else p.parent.name)
    data = json.loads(Path(picked).read_text(encoding="utf-8"))
    st.caption(
        f"{data.get('label', '')} · {data.get('created_at', '')} · "
        f"{data.get('n_queries', len(data.get('queries', [])))} queries"
    )
    with st.expander("Run config", expanded=False):
        st.json(data.get("config", {}), expanded=False)

    queries = data.get("queries", [])
    if not queries:
        return
    labels = [f"{i + 1}. {q.get('query', '')[:90]}" for i, q in enumerate(queries)]
    chosen = st.selectbox("query", range(len(queries)), format_func=lambda i: labels[i])
    record = queries[chosen]

    st.subheader("Answer")
    st.markdown(record.get("answer") or "_(no answer recorded)_")
    if record.get("reference"):
        with st.expander("Reference answer"):
            st.markdown(record["reference"])

    chunks = record.get("final_chunks", [])
    st.subheader(f"Retrieved chunks ({len(chunks)})")
    run_key = f"saved::{Path(picked).stem}::{chosen}"
    chunk_list(chunks, index, run_key, record.get("query", ""))


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    st.title("Author workbench")

    index = _index(st.session_state.get("index_rebuilds", 0))
    warnings = index.get("warnings") or []
    if warnings:
        with st.expander(f"Document index: {len(warnings)} warning(s)", expanded=False):
            for warning in warnings:
                st.warning(warning)

    base = cr.base_config()
    effective = sidebar(base)
    overrides = {path: after for path, _, after in cr.diff_paths(base, effective)}

    with st.sidebar.expander("Document index", expanded=False):
        st.caption(
            f"{len(index.get('documents', {}))} documents · chunker "
            f"`{index.get('chunker')}` · built {index.get('built_at', '')}"
        )
        if st.button("Rebuild index", width="stretch"):
            st.session_state["index_rebuilds"] = st.session_state.get("index_rebuilds", 0) + 1
            st.rerun()

    ask, compare_view, knowledge_base, saved = st.tabs(
        ["Ask", "Compare", "Knowledge base", "Saved runs"]
    )
    with ask:
        ask_tab(effective, index)
    with compare_view:
        compare_tab(base, overrides, index)
    with knowledge_base:
        library.render(index)
    with saved:
        saved_runs_tab(index)

    # A dialog stays open only while it is re-invoked on every rerun.
    viewer.render_if_open(index)


main()
