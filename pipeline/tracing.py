"""
Run/query tracing — captures every intermediate step of a retrieval run so it
can be saved as a single self-contained JSON and inspected later (including in
the Streamlit viewer).

Two objects:

  * ``QueryTrace``  — everything that happened for one query: the reformulated
    queries, per-variant retrieval results (round 1 and, in two-call mode,
    round 2), the merged/deduped candidate counts, the gap analysis, the
    reranked chunks, the post-processed final chunks, and the final answer.

  * ``RunRecorder`` — the whole run: a config snapshot plus the list of query
    traces, written to ``data/runs/run_<timestamp>.json``.

Everything is plain dicts/lists so it serialises cleanly and the viewer needs no
knowledge of the pipeline internals.
"""

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.settings import RUNS_DIR

logger = logging.getLogger("Tracing")


@dataclass
class QueryTrace:
    query: str
    reformulated_queries: List[str] = field(default_factory=list)
    # Round 1: one entry per query variant -> the chunks it retrieved.
    round1_variants: List[Dict[str, Any]] = field(default_factory=list)
    merged_candidates: int = 0
    deduped_candidates: int = 0
    # Two-call / corrective retrieval (only populated when enabled).
    two_call_enabled: bool = False
    gap_analysis: Optional[Dict[str, Any]] = None
    round2_variants: List[Dict[str, Any]] = field(default_factory=list)
    round2_added: int = 0
    # After rerank / post-processing.
    reranked_chunks: List[Dict[str, Any]] = field(default_factory=list)
    final_chunks: List[Dict[str, Any]] = field(default_factory=list)
    # Filled in by the calling script after generation.
    answer: str = ""
    reference: Optional[str] = None
    elapsed_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "reformulated_queries": self.reformulated_queries,
            "round1_variants": self.round1_variants,
            "merged_candidates": self.merged_candidates,
            "deduped_candidates": self.deduped_candidates,
            "two_call_enabled": self.two_call_enabled,
            "gap_analysis": self.gap_analysis,
            "round2_variants": self.round2_variants,
            "round2_added": self.round2_added,
            "reranked_chunks": self.reranked_chunks,
            "final_chunks": self.final_chunks,
            "answer": self.answer,
            "reference": self.reference,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
        }


class RunRecorder:
    """Accumulates query traces for one run and writes a single JSON artifact."""

    def __init__(self, config: Dict[str, Any], label: Optional[str] = None, runs_dir: Path = RUNS_DIR):
        self.config = config
        self.label = label or "run"
        self.runs_dir = Path(runs_dir)
        self.created_at = datetime.now()
        self.run_id = f"{self.created_at:%Y%m%d_%H%M%S}__{self.label}"
        self.traces: List[QueryTrace] = []
        self._t0 = time.time()

    def add(self, trace: QueryTrace) -> None:
        self.traces.append(trace)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "label": self.label,
            "created_at": self.created_at.isoformat(timespec="seconds"),
            "elapsed_seconds": round(time.time() - self._t0, 3),
            "config": self.config,
            "n_queries": len(self.traces),
            "queries": [t.to_dict() for t in self.traces],
        }

    def save(self) -> Path:
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        path = self.runs_dir / f"{self.run_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        logger.info(f"Run trace saved to {path}")
        return path
