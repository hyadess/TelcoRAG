"""CSV / JSON loading and saving for judge results."""

import csv
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

from .stats import compute_summary

logger = logging.getLogger("JudgeIO")


def load_query_response_csv(path: Union[str, Path]) -> Tuple[List[str], List[str]]:
    """Two columns expected: query, response (with header)."""
    queries, responses = [], []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        for row in reader:
            if len(row) >= 2:
                queries.append(row[0])
                responses.append(row[1])
    return queries, responses


def load_reference_csv(path: Union[str, Path]) -> Dict[str, str]:
    """Two columns: Question, Answer (with header)."""
    refs = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if len(row) >= 2:
                refs[row[0].strip()] = row[1].strip()
    return refs


def load_chunks_json(path: Union[str, Path]) -> List[Dict]:
    """Single-query chunks dump (a flat list)."""
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_results_csv(path: Union[str, Path]) -> List[Dict]:
    """Reload a previously saved judge results CSV. Numeric columns get coerced."""
    out = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for k, v in list(row.items()):
                # Try to parse numeric values back
                try:
                    row[k] = float(v)
                except (ValueError, TypeError):
                    pass
            out.append(dict(row))
    return out


def save_results(results: List[Dict[str, Any]], path: Union[str, Path]):
    """Write CSV + print a summary."""
    if not results:
        logger.warning("No results to save.")
        return

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Use the union of all keys so missing columns get blanks instead of crashing
    fieldnames = list({k for r in results for k in r.keys()})
    fieldnames.sort()

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow({k: row.get(k, "") for k in fieldnames})

    summary = compute_summary(results)
    logger.info(f"Saved {len(results)} rows to {path}")
    logger.info(f"{'=' * 60}")
    logger.info(f"  SUMMARY ({len(results)} queries)")
    logger.info(f"{'=' * 60}")
    for metric, stats in summary.items():
        logger.info(
            f"  {metric:<24}: {stats['mean']:.2f} ± {stats['std']:.2f}  "
            f"(min={stats['min']}, max={stats['max']}, n={stats['n']})"
        )
    logger.info(f"{'=' * 60}")
