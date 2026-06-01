"""
Stage 3 orchestrator — the end-to-end retrieval pipeline.

Single-call flow per query:
  1. Reformulate via the chosen operator (1..N query variants).
  2. Run the chosen retriever for each variant; collect candidates.
  3. Pre-rerank dedupe (keep best score per unique subsection_text).
  4. Rerank the merged candidates against the MAIN query.
  5. Apply configured post-processing (dedupe / filter / MMR).

Two-call (corrective) flow, enabled via pipeline.yaml -> two_call.enabled:
  1-3. Run round 1 exactly as above to get a merged candidate set.
  4.   Ask the gap-analysis LLM whether those candidates cover the MAIN query.
  5.   If not, run a second retrieval round on the LLM's follow-up queries
       (themselves reformulated, so multi-query operators fan out again), merge
       the new candidates in, then rerank everything against the MAIN query.

Every step is recorded into a ``QueryTrace`` so a run can be saved as one JSON
and inspected later. ``process_query`` returns that trace (use ``.final_chunks``
for generation); ``retrieve`` is a thin wrapper returning just the chunks.

Construct one ``RetrievalPipeline`` and reuse it across many queries.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from config.settings import SETTINGS, chunk_namespace, get_chunker_name
from core.registry import (
    EMBEDDERS,
    QUERY_STRATEGIES,
    RERANKERS,
    RETRIEVERS,
    discover_plugins,
)

from .post_processing import run_post_processing
from .refinement import analyze_gap
from ..tracing import QueryTrace

logger = logging.getLogger("RetrievalPipeline")


class RetrievalPipeline:
    """End-to-end retrieval orchestrator. Reads strategy from pipeline.yaml."""

    def __init__(
        self,
        embedder_name: Optional[str] = None,
        query_strategy: Optional[str] = None,
        retriever_name: Optional[str] = None,
        reranker_name: Optional[str] = None,
        chunker_name: Optional[str] = None,
        two_call: Optional[bool] = None,
    ):
        discover_plugins()
        cfg = SETTINGS.pipeline

        self.embedder_name = embedder_name or cfg["embedder"]
        self.query_strategy_name = query_strategy or cfg["query_strategy"]
        self.retriever_name = retriever_name or cfg["retriever"]
        self.reranker_name = reranker_name or cfg["reranker"]
        self.chunker_name = (chunker_name or get_chunker_name()).strip().lower()

        # Two-call config
        tc = cfg.get("two_call", {}) or {}
        self.two_call_enabled = tc.get("enabled", False) if two_call is None else bool(two_call)
        self.two_call_max_rounds = int(tc.get("max_rounds", 1))  # extra rounds after round 1

        # Build embedder once, pointed at this chunker's namespace.
        self.embedder = EMBEDDERS.build(self.embedder_name)
        self.embedder.set_namespace(chunk_namespace(self.chunker_name))
        self.embedder.initialize_db()

        self.retriever = RETRIEVERS.build(self.retriever_name, chunker=self.chunker_name)
        if hasattr(self.retriever, "set_embedder"):
            self.retriever.set_embedder(self.embedder)

        self.query_strategy = QUERY_STRATEGIES.build(self.query_strategy_name)
        self.reranker = RERANKERS.build(self.reranker_name)

        self.post_steps: List[str] = cfg.get("post_processing", [])
        retrieval_cfg = cfg.get("retrieval", {})
        self.relevance_threshold = retrieval_cfg.get("relevance_threshold", 0.01)
        self.mmr_lambda = retrieval_cfg.get("mmr_lambda", 0.7)

        logger.info(
            f"Pipeline ready: embedder={self.embedder_name}, chunker={self.chunker_name}, "
            f"query={self.query_strategy_name}, retriever={self.retriever_name}, "
            f"reranker={self.reranker_name}, two_call={self.two_call_enabled}, post={self.post_steps}"
        )

    # ---------- config snapshot (for the run recorder) ----------
    def config_snapshot(self) -> Dict[str, Any]:
        return {
            "embedder": self.embedder_name,
            "chunker": self.chunker_name,
            "query_strategy": self.query_strategy_name,
            "retriever": self.retriever_name,
            "reranker": self.reranker_name,
            "two_call_enabled": self.two_call_enabled,
            "two_call_max_rounds": self.two_call_max_rounds,
            "post_processing": list(self.post_steps),
            "retrieval": dict(SETTINGS.pipeline.get("retrieval", {})),
            "hierarchical": dict(SETTINGS.pipeline.get("hierarchical", {})),
        }

    # ---------- one round: reformulate -> retrieve -> record ----------
    def _retrieve_round(
        self,
        query: str,
        retrieval_top_k: int,
        record: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Reformulate `query`, retrieve each variant, append per-variant records.

        Returns the accumulated candidate chunks for this round.
        """
        reformulated = self.query_strategy.reformulate(query)
        candidates: List[Dict[str, Any]] = []
        for q in reformulated.queries:
            results = self.retriever.search(q, top_k=retrieval_top_k)
            record.append({"variant_query": q, "n_results": len(results), "results": results})
            candidates.extend(results)
        return candidates

    # ---------- main API ----------
    def process_query(
        self,
        query: str,
        retrieval_top_k: int = 30,
        rerank_top_k: int = 20,
    ) -> QueryTrace:
        t0 = time.time()
        trace = QueryTrace(query=query, two_call_enabled=self.two_call_enabled)

        # --- Round 1 ---
        round1_records: List[Dict[str, Any]] = []
        candidates = self._retrieve_round(query, retrieval_top_k, round1_records)
        trace.round1_variants = round1_records
        trace.reformulated_queries = [r["variant_query"] for r in round1_records]
        trace.merged_candidates = len(candidates)

        candidates = _dedupe_by_text_keep_best(candidates)
        trace.deduped_candidates = len(candidates)
        logger.info(
            f"Round 1: {trace.merged_candidates} candidates -> {len(candidates)} unique"
        )

        # --- Two-call: gap analysis + round 2 (against the MAIN query) ---
        if self.two_call_enabled and candidates:
            rounds_done = 0
            current = candidates
            while rounds_done < self.two_call_max_rounds:
                gap = analyze_gap(query, current)
                trace.gap_analysis = gap.model_dump()
                logger.info(
                    f"Gap analysis: sufficient={gap.sufficient} "
                    f"followups={gap.followup_queries}"
                )
                if gap.sufficient or not gap.followup_queries:
                    break

                before = len(current)
                seen = {c.get("subsection_text", "") for c in current}
                for fq in gap.followup_queries:
                    r2_records: List[Dict[str, Any]] = []
                    new_cands = self._retrieve_round(fq, retrieval_top_k, r2_records)
                    trace.round2_variants.extend(r2_records)
                    for c in new_cands:
                        txt = c.get("subsection_text", "")
                        if txt and txt not in seen:
                            seen.add(txt)
                            current.append(c)
                current = _dedupe_by_text_keep_best(current)
                trace.round2_added = len(current) - before
                rounds_done += 1
            candidates = current

        if not candidates:
            trace.elapsed_seconds = time.time() - t0
            return trace

        # --- Rerank against the MAIN query ---
        reranked = self.reranker.rerank(query, candidates, top_k=rerank_top_k)
        trace.reranked_chunks = reranked
        logger.info(f"Reranker produced {len(reranked)} chunks")

        # --- Post-processing ---
        final = run_post_processing(
            reranked,
            steps=self.post_steps,
            relevance_threshold=self.relevance_threshold,
            mmr_lambda=self.mmr_lambda,
        )
        trace.final_chunks = final
        trace.elapsed_seconds = time.time() - t0
        return trace

    def retrieve(self, query: str, retrieval_top_k: int = 30, rerank_top_k: int = 20) -> List[Dict[str, Any]]:
        """Convenience wrapper: return only the final chunks."""
        return self.process_query(query, retrieval_top_k, rerank_top_k).final_chunks


# =============================================================================
# Internal: pre-rerank dedup
# =============================================================================

def _dedupe_by_text_keep_best(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    best: Dict[str, Dict[str, Any]] = {}
    for c in chunks:
        text = c.get("subsection_text", "")
        if not text:
            continue
        score = c.get("score", c.get("relevance_score", 0))
        existing = best.get(text)
        existing_score = existing and existing.get("score", existing.get("relevance_score", 0))
        if existing is None or score > existing_score:
            best[text] = c
    return list(best.values())
