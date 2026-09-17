# `evaluatorTool/`

The **deployed** rating application for the human evaluation. An admin creates evaluator accounts; each evaluator signs in and works through their assigned questions one at a time — system answer on the left, reference answer on the right, with a toggle that reveals the reference chunks and their source PDF pages.

| Path | What it is |
| --- | --- |
| [`DESIGN.md`](DESIGN.md) | The full design: stack, accounts, data model, routes, the rating screen, PDF serving, deployment, build order, and open decisions. |

**Status:** design only. No code has been written yet.

## Three things to know before building

- **`tool/` is not touched.** This is a separate application with its own database, its own `TELCORAG_EVAL_*` environment prefix, and no shared Python modules. `DESIGN.md` §1.
- **It serves frozen traces, not live retrieval.** No Pinecone, no Gemini, no pipeline code in the deployed service — it is a form over a JSON item bank plus a PDF directory. Every evaluator sees byte-identical stimuli, and the automatic judge scores the same frozen outputs.
- **It cannot deploy the way `tool/` does.** `tool/deploy.md` targets Vercel; serving page PDFs from disk needs a **persistent volume**, so this goes on a container host (Render / Railway / Fly / VPS). `DESIGN.md` §11.1.

## Two details that decide whether the data is usable

- **H1 and H2 are N/A on C1**, stored as NULL plus an explicit flag — never as `1`. Coding an undefined item as the lowest score poisons every mean and every reliability coefficient.
- **The condition never reaches the client** — not in HTML, JSON, URLs, or `data-` attributes. Even `item_id` is tokenised, because `Q07-C3` leaks the condition in its own name.

`DESIGN.md` §7.7 flags one deliberate deviation from `paper/guideline.md` §7.6: the reference answer is shown to evaluators. That makes H4 *reference-aided* correctness and can inflate the RQ2 agreement statistic. The recommended mitigation — collapsed by default, reveal logged — turns it from a confound into a measured moderator. Read that section before building the rating screen.

Related: [`humanEvaluation/`](../humanEvaluation/DESIGN.md) (authoritative for the item bank, assignments, and instrument) · [`authorTool/`](../authorTool/DESIGN.md) (shares the page-deck navigation model) · [`paper/guideline.md`](../paper/guideline.md) §7.
