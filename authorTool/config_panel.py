"""
The sidebar configuration form.

Two rules from DESIGN.md §4, both of which are about not going stale:

  * **Choices come from the registry, never from a literal.** Drop a new
    retriever into ``pipeline/stage3_retrieval/retrievers/`` and it appears in
    the dropdown with zero edits here.
  * **Widgets come from the YAML tree, by type.** Add a scalar to
    ``config/pipeline.yaml`` and it gets a widget for free, inside a section
    named after its own top-level key.

Only ``hierarchical.levels`` is rendered bespoke, because it is an ordered list
of ``{field, top_n}`` records whose order is semantic (coarse-to-fine).

``render()`` returns the override layer: dotted paths for the keys whose widget
value differs from ``config/pipeline.yaml``. Untouched keys stay out of it, so a
later edit to the YAML still reaches the tool.
"""

from __future__ import annotations

import inspect
import re
from typing import Any, Dict, List, Optional

import streamlit as st

from core.registry import (
    CHUNKERS,
    EMBEDDERS,
    QUERY_STRATEGIES,
    RERANKERS,
    RETRIEVERS,
    discover_plugins,
)

from . import config_resolver as cr

# Which top-level YAML keys are component choices, and which registry lists the
# legal values for each. The values are always read from the registry.
REGISTRY_FIELDS = {
    "embedder": EMBEDDERS,
    "chunker": CHUNKERS,
    "query_strategy": QUERY_STRATEGIES,
    "retriever": RETRIEVERS,
    "reranker": RERANKERS,
}

# Groups that only matter for one retriever. Greyed out, never hidden — hiding
# them teaches the author the knob does not exist; disabling teaches the truth.
CONDITIONAL_GROUPS = {"hybrid": "hybrid", "hierarchical": "hierarchical"}

# Ingestion-time keys: shown read-only, because changing them here would
# describe a knowledge base that is not the one on disk.
READ_ONLY_GROUPS = {"chunking"}

WIDGET_PREFIX = "cfg::"


# =============================================================================
# Enumerating choices
# =============================================================================

@st.cache_data(show_spinner=False)
def registry_options() -> Dict[str, List[str]]:
    """Plugin names per component family, read from the registry at runtime."""
    discover_plugins(include_judges=False)
    return {field: registry.list() for field, registry in REGISTRY_FIELDS.items()}


@st.cache_data(show_spinner=False)
def post_processing_options() -> List[str]:
    """Step names accepted by ``run_post_processing``.

    There is no registry for post-processing steps — they are an if/elif chain
    — so the names are read out of that function's source. A step added there
    shows up here; if the shape ever changes, the fallback keeps the UI usable.
    """
    from pipeline.stage3_retrieval import post_processing

    try:
        source = inspect.getsource(post_processing.run_post_processing)
        names = re.findall(r'step\s*==\s*"([a-z_]+)"', source)
        if names:
            return list(dict.fromkeys(names))
    except (OSError, TypeError):
        pass
    return ["dedupe", "relevance_filter", "mmr"]


# =============================================================================
# Generic widgets
# =============================================================================

def _key(path: str) -> str:
    return WIDGET_PREFIX + path


def _label(path: str) -> str:
    return path.split(".")[-1]


def _render_scalar(path: str, base_value: Any, *, disabled: bool, options: Optional[List[str]] = None) -> Any:
    """One widget, chosen by the YAML value's type. Returns the current value."""
    key = _key(path)
    label = _label(path)

    if options is not None:
        current = base_value if base_value in options else (options[0] if options else "")
        index = options.index(current) if current in options else 0
        return st.selectbox(label, options, index=index, key=key, disabled=disabled)

    if isinstance(base_value, bool):
        return st.checkbox(label, value=base_value, key=key, disabled=disabled)

    if isinstance(base_value, int):
        return int(
            st.number_input(label, value=int(base_value), step=1, min_value=0, key=key, disabled=disabled)
        )

    if isinstance(base_value, float):
        return float(
            st.number_input(
                label, value=float(base_value), step=0.01, format="%.3f", key=key, disabled=disabled
            )
        )

    if base_value is None:
        raw = st.text_input(label, value="", key=key, disabled=disabled, placeholder="null")
        raw = raw.strip()
        if not raw or raw.lower() == "null":
            return None
        return int(raw) if raw.isdigit() else raw

    if isinstance(base_value, list):
        if base_value and all(isinstance(v, dict) for v in base_value):
            return _render_records(path, base_value, disabled=disabled)
        choices = post_processing_options() if path == "post_processing" else [str(v) for v in base_value]
        for value in base_value:
            if str(value) not in choices:
                choices.append(str(value))
        return st.multiselect(label, choices, default=[str(v) for v in base_value], key=key, disabled=disabled)

    return st.text_input(label, value=str(base_value), key=key, disabled=disabled)


