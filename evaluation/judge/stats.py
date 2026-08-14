"""Statistics helpers — mean/std/min/max + experiment comparison."""

import math
from typing import Any, Dict, List, Optional


def compute_summary(
    results: List[Dict[str, Any]],
    numeric_keys: Optional[List[str]] = None,
) -> Dict[str, Dict[str, float]]:
    """
    Compute mean, std, min, max for numeric columns. Skips 0 values (treated
    as 'not evaluated') so they don't pull the average down.
    """
    if not results:
        return {}

    if numeric_keys is None:
        numeric_keys = [
            k for k, v in results[0].items()
            if isinstance(v, (int, float)) and k != "timestamp"
        ]

    summary = {}
    for key in numeric_keys:
        values = [
            r[key] for r in results
            if isinstance(r.get(key), (int, float)) and r[key] > 0
        ]
        if not values:
            continue
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        summary[key] = {
            "mean": round(mean, 3),
            "std": round(math.sqrt(variance), 3),
            "min": min(values),
            "max": max(values),
            "n": len(values),
        }
    return summary


def compare_experiments(
    results_a: List[Dict],
    results_b: List[Dict],
    label_a: str = "A",
    label_b: str = "B",
):
    """Side-by-side comparison printed to stdout."""
    keys = [
        "ctx_precision", "ctx_sufficiency", "faithfulness",
        "correctness", "answer_relevance",
        "retrieval_score", "generation_score", "overall_score",
    ]
    sa = compute_summary(results_a, keys)
    sb = compute_summary(results_b, keys)

    print(f"\n{'=' * 78}")
    print(f"  COMPARISON: [{label_a}] vs [{label_b}]")
    print(f"{'=' * 78}")
    print(f"  {'Metric':<22} {'[' + label_a + ']':>14} {'[' + label_b + ']':>14} {'Δ':>10} {'Winner':>10}")
    print(f"  {'-' * 72}")
    for k in keys:
        a_val = sa.get(k, {}).get("mean", 0)
        b_val = sb.get(k, {}).get("mean", 0)
        delta = b_val - a_val
        if abs(delta) < 0.05 or not (a_val and b_val):
            winner = "tie"
        else:
            winner = label_b if delta > 0 else label_a
        a_str = f"{a_val:.2f}" if a_val else "N/A"
        b_str = f"{b_val:.2f}" if b_val else "N/A"
        d_str = f"{delta:+.2f}" if a_val and b_val else "N/A"
        print(f"  {k:<22} {a_str:>14} {b_str:>14} {d_str:>10} {winner:>10}")
    print(f"{'=' * 78}\n")
