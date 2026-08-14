"""
Experiment runner — sweep pipeline configurations and judge each.

Sweeps the Cartesian product of these axes:

    embedder  x  query_strategy  x  retriever  x  reranker  x  two_call

(The chunker is fixed: there is a single baseline indexing convention.)

For every combination it runs retrieval + generation + LLM judge and saves
results in ``data/experiments/<label>/``:
  - judge_results.csv   — per-query metric scores
  - config.json         — the combo
  - responses.csv       — query + answer
  - run.json            — the FULL run trace (same shape app.py reads), so each
                          experiment is itself viewable in the Streamlit app.
At the end it writes a ranked ``data/experiments/leaderboard.csv``.

----------------------------------------------------------------------------
DEFINING THE SWEEP
----------------------------------------------------------------------------
Edit the AXES dict below (single-element list = pinned axis; multi = swept), or
override from a JSON file with --axes path/to/axes.json. CLI file > AXES below.

    AXES = {
        "embedder":       ["gemini"],
        "query_strategy": ["simple", "decompose", "diversify", "abstract", "hyde"],
        "retriever":      ["vector", "hybrid", "hierarchical"],
        "reranker":       ["voyage"],
        "two_call":       [false, true],
    }

USAGE
    python -m scripts.run_experiments
    python -m scripts.run_experiments --resume
    python -m scripts.run_experiments --axes my.json
    python -m scripts.run_experiments --limit 20
    python -m scripts.run_experiments --pairwise
    python -m scripts.run_experiments --dry-run
"""

import argparse
import csv
import itertools
import json
import logging
import os
from typing import Dict, List, Optional

from config.settings import (
    DATA_DIR,
    QUERIES_FILE,
    REFERENCE_FILE,
    SETTINGS,
    bm25_index_path,
    get_chunker_name,
)
from core.registry import (
    EMBEDDERS,
    QUERY_STRATEGIES,
    RERANKERS,
    RETRIEVERS,
    discover_plugins,
)
from evaluation.judge.orchestrator import FULL_MODULES, evaluate_batch
from evaluation.judge.io import load_reference_csv, save_results
from evaluation.judge.stats import compare_experiments, compute_summary
from pipeline.stage3_retrieval.generator import generate_response
from pipeline.stage3_retrieval.orchestrator import RetrievalPipeline
from pipeline.tracing import RunRecorder
from utils.logging_setup import setup_logging

setup_logging()
logger = logging.getLogger("Experiments")


# =============================================================================
# The sweep — edit these lists.
# =============================================================================
AXES: Dict[str, List] = {
    "embedder":       ["gemini"],
    "query_strategy": ["simple", "decompose", "diversify", "abstract", "hyde"],
    "retriever":      ["vector", "hybrid", "hierarchical"],
    "reranker":       ["voyage"],
    "two_call":       [False],
}

AXIS_ORDER = ["embedder", "query_strategy", "retriever", "reranker", "two_call"]

OUTPUT_DIR = DATA_DIR / "experiments"
BM25_RETRIEVERS = {"bm25", "hybrid"}

LEADERBOARD_METRICS = [
    "overall_score", "retrieval_score", "generation_score",
    "ctx_precision", "ctx_sufficiency", "faithfulness",
    "correctness", "answer_relevance",
]


def _fmt(v) -> str:
    return f"tc{int(bool(v))}" if isinstance(v, bool) else str(v)


def label_for(combo: Dict) -> str:
    return "__".join(_fmt(combo[a]) for a in AXIS_ORDER)


def expand_grid(axes: Dict[str, List]) -> List[Dict]:
    values = [axes[a] for a in AXIS_ORDER]
    return [dict(zip(AXIS_ORDER, picks)) for picks in itertools.product(*values)]


def validate_axes(axes: Dict[str, List]) -> None:
    discover_plugins()
    registries = {
        "embedder": EMBEDDERS,
        "query_strategy": QUERY_STRATEGIES,
        "retriever": RETRIEVERS,
        "reranker": RERANKERS,
    }
    for axis, reg in registries.items():
        available = set(reg.list())
        for name in axes.get(axis, []):
            if name not in available:
                raise SystemExit(f"[{axis}] '{name}' is not registered. Available: {sorted(available)}")


def can_run(combo: Dict) -> Optional[str]:
    if combo["retriever"] in BM25_RETRIEVERS:
        path = bm25_index_path(get_chunker_name())
        if not path.exists():
            return f"BM25 index missing ({path.name}); run ingestion first."
    return None