def _render_records(path: str, base_value: List[Dict[str, Any]], *, disabled: bool) -> List[Dict[str, Any]]:
    """Ordered list of dicts — today only ``hierarchical.levels``.

    Order is semantic here: it is the coarse-to-fine filtering order, so the
    editor must preserve row order and let rows be added, removed and reordered.
    """
    st.caption(f"{_label(path)} — order is the coarse-to-fine filter order")
    edited = st.data_editor(
        [dict(row) for row in base_value],
        num_rows="dynamic",
        width="stretch",
        key=_key(path),
        disabled=disabled,
    )
    if hasattr(edited, "to_dict"):
        edited = edited.to_dict("records")
    rows: List[Dict[str, Any]] = []
    for row in edited or []:
        field = str(row.get("field", "") or "").strip()
        if not field:
            continue
        try:
            top_n = int(row.get("top_n") or 0)
        except (TypeError, ValueError):
            continue
        rows.append({"field": field, "top_n": top_n})
    return rows


# =============================================================================
# The panel
# =============================================================================

def _inactive_reason(group: str, retriever: Any) -> Optional[str]:
    required = CONDITIONAL_GROUPS.get(group)
    if required and str(retriever) != required:
        return f"inactive: retriever is `{retriever}`"
    return None


def render(base: Dict[str, Any]) -> Dict[str, Any]:
    """Draw the whole sidebar form. Returns the dotted-path override layer."""
    overrides: Dict[str, Any] = {}
    options = registry_options()

    def record(path: str, value: Any) -> None:
        if value != cr.get_path(base, path):
            overrides[path] = value

    # --- Components: the five registry-backed choices ------------------------
    st.sidebar.subheader("Components")
    with st.sidebar:
        for field in REGISTRY_FIELDS:
            if field not in base:
                continue
            record(field, _render_scalar(field, base.get(field), disabled=False, options=options[field]))

    retriever = overrides.get("retriever", base.get("retriever"))

    # --- Everything else, in the YAML's own key order ------------------------
    scalars = [
        k for k, v in base.items()
        if k not in REGISTRY_FIELDS and not isinstance(v, dict)
    ]
    groups = [k for k, v in base.items() if isinstance(v, dict)]

    if scalars:
        with st.sidebar.expander("Generation & post-processing", expanded=True):
            for path in scalars:
                record(path, _render_scalar(path, base[path], disabled=False))

    for group in groups:
        reason = _inactive_reason(group, retriever)
        read_only = group in READ_ONLY_GROUPS
        title = group.replace("_", " ")
        with st.sidebar.expander(title, expanded=False):
            if reason:
                st.caption(reason)
            if read_only:
                st.caption("ingestion-time — set before chunking, read-only here")
            disabled = bool(reason) or read_only
            for path, value in flatten_paths(base[group], group):
                record(path, _render_scalar(path, value, disabled=disabled))

    return overrides


def flatten_paths(node: Dict[str, Any], prefix: str):
    """Yield (dotted path, value) for every leaf under a group, in YAML order."""
    for key, value in node.items():
        path = f"{prefix}.{key}"
        if isinstance(value, dict):
            yield from flatten_paths(value, path)
        else:
            yield path, value


def reset_widgets() -> None:
    """Clear every config widget so the form falls back to pipeline.yaml."""
    for key in [k for k in st.session_state if k.startswith(WIDGET_PREFIX)]:
        del st.session_state[key]
