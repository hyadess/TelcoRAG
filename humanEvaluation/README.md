# `humanEvaluation/`

Everything for running the human evaluation: the 24-question pool, the rule that splits it into two evaluator sets, the frozen item bank, the 12 per-evaluator assignment files, and the analysis scripts that turn returned ratings into the manuscript's tables and figures.

| Path | What it is |
| --- | --- |
| [`DESIGN.md`](DESIGN.md) | The full design: allocation, inputs, the item-bank schema, assignment rules, the analysis plan, folder layout, ethics, and the build sequence. |

**Status:** design only. No pool, scripts, or data yet.

**This folder is the single source of truth for the study's allocation design and the item-bank schema.** [`evaluatorTool/`](../evaluatorTool/DESIGN.md) consumes both.

## The design in one table

| | |
| --- | --- |
| Question pool | **24** (T1–T6) |
| Sets | **2** × 15 questions = 6 shared + 9 unique |
| Shared questions | **6** — one per type |
| Evaluators | **12** = 6 experts + 6 non-experts, **3 + 3 per set** |
| Conditions | **3** — C1 no-retrieval, C2 standard RAG, C3 structure-aware |
| Tasks per evaluator | **45** · Total **540** · Distinct items **72** |
| Ratings per item | **6** (set-unique) · **12** (shared) — and 3 per item *within each tier* |

Because tier is **crossed with** set, the expert/non-expert contrast (RQ4) is unconfounded and runs on all 24 questions — a real improvement on `paper/guideline.md` §7.5.5, which had to concede RQ4 was not answerable. `DESIGN.md` §3.7 lists every difference from the guideline and what each one costs.

Start with `DESIGN.md` §3 (allocation) and §5 (the item bank). Then §7.3, which states honestly what this sample size can and cannot detect.

Related: [`paper/guideline.md`](../paper/guideline.md) §7 · [`authorTool/`](../authorTool/DESIGN.md) · [`evaluatorTool/`](../evaluatorTool/DESIGN.md).
