# Running experiments

This guide explains how to reproduce the retrieval ablations the system is built
for: a clean comparison of **query reformulation operators**, **retrievers**
(including the structure-aware hierarchical one with its sibling/neighbour
expansion), and **single- vs two-call** retrieval — swept across any embedder /
reranker, scored by the LLM judge, and ranked in one leaderboard.

Assumes you can run the base pipeline (keys in `.env`, PDFs ingested). If not,
read `README.md` first.

---

## 1. What is being compared

There is a single `baseline` indexing convention (dense = summary + headers +
subsection; BM25 = subsection text), so the chunker is **not** an axis. The
meaningful independent variables are:

| Axis | Values | Question it answers |
| --- | --- | --- |
| `query_strategy` | `simple`, `decompose`, `diversify`, `abstract`, `hyde` | Which reformulation operator (which failure mode) helps this corpus? |
| `retriever` | `vector`, `bm25`, `hybrid`, `hierarchical` | Does structure-aware retrieval beat flat dense/sparse? |
| `two_call` | `false`, `true` | Does corrective second-round retrieval add recall worth the extra LLM call? |
| `embedder` / `reranker` | any registered | Model-choice effects. |

The four operators map onto the four reformulation operator families
(decomposition / diversification / abstraction / hypothetical expansion), so a
sweep over `query_strategy` is a direct operator-family ablation.

---

## 2. Defining and running the sweep

Edit the `AXES` dict in `scripts/run_experiments.py` (single-element list pins an
axis; multiple values sweep it), or pass `--axes grid.json`.

```python
AXES = {
    "embedder":       ["gemini"],
    "query_strategy": ["simple", "decompose", "diversify", "abstract", "hyde"],
    "retriever":      ["vector", "hybrid", "hierarchical"],
    "reranker":       ["voyage"],
    "two_call":       [False, True],
}
```

```bash
python -m scripts.run_experiments --dry-run     # preview combos + skips
python -m scripts.run_experiments --resume      # skip already-completed combos
python -m scripts.run_experiments --limit 15    # cap queries for a smoke test
python -m scripts.run_experiments --pairwise    # also print pairwise Δ tables
```

`bm25`/`hybrid` combos require the BM25 index to exist — run
`python -m scripts.run_ingestion` first.

---

## 3. Suggested ablation ladders

**Operator effect (retriever fixed):**
```python
"query_strategy": ["simple", "decompose", "diversify", "abstract", "hyde"],
"retriever":      ["hierarchical"],
"two_call":       [False],
```

**Retriever effect (operator fixed):**
```python
"query_strategy": ["decompose"],
"retriever":      ["vector", "bm25", "hybrid", "hierarchical"],
```

**Two-call effect:**
```python
"query_strategy": ["decompose"],
"retriever":      ["hierarchical"],
"two_call":       [False, True],
```

**Hierarchical expansion ablation** — this one is tuned in
`config/pipeline.yaml → hierarchical`, not as a sweep axis. Toggle
`expand_siblings` / `expand_neighbors` and adjust `levels` and the neighbour
thresholds, re-running `run_retrieval`/`run_experiments` between settings.

---

## 4. Outputs

Per combo, under `data/experiments/<label>/`:
- `judge_results.csv` — per-query metric scores
- `config.json` — the combo
- `responses.csv` — query + answer
- `run.json` — the full run trace (open it in `streamlit run app.py`)

Plus a ranked `data/experiments/leaderboard.csv`. Labels encode the axes, e.g.
`gemini__decompose__hierarchical__voyage__tc1` (`tc1` = two-call on).

---

## 5. Reading the metrics

`retrieval_score`, `generation_score`, and `overall_score` are composites of the
judge modules (context precision/sufficiency, faithfulness, correctness,
completeness, relevance, answer relevance), excluding not-evaluated metrics.
Use `--pairwise` for head-to-head deltas with position-bias mitigation. For a
qualitative read, open the combo's `run.json` in the viewer and inspect where
neighbour/sibling expansion or the two-call round changed the final chunks.
