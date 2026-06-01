"""
Judge orchestrator — run the configured judge modules across a set of
queries / responses / chunks / references and produce per-query result rows.

The orchestrator is configurable: pass a list of module names and it will
look them up in the JUDGE_MODULES registry. This makes "run only retrieval
metrics" or "add a new metric" a one-line config change.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.registry import JUDGE_MODULES, discover_plugins

logger = logging.getLogger("JudgeOrchestrator")


# Default module sets — pick one based on what data you have.
RETRIEVAL_MODULES = ["context_relevance", "context_sufficiency"]
GENERATION_MODULES = ["faithfulness", "answer_relevance"]
FULL_MODULES = [
    "context_relevance",
    "context_sufficiency",
    "faithfulness",
    "answer_correctness",
    "answer_relevance",
]


def _safe_avg(values: List[float]) -> float:
    """Average of non-zero values (zero is reserved for 'not evaluated')."""
    valid = [v for v in values if isinstance(v, (int, float)) and v > 0]
    return round(sum(valid) / len(valid), 2) if valid else 0.0


def evaluate_query(
    modules: List[Any],
    query: str,
    response: Optional[str] = None,
    chunks: Optional[List[Dict]] = None,
    reference: Optional[str] = None,
    experiment_tag: str = "default",
) -> Dict[str, Any]:
    """Run every module on a single query and merge their result dicts."""
    row: Dict[str, Any] = {
        "experiment": experiment_tag,
        "query": query,
        "timestamp": datetime.now().isoformat(),
    }
    for module in modules:
        try:
            result = module.evaluate(
                query=query,
                response=response,
                chunks=chunks,
                reference=reference,
            )
            row.update(result)
        except Exception as e:
            logger.error(f"Module '{module.name}' failed for query '{query[:60]}...': {e}")

    # Composite scores
    retrieval_keys = ["ctx_precision", "ctx_sufficiency"]
    generation_keys = ["faithfulness", "correctness", "completeness", "relevance", "answer_relevance"]
    row["retrieval_score"] = _safe_avg([row.get(k, 0) for k in retrieval_keys])
    row["generation_score"] = _safe_avg([row.get(k, 0) for k in generation_keys])
    row["overall_score"] = _safe_avg([row["retrieval_score"], row["generation_score"]])
    return row


def evaluate_batch(
    queries: List[str],
    responses: Optional[List[str]] = None,
    chunks_per_query: Optional[List[List[Dict]]] = None,
    references: Optional[List[Optional[str]]] = None,
    module_names: Optional[List[str]] = None,
    experiment_tag: str = "default",
) -> List[Dict[str, Any]]:
    """
    Evaluate a batch of queries.

    Each list (responses, chunks_per_query, references) must be either None or
    the same length as `queries`. None means "not provided" for that field;
    individual modules will skip themselves if their needed inputs are missing.
    """
    discover_plugins()
    module_names = module_names or FULL_MODULES
    modules = [JUDGE_MODULES.build(name) for name in module_names]
    logger.info(f"Loaded judge modules: {[m.name for m in modules]}")

    n = len(queries)
    responses = responses or [None] * n
    chunks_per_query = chunks_per_query or [None] * n
    references = references or [None] * n

    results = []
    for i in range(n):
        logger.info(f"[{i + 1}/{n}] Evaluating: {queries[i][:80]}...")
        row = evaluate_query(
            modules=modules,
            query=queries[i],
            response=responses[i],
            chunks=chunks_per_query[i],
            reference=references[i],
            experiment_tag=experiment_tag,
        )
        results.append(row)
    return results