def run_one(combo: Dict, queries: List[str], refs: Dict[str, str]) -> List[Dict]:
    label = label_for(combo)
    logger.info(f"\n{'=' * 70}\n  EXPERIMENT: {label}\n{'=' * 70}")
    logger.info("  " + ", ".join(f"{a}={combo[a]}" for a in AXIS_ORDER))

    pipeline = RetrievalPipeline(
        embedder_name=combo["embedder"],
        query_strategy=combo["query_strategy"],
        retriever_name=combo["retriever"],
        reranker_name=combo["reranker"],
        two_call=bool(combo["two_call"]),
    )

    retr_cfg = SETTINGS.pipeline["retrieval"]
    recorder = RunRecorder(config=pipeline.config_snapshot(), label=label)
    all_responses, all_chunks = [], []
    for i, q in enumerate(queries):
        logger.info(f"  [{i + 1}/{len(queries)}] {q[:80]}...")
        trace = pipeline.process_query(q, retrieval_top_k=retr_cfg["top_k"], rerank_top_k=retr_cfg["rerank_top_k"])
        trace.answer = generate_response(q, trace.final_chunks)
        trace.reference = refs.get(q.strip())
        recorder.add(trace)
        all_responses.append(trace.answer)
        all_chunks.append(trace.final_chunks)

    matched_refs = [refs.get(q.strip()) for q in queries]
    results = evaluate_batch(
        queries=queries, responses=all_responses, chunks_per_query=all_chunks,
        references=matched_refs, module_names=FULL_MODULES, experiment_tag=label,
    )

    exp_dir = OUTPUT_DIR / label
    exp_dir.mkdir(parents=True, exist_ok=True)
    save_results(results, exp_dir / "judge_results.csv")
    with open(exp_dir / "config.json", "w", encoding="utf-8") as f:
        json.dump(combo, f, indent=2)
    with open(exp_dir / "responses.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["query", "response"])
        for q, r in zip(queries, all_responses):
            writer.writerow([q, r])
    # Full trace (viewable in app.py) instead of a bare chunk dump.
    with open(exp_dir / "run.json", "w", encoding="utf-8") as f:
        json.dump(recorder.to_dict(), f, indent=2, ensure_ascii=False)
    return results


def write_leaderboard(all_results: Dict[str, List[Dict]]) -> None:
    rows = []
    for label, results in all_results.items():
        summary = compute_summary(results, LEADERBOARD_METRICS)
        row = {"experiment": label}
        for m in LEADERBOARD_METRICS:
            row[m] = summary.get(m, {}).get("mean", "")
        row["n_queries"] = len(results)
        rows.append(row)

    rows.sort(key=lambda r: (r.get("overall_score") or 0), reverse=True)
    path = OUTPUT_DIR / "leaderboard.csv"
    fieldnames = ["experiment", "n_queries"] + LEADERBOARD_METRICS
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in fieldnames})

    logger.info(f"\n{'=' * 78}\n  LEADERBOARD (ranked by overall_score) -> {path}\n{'=' * 78}")
    logger.info(f"  {'experiment':<52}{'overall':>9}{'retr':>8}{'gen':>8}")
    for r in rows:
        ov = r.get("overall_score") or 0
        rt = r.get("retrieval_score") or 0
        gn = r.get("generation_score") or 0
        logger.info(f"  {r['experiment']:<52}{ov:>9.2f}{rt:>8.2f}{gn:>8.2f}")
    logger.info(f"{'=' * 78}\n")


def load_queries(path: str, limit: Optional[int]) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        queries = [row[0] for row in reader if row]
    return queries[:limit] if limit else queries


def main():
    parser = argparse.ArgumentParser(description="Sweep pipeline configurations and judge each.")
    parser.add_argument("--axes", default=None, help="JSON file overriding the AXES grid.")
    parser.add_argument("--resume", action="store_true", help="Skip combos already done.")
    parser.add_argument("--limit", type=int, default=None, help="Cap number of queries.")
    parser.add_argument("--pairwise", action="store_true", help="Also print pairwise tables.")
    parser.add_argument("--dry-run", action="store_true", help="Print combos, then exit.")
    args = parser.parse_args()

    axes = dict(AXES)
    if args.axes:
        with open(args.axes, "r", encoding="utf-8") as f:
            axes.update(json.load(f))

    validate_axes(axes)
    combos = expand_grid(axes)
    logger.info(f"Grid: {len(combos)} combination(s) across {[len(axes[a]) for a in AXIS_ORDER]}")

    if args.dry_run:
        for c in combos:
            reason = can_run(c)
            logger.info(f"  {label_for(c)}  [{'SKIP: ' + reason if reason else 'ok'}]")
        return

    if not os.path.exists(QUERIES_FILE):
        logger.error(f"Queries file not found: {QUERIES_FILE}")
        return
    queries = load_queries(QUERIES_FILE, args.limit)
    logger.info(f"Loaded {len(queries)} queries")

    refs = {}
    if os.path.exists(REFERENCE_FILE):
        refs = load_reference_csv(REFERENCE_FILE)
        logger.info(f"Loaded {len(refs)} reference answers")
    else:
        logger.warning(f"No reference file at {REFERENCE_FILE}; answer_correctness skipped.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_results: Dict[str, List[Dict]] = {}
    for combo in combos:
        label = label_for(combo)
        done = OUTPUT_DIR / label / "judge_results.csv"
        if args.resume and done.exists():
            logger.info(f"[resume] skipping completed: {label}")
            from evaluation.judge.io import load_results_csv
            all_results[label] = load_results_csv(done)
            continue
        reason = can_run(combo)
        if reason:
            logger.warning(f"[skip] {label}: {reason}")
            continue
        try:
            all_results[label] = run_one(combo, queries, refs)
        except Exception as e:
            logger.error(f"Experiment '{label}' failed: {e}")
            continue

    if all_results:
        write_leaderboard(all_results)

    if args.pairwise:
        labels = list(all_results.keys())
        logger.info("\n\n=== PAIRWISE COMPARISONS ===")
        for i in range(len(labels)):
            for j in range(i + 1, len(labels)):
                compare_experiments(all_results[labels[i]], all_results[labels[j]], labels[i], labels[j])


if __name__ == "__main__":
    main()
