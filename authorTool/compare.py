"""
Comparison mode — one question, one axis, several values, side by side.

There are no named conditions in this tool, so a comparison is defined the same
way a run is: take the configuration currently in the sidebar and vary exactly
one key of ``config/pipeline.yaml``. That keeps the columns interpretable —
whatever differs between them is the axis, and nothing else.

Two properties worth keeping:

  * **Runs are sequential.** The Gemini embedder is throttled through
    ``embedding_request_delay_seconds``; parallel runs would fight that.
  * **No quality verdict.** No judge scores, no winner marking. Scoring answers
    is ``evaluation/judge/``'s job, and a verdict here would invite choosing a
    configuration by eyeballing a handful of questions.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

from . import config_panel, config_resolver as cr, runner, viewer


def _comparable_paths(base: Dict[str, Any]) -> List[str]:
    """Every scalar key in pipeline.yaml, component choices first."""
    paths = [k for k in config_panel.REGISTRY_FIELDS if k in base]
    for key, value in base.items():
        if key in config_panel.REGISTRY_FIELDS:
            continue
        if isinstance(value, dict):
            paths.extend(p for p, v in config_panel.flatten_paths(value, key) if not isinstance(v, list))
        elif not isinstance(value, list):
            paths.append(key)
    return paths


def _value_picker(path: str, base_value: Any, options: Dict[str, List[str]]) -> List[Any]:
    """Choose the values to sweep, typed like the key itself."""
    if path in options:
        choices = options[path]
        default = [v for v in choices if v == base_value][:1]
        default += [v for v in choices if v != base_value][:1]
        return st.multiselect(f"values for `{path}`", choices, default=default or choices[:2])
    if isinstance(base_value, bool):
        return st.multiselect(f"values for `{path}`", [True, False], default=[True, False])

    raw = st.text_input(
        f"values for `{path}` (comma-separated)",
        value=str(base_value),
        help="Parsed with the same type as the key's value in pipeline.yaml.",
    )
    values: List[Any] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            values.append(int(part) if isinstance(base_value, int) else float(part) if isinstance(base_value, float) else part)
        except ValueError:
            st.warning(f"Skipping unparseable value {part!r}")
    return values


def render(
    base: Dict[str, Any],
    overrides: Dict[str, Any],
    question: str,
    references: Optional[Dict[str, str]] = None,
) -> List[runner.RunResult]:
    """Draw the comparison controls and, on Run, execute the sweep."""
    st.caption(
        "Runs the question under the sidebar configuration, varying one key. "
        "Everything else is held fixed, so the columns differ only on that axis."
    )

    axis_col, values_col = st.columns([0.35, 0.65])
    with axis_col:
        axis = st.selectbox("axis", _comparable_paths(base), key="compare_axis")
    with values_col:
        values = _value_picker(axis, cr.get_path(base, axis), config_panel.registry_options())

    if len(values) > 3:
        st.info(f"{len(values)} values selected — that is {len(values)} full pipeline runs.")

    disabled = not question.strip() or len(values) < 2
    if not st.button(
        f"Run {len(values)} configurations",
        type="primary",
        disabled=disabled,
        key="compare_run",
    ):
        return st.session_state.get("compare_results", [])

    results: List[runner.RunResult] = []
    progress = st.progress(0.0, text="starting")
    for i, value in enumerate(values):
        variant_overrides = dict(overrides)
        variant_overrides[axis] = value
        effective = cr.resolve(base, variant_overrides)
        progress.progress(i / len(values), text=f"{axis} = {value}")
        results.append(
            runner.run_question(
                question, effective, label=f"{axis}={value}", references=references
            )
        )
    progress.empty()
    st.session_state["compare_results"] = results
    return results


def render_results(results: List[runner.RunResult], index: Dict[str, Any], question: str) -> None:
    if not results:
        return

    columns = st.columns(len(results))
    for column, result in zip(columns, results):
        with column:
            st.markdown(f"**{result.label}**")
            st.caption(cr.summarise(result.effective_config))
            if not result.ok:
                st.error(result.error)
                continue
            st.caption(
                f"{result.elapsed_seconds:.1f} s · {result.llm_calls} LLM calls · "
                f"{len(result.chunks)} chunks · `{result.config_hash[:12]}`"
            )
            st.markdown(result.answer or "_(empty answer)_")
            if result.chunks and st.button(
                "Inspect evidence", key=f"cmp_inspect::{result.config_hash}", width="stretch"
            ):
                viewer.open_inspector(result.config_hash, result.chunks, 0, question)
                st.rerun()

    with st.expander("What differs between these runs"):
        rows: List[Tuple[str, ...]] = []
        first = results[0].effective_config
        for path, before, after in cr.diff_paths(first, results[-1].effective_config):
            rows.append((path, str(before), str(after)))
        if rows:
            st.dataframe(
                {"key": [r[0] for r in rows],
                 results[0].label: [r[1] for r in rows],
                 results[-1].label: [r[2] for r in rows]},
                width="stretch",
                hide_index=True,
            )
        else:
            st.caption("No configuration difference recorded — check the axis selection.")
