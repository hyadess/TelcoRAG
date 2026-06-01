"""
TelcoRAG — run & trace viewer (Streamlit).

Browse the full intermediate logs of any retrieval run saved by
``scripts/run_retrieval.py`` (data/runs/*.json) or any experiment combo
(data/experiments/*/run.json):

  - run config snapshot + summary metrics
  - per query: the reformulated query variants (round 1) and the chunks each
    retrieved, the two-call gap analysis + round-2 follow-ups, the reranked
    chunks, the post-processed final chunks, and the final answer
  - retrieval diagnostics: raw vs boosted scores, hierarchy ranks, and which
    chunks were sibling- or neighbour-expanded

Run:  streamlit run app.py
"""

import json
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
RUNS_DIR = PROJECT_ROOT / "data" / "runs"
EXPERIMENTS_DIR = PROJECT_ROOT / "data" / "experiments"

st.set_page_config(page_title="TelcoRAG · Run Viewer", page_icon="🔭", layout="wide")

# ----------------------------------------------------------------------------- CSS
st.markdown(
    """
    <style>
      .block-container { padding-top: 2rem; max-width: 1300px; }
      .badge { display:inline-block; padding:2px 9px; border-radius:11px; font-size:11px;
               font-weight:600; margin-right:5px; letter-spacing:.02em; }
      .b-neighbor { background:#e8f0ff; color:#1d4ed8; }
      .b-sibling  { background:#eafaf1; color:#0f9d58; }
      .b-r1       { background:#f3effe; color:#7c3aed; }
      .b-r2       { background:#fff4e5; color:#c2680c; }
      .b-high     { background:#e6f7ec; color:#137a3b; }
      .b-med      { background:#fff7e0; color:#9a6700; }
      .b-low      { background:#fdeaea; color:#b42318; }
      .chunk-card { border:1px solid #ececf1; border-radius:12px; padding:14px 16px;
                    margin-bottom:10px; background:#ffffff; }
      .chunk-head { font-size:12.5px; color:#5b5b6b; margin-bottom:6px; }
      .chunk-text { font-size:13.5px; color:#1f1f29; white-space:pre-wrap; line-height:1.5; }
      .score-track { background:#eef0f4; border-radius:6px; height:7px; width:100%; margin-top:5px; }
      .score-fill  { background:linear-gradient(90deg,#6366f1,#22c55e); height:7px; border-radius:6px; }
      .q-title { font-size:15px; font-weight:600; color:#111; }
      .muted { color:#8a8a96; font-size:12.5px; }
      .answer-box { border-left:4px solid #6366f1; background:#fafaff; padding:14px 18px;
                    border-radius:8px; font-size:14px; line-height:1.6; }
      .ref-box { border-left:4px solid #94a3b8; background:#f8fafc; padding:12px 16px;
                 border-radius:8px; font-size:13px; line-height:1.55; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------------- helpers
def discover_runs():
    """Return [(label, path)] for every saved run, newest first."""
    runs = []
    if RUNS_DIR.exists():
        for p in sorted(RUNS_DIR.glob("*.json"), reverse=True):
            runs.append((f"run · {p.stem}", p))
    if EXPERIMENTS_DIR.exists():
        for p in sorted(EXPERIMENTS_DIR.glob("*/run.json")):
            runs.append((f"experiment · {p.parent.name}", p))
    return runs


@st.cache_data(show_spinner=False)
def load_run(path_str: str):
    with open(path_str, "r", encoding="utf-8") as f:
        return json.load(f)


def score_of(chunk):
    for k in ("relevance_score", "score", "base_score"):
        if k in chunk and chunk[k] is not None:
            return float(chunk[k])
    return 0.0


def score_bar(value, vmax=1.0):
    pct = max(0.0, min(100.0, (value / vmax) * 100 if vmax else 0))
    return f'<div class="score-track"><div class="score-fill" style="width:{pct:.0f}%"></div></div>'


def expansion_badges(chunk):
    out = ""
    if chunk.get("neighbor_expanded"):
        out += '<span class="badge b-neighbor">neighbour-expanded</span>'
    dec = chunk.get("neighbor_decision")
    if dec == "high":
        out += '<span class="badge b-high">relevance: high</span>'
    elif dec == "medium":
        out += '<span class="badge b-med">relevance: medium</span>'
    elif dec == "low":
        out += '<span class="badge b-low">relevance: low</span>'
    if chunk.get("sibling_expanded"):
        out += '<span class="badge b-sibling">sibling</span>'
    return out


def render_chunk(chunk, idx=None, vmax=1.0, show_text=True):
    doc = chunk.get("doc_name", "—")
    ch = chunk.get("chapter", "")
    sec = chunk.get("section", "")
    sid = chunk.get("subsection_id", "")
    sc = score_of(chunk)
    ranks = []
    for fld, lbl in (("hier_doc_name_rank", "doc"), ("hier_chapter_rank", "chap"), ("hier_section_rank", "sec")):
        if fld in chunk:
            ranks.append(f"{lbl}#{chunk[fld]}")
    rank_str = (" · ranks: " + ", ".join(ranks)) if ranks else ""
    prefix = f"[{idx}] " if idx is not None else ""
    head = f"{prefix}<b>{doc}</b>"
    if ch:
        head += f" · {ch}"
    if sec:
        head += f" · {sec}"
    if sid and sid != "N/A":
        head += f" · §{sid}"
    head += f" · <b>score {sc:.3f}</b>{rank_str}"

    text = (chunk.get("subsection_text", "") or "")
    body = f'<div class="chunk-text">{text}</div>' if show_text else ""
    st.markdown(
        f'<div class="chunk-card"><div class="chunk-head">{head}</div>'
        f'{expansion_badges(chunk)}{score_bar(sc, vmax)}{body}</div>',
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------------------------- sidebar
st.sidebar.title("🔭 TelcoRAG")
st.sidebar.caption("Retrieval run & intermediate-log viewer")

runs = discover_runs()
if not runs:
    st.title("No runs found yet")
    st.info(
        "Run a retrieval first:\n\n"
        "```bash\npython -m scripts.run_retrieval\n```\n\n"
        "Traces are written to `data/runs/` and appear here automatically."
    )
    st.stop()

labels = [lbl for lbl, _ in runs]
choice = st.sidebar.selectbox("Select a run", labels)
run_path = dict(runs)[choice]
run = load_run(str(run_path))

cfg = run.get("config", {})
st.sidebar.markdown("### Configuration")
st.sidebar.json(cfg, expanded=False)


# ----------------------------------------------------------------------------- header + overview
st.markdown(f"## {run.get('label', 'run')}  ·  `{run.get('run_id', '')}`")
st.caption(f"created {run.get('created_at', '')} · {run.get('elapsed_seconds', 0)}s total")

queries = run.get("queries", [])
n_neighbor = sum(
    1 for q in queries for c in q.get("final_chunks", []) if c.get("neighbor_expanded")
)
n_two_call_used = sum(
    1 for q in queries if q.get("gap_analysis") and not q["gap_analysis"].get("sufficient", True)
)

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Queries", len(queries))
m2.metric("Retriever", cfg.get("retriever", "—"))
m3.metric("Operator", cfg.get("query_strategy", "—"))
m4.metric("Two-call rounds used", n_two_call_used if cfg.get("two_call_enabled") else "off")
m5.metric("Neighbour-expanded chunks", n_neighbor)

st.divider()

tab_explore, tab_pipeline, tab_raw = st.tabs(["🔎 Query explorer", "🧭 Stage log", "🧩 Raw JSON"])


# ----------------------------------------------------------------------------- query explorer
with tab_explore:
    if not queries:
        st.warning("This run has no queries.")
    else:
        qlabels = [f"{i+1}. {q['query'][:70]}" for i, q in enumerate(queries)]
        qi = st.selectbox("Query", range(len(queries)), format_func=lambda i: qlabels[i])
        q = queries[qi]

        st.markdown(f'<div class="q-title">{q["query"]}</div>', unsafe_allow_html=True)
        st.caption(f"elapsed {q.get('elapsed_seconds', 0)}s")

        # Final answer
        st.markdown("#### Answer")
        st.markdown(f'<div class="answer-box">{q.get("answer","") or "—"}</div>', unsafe_allow_html=True)
        if q.get("reference"):
            with st.expander("Reference answer"):
                st.markdown(f'<div class="ref-box">{q["reference"]}</div>', unsafe_allow_html=True)

        # Reformulation (round 1)
        st.markdown("#### 1 · Query reformulation (round 1)")
        rq = q.get("reformulated_queries", [])
        st.caption(f"Operator produced {len(rq)} variant(s)")
        for v in q.get("round1_variants", []):
            with st.expander(f'“{v.get("variant_query","")}”  —  {v.get("n_results",0)} chunks'):
                results = v.get("results", [])
                vmax = max((score_of(c) for c in results), default=1.0) or 1.0
                for j, c in enumerate(results[:15], 1):
                    render_chunk(c, idx=j, vmax=vmax, show_text=False)

        # Two-call
        if q.get("two_call_enabled"):
            st.markdown("#### 2 · Two-call gap analysis")
            ga = q.get("gap_analysis")
            if ga:
                suff = ga.get("sufficient", True)
                st.markdown(
                    f'<span class="badge {"b-high" if suff else "b-low"}">'
                    f'{"sufficient — no 2nd round" if suff else "insufficient — 2nd round triggered"}</span>',
                    unsafe_allow_html=True,
                )
                st.caption(ga.get("reasoning", ""))
                if not suff:
                    if ga.get("missing_info"):
                        st.markdown(f"**Missing:** {ga['missing_info']}")
                    if ga.get("followup_queries"):
                        st.markdown("**Follow-up queries:**")
                        for fq in ga["followup_queries"]:
                            st.markdown(f"- {fq}")
                    r2 = q.get("round2_variants", [])
                    if r2:
                        st.caption(f"Round 2 added {q.get('round2_added',0)} new unique chunks across {len(r2)} variant(s)")
                        for v in r2:
                            with st.expander(f'round-2 “{v.get("variant_query","")}” — {v.get("n_results",0)} chunks'):
                                for j, c in enumerate(v.get("results", [])[:15], 1):
                                    render_chunk(c, idx=j, show_text=False)
            else:
                st.caption("No gap analysis recorded.")

        # Reranked
        st.markdown("#### 3 · After rerank")
        reranked = q.get("reranked_chunks", [])
        st.caption(f"{len(reranked)} chunks (merged candidates → reranked against the main query)")
        vmax = max((score_of(c) for c in reranked), default=1.0) or 1.0
        with st.expander("Show reranked chunks", expanded=False):
            for j, c in enumerate(reranked, 1):
                render_chunk(c, idx=j, vmax=vmax, show_text=False)

        # Final
        st.markdown("#### 4 · Final chunks (post-processed → sent to generator)")
        final = q.get("final_chunks", [])
        st.caption(f"{len(final)} chunks")
        vmax = max((score_of(c) for c in final), default=1.0) or 1.0
        for j, c in enumerate(final, 1):
            render_chunk(c, idx=j, vmax=vmax, show_text=True)


# ----------------------------------------------------------------------------- stage log
with tab_pipeline:
    st.markdown("### Pipeline stages")
    st.caption("How each query flows through the configured pipeline.")
    for i, q in enumerate(queries, 1):
        ga = q.get("gap_analysis") or {}
        tc = "off"
        if q.get("two_call_enabled"):
            tc = "sufficient" if ga.get("sufficient", True) else f"2nd round (+{q.get('round2_added',0)})"
        st.markdown(
            f"**{i}. {q['query'][:80]}**  \n"
            f'<span class="muted">'
            f'reformulate → {len(q.get("reformulated_queries",[]))} variants · '
            f'merged {q.get("merged_candidates",0)} → deduped {q.get("deduped_candidates",0)} · '
            f'two-call: {tc} · reranked {len(q.get("reranked_chunks",[]))} → '
            f'final {len(q.get("final_chunks",[]))}'
            f'</span>',
            unsafe_allow_html=True,
        )


# ----------------------------------------------------------------------------- raw
with tab_raw:
    st.markdown("### Raw run JSON")
    st.caption(str(run_path))
    st.download_button("Download run.json", data=json.dumps(run, indent=2),
                       file_name=run_path.name, mime="application/json")
    st.json(run, expanded=False)
