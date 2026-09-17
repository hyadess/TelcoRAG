"""
Running one question under one effective config.

Thin wrapper over the same functions ``scripts/run_retrieval.py`` calls —
``RetrievalPipeline`` and ``generate_response`` — so the workbench and the CLI
cannot drift apart. What this module adds:

  * the pipeline is built inside ``config_resolver.applied()`` and cached by the
    effective-config hash, so switching a knob rebuilds and switching back
    reuses (rebuilding re-opens the Pinecone index on every rerun otherwise);
  * an honest LLM-call count, by counting actual calls rather than guessing
    from the trace shape;
  * failures captured per run instead of raised, so a rate limit shows up next
    to the configuration that produced it.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

from config.settings import RUNS_DIR
from pipeline.stage3_retrieval.generator import generate_response
from pipeline.stage3_retrieval.orchestrator import RetrievalPipeline
from pipeline.tracing import QueryTrace, RunRecorder

from . import config_resolver as cr

logger = logging.getLogger("authorTool.runner")


# =============================================================================
# LLM call counting
# =============================================================================

@contextmanager
def _count_llm_calls(counter: Dict[str, int]):
    """Count real Gemini calls made during the block.

    The pipeline modules do ``from clients.gemini import general_response``, so
    each holds its own binding; patching ``clients.gemini`` alone would miss
    them. Every module-level binding is wrapped instead, and restored after.
    """
    import clients.gemini as gemini

    originals: List[tuple] = []

    def make_wrapper(fn):
        def wrapper(*args, **kwargs):
            counter["llm_calls"] = counter.get("llm_calls", 0) + 1
            return fn(*args, **kwargs)
        return wrapper

    for name in ("general_response", "structured_response"):
        target = getattr(gemini, name)
        for module in list(sys.modules.values()):
            if module is None:
                continue
            try:
                bound = getattr(module, name, None)
            except Exception:
                continue
            if bound is target:
                originals.append((module, name, target))
                setattr(module, name, make_wrapper(target))
    try:
        yield counter
    finally:
        for module, name, original in originals:
            setattr(module, name, original)


# =============================================================================
# Pipeline construction, cached by config hash
# =============================================================================

@st.cache_resource(show_spinner=False, max_entries=4)
def _build_pipeline(cfg_hash: str, _effective: Dict[str, Any]) -> RetrievalPipeline:
    """One pipeline per effective config. ``cfg_hash`` is the cache key; the
    config itself is passed unhashed (leading underscore) because it is a dict."""
    with cr.applied(_effective):
        return RetrievalPipeline()


def get_pipeline(effective: Dict[str, Any]) -> RetrievalPipeline:
    return _build_pipeline(cr.config_hash(effective), effective)


# =============================================================================
# Running a question
# =============================================================================

@dataclass
class RunResult:
    """One question, one config — everything the UI needs to render it."""

    question: str
    label: str
    effective_config: Dict[str, Any]
    config_hash: str
    trace: Optional[QueryTrace] = None
    llm_calls: int = 0
    elapsed_seconds: float = 0.0
    error: Optional[str] = None
    extras: Dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.error is None and self.trace is not None

    @property
    def chunks(self) -> List[Dict[str, Any]]:
        return list(self.trace.final_chunks) if self.trace else []

    @property
    def answer(self) -> str:
        return self.trace.answer if self.trace else ""


def run_question(
    question: str,
    effective: Dict[str, Any],
    *,
    label: str = "run",
    references: Optional[Dict[str, str]] = None,
    generate: bool = True,
) -> RunResult:
    """Retrieve, generate, and return a fully populated result.

    Errors are captured rather than raised: a missing API key or a rate limit
    should show up in the UI as a message next to the config that produced it,
    not as a stack trace that loses the run.
    """
    result = RunResult(
        question=question,
        label=label,
        effective_config=effective,
        config_hash=cr.config_hash(effective),
    )
    references = references or {}
    counter: Dict[str, int] = {"llm_calls": 0}
    t0 = time.time()

    try:
        with cr.applied(effective), _count_llm_calls(counter):
            pipeline = get_pipeline(effective)
            retrieval = effective.get("retrieval", {}) or {}
            trace = pipeline.process_query(
                question,
                retrieval_top_k=int(retrieval.get("top_k", 30)),
                rerank_top_k=int(retrieval.get("rerank_top_k", 20)),
            )
            if generate:
                trace.answer = generate_response(question, trace.final_chunks)
            trace.reference = references.get(question.strip())
            trace.elapsed_seconds = trace.elapsed_seconds or (time.time() - t0)
            result.trace = trace
    except Exception as exc:  # noqa: BLE001 — surfaced in the UI, not swallowed
        logger.exception("Run failed")
        result.error = f"{type(exc).__name__}: {exc}"

    result.llm_calls = counter.get("llm_calls", 0)
    result.elapsed_seconds = time.time() - t0
    _note_session_cost(result)
    return result


def _note_session_cost(result: RunResult) -> None:
    """Tally runs, LLM calls and elapsed time for the session counter.

    Counted here rather than at the call sites so a run is counted exactly
    once, whether it came from the Ask tab or a comparison sweep.
    """
    counters = st.session_state.setdefault(
        "counters", {"runs": 0, "llm_calls": 0, "seconds": 0.0}
    )
    counters["runs"] += 1
    counters["llm_calls"] += result.llm_calls
    counters["seconds"] += result.elapsed_seconds


# =============================================================================
# Persisting a session
# =============================================================================

def trace_payload(result: RunResult) -> Dict[str, Any]:
    """A trace dict plus the author-tool fields that identify its config."""
    payload = result.trace.to_dict() if result.trace else {"query": result.question}
    payload["config_hash"] = result.config_hash
    payload["label"] = result.label
    payload["llm_calls"] = result.llm_calls
    return payload


def save_results(results: List[RunResult], label: str = "author") -> Optional[Path]:
    """Write results as one run JSON in the same schema as the experiment scripts.

    Reusing ``RunRecorder`` is deliberate: author sessions land in the schema
    ``scripts/run_experiments.py`` writes, so the root ``app.py`` viewer reads
    them and analysis can join them.
    """
    results = [r for r in results if r.ok]
    if not results:
        return None

    config: Dict[str, Any] = {
        "source": "authorTool",
        "config_hash": results[0].config_hash,
        "effective_config": results[0].effective_config,
    }
    if len({r.config_hash for r in results}) > 1:
        config["config_hash"] = "multiple"
        config["configs"] = {
            r.label: {"config_hash": r.config_hash, "effective_config": r.effective_config}
            for r in results
        }

    recorder = RunRecorder(config=config, label=label, runs_dir=RUNS_DIR)
    for result in results:
        recorder.add(result.trace)
    path = recorder.save()

    # RunRecorder serialises QueryTrace only; re-write with the author fields.
    data = json.loads(path.read_text(encoding="utf-8"))
    data["queries"] = [trace_payload(r) for r in results]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
