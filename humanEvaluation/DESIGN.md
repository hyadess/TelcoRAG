# `humanEvaluation/` — design

**Status:** design document, first version.
**Written:** 2026-09-14.
**Scope:** everything needed to run the human evaluation — the 24-question pool, the rule that splits it into two evaluator sets, the frozen item bank, the per-evaluator assignment files, and the analysis scripts that turn returned ratings into the numbers the manuscript reports.

**Authority.** This document is the **single source of truth for the study's allocation design and for the item-bank schema.** [`evaluatorTool/`](../evaluatorTool/DESIGN.md) consumes those artifacts; [`authorTool/`](../authorTool/DESIGN.md) helps author them. Where this document and `paper/guideline.md` §7 differ, **this document wins for allocation** (§3.7 lists every difference and why); the guideline still governs the instrument, ethics, and analysis rationale.

---

## 0. How to read this document

Same marker convention as [`paper/guideline.md`](../paper/guideline.md) §0.

| Marker | Meaning |
| --- | --- |
| **[VERIFIED]** | Checked against this repository's files, or arithmetic recomputed and confirmed. |
| **[TO VERIFY]** | Not confirmed. Confirm before relying on it. |
| **[DECISION]** | A choice the team has to make. A recommendation is given. |
| **[SETTLED]** | A decision the team has already made. Recorded here so it is not relitigated. |

Every count in §3 was recomputed programmatically on 2026-09-14 and is marked **[VERIFIED]**. The arithmetic closes exactly in three independent directions (§3.6); if an implementation produces different totals, the implementation is wrong.

---

## 1. Purpose

Turn a verified question pool into study-grade human ratings, and turn those ratings into defensible statistics.

The folder has two halves, and they run months apart:

- **Before collection — preparation.** Validate the pool, split it into evaluator sets, generate the answers under three conditions, freeze an item bank, and emit one assignment file per evaluator.
- **After collection — analysis.** Ingest the export from `evaluatorTool/`, compute reliability, condition effects, human↔machine agreement, tier moderation, and failure-mode frequencies, then emit the manuscript's tables and figures.

### 1.1 Non-goals

- **No UI.** Evaluators never see this folder. Rating happens in [`evaluatorTool/`](../evaluatorTool/DESIGN.md).
- **No generation logic.** Answers come from `scripts/run_experiments.py`; this folder orchestrates and freezes, it does not re-implement retrieval.
- **Does not touch `tool/`.**

---

## 2. Research questions

From `paper/guideline.md` §7.1, with the change this design makes possible.

| RQ | Question | Status under this design |
| --- | --- | --- |
| RQ1 | How do raters score answer quality across retrieval relevance, groundedness, completeness, correctness, and decision usability? | Answerable |
| RQ2 | To what extent do automated LLM-as-a-judge scores agree with human ratings, per dimension? **This is the paper's contribution.** | Answerable |
| RQ3 | Do pipeline design choices the automatic harness prefers also win under human judgement? | Answerable, bounded — see §7.3 |
| RQ4 | Does rater expertise moderate that agreement? | **Answerable, and better than in the guideline** — see below |
| RQ5 | What failure modes do raters identify that no automatic metric captures? | Answerable |

**RQ4 is the design's biggest gain.** `paper/guideline.md` §7.5.5 had to concede that "with 6 raters split across disjoint sets, any expert / non-expert contrast is confounded with set", and proposed rescuing RQ4 with a 3-person non-expert panel rating only a 6-item anchor block.

Here, **tier is crossed with set**: each set is rated by 3 experts *and* 3 non-experts. Tier is therefore orthogonal to set, and the expert/non-expert contrast runs on **all 24 questions and all 72 items**, not on an anchor block. RQ4 moves from a descriptive footnote to a properly powered secondary analysis — and it is the question this journal is most likely to find interesting.

---

## 3. The allocation design

**[SETTLED]** by the team on 2026-09-14. All counts **[VERIFIED]** by recomputation.

### 3.1 Parameters

| Parameter | Value |
| --- | --- |
| Question pool | **24** |
| Query types | 6 (T1–T6) |
| Sets | **2** — Set A, Set B |
| Questions per set | **15** = 6 shared + 9 unique |
| Shared (intersection) questions | **6** — one from each type |
| Unique questions per set | **9** |
| Evaluators | **12** = 6 experts (E01–E06) + 6 non-experts (N01–N06) |
| Evaluators per set | **6** = 3 experts + 3 non-experts |
| System conditions rated by humans | **3** — C1, C2, C3 |
| Rating tasks per evaluator | **45** = 15 × 3 |
| Total rating tasks | **540** |
| Distinct items | **72** = 24 × 3 |
| Ratings per set-unique item | **6** (3 expert + 3 non-expert) |
| Ratings per shared item | **12** (6 expert + 6 non-expert) |
| Ordinal judgements collected | **2,340** |

### 3.2 Query types

Definitions from `paper/guideline.md` §7.3.2.

| Type | Definition |
| --- | --- |
| **T1** Single-fact lookup | Answer is one value or short phrase in one subsection |
| **T2** Enumerative | Answer is a closed list that must be complete |
| **T3** Numeric / tariff | A fee, rate, or threshold, often from a schedule or table |
| **T4** Procedural / conditional | A process, or an obligation with conditions and exceptions, typically spanning adjacent subsections |
| **T5** Cross-document | Requires combining two or more of the 25 documents |
| **T6** Unanswerable / out-of-scope | The corpus does not answer it — a different jurisdiction, a repealed provision, or a plausible-but-absent topic |

**T6 is not optional.** It is the only stratum that measures whether the system abstains or confabulates, and abstention is the governance question this venue cares about. No automatic metric scores abstention — `answer_relevance`'s own prompt states that "a response that is completely wrong but on-topic can still score 5" **[VERIFIED]** — so it is measured by human item H6 alone.

**T5 does not yet exist.** `paper/guideline.md` §7.3.2 records that the current 28-question file contains no cross-document items **[VERIFIED]**. All 5 T5 questions must be authored, and they are the strongest test of the hierarchical retriever.

### 3.3 Pool composition **[VERIFIED]**

| Type | Shared | Set A unique | Set B unique | **Pool total** |
| --- | --- | --- | --- | --- |
| T1 single-fact | 1 | 1 | 1 | **3** |
| T2 enumerative | 1 | 1 | 1 | **3** |
| T3 numeric / tariff | 1 | 2 | 2 | **5** |
| T4 procedural / conditional | 1 | 2 | 2 | **5** |
| T5 cross-document | 1 | 2 | 2 | **5** |
| T6 unanswerable | 1 | 1 | 1 | **3** |
| **Total** | **6** | **9** | **9** | **24** |

The unique allocation is **1 each from T1, T2, T6 and 2 each from T3, T4, T5** — the team's rule, giving 9 per set. The heavier weighting of T3/T4/T5 is well judged: those are the types where retrieval quality actually varies. T1 is close to a solved lookup, and T6 items rate in about a minute.

### 3.4 What each set contains **[VERIFIED]**

| Type | In each set (shared + unique) |
| --- | --- |
| T1 | 1 + 1 = **2** |
| T2 | 1 + 1 = **2** |
| T3 | 1 + 2 = **3** |
| T4 | 1 + 2 = **3** |
| T5 | 1 + 2 = **3** |
| T6 | 1 + 1 = **2** |
| **Total** | **15** |

Both sets are identically stratified. This matters: `paper/guideline.md` §7.5.3 warns that a random 50/50 cut can hand one set five T1 questions and one T5, confounding question type with rater group and making the per-type breakdown uninterpretable. Splitting **within type** removes that failure mode by construction.

### 3.5 Evaluator assignment

| Set | Experts | Non-experts | Questions | Tasks each |
| --- | --- | --- | --- | --- |
| **A** | E01, E02, E03 | N01, N02, N03 | 6 shared + 9 A-unique = 15 | 45 |
| **B** | E04, E05, E06 | N04, N05, N06 | 6 shared + 9 B-unique = 15 | 45 |

Consequences worth stating explicitly:

- **Every evaluator rates all 3 conditions for every question they receive.** The condition comparison is therefore paired *within rater*, so rater severity cancels exactly. `paper/guideline.md` §7.11.2 identifies this as the single biggest source of recovered sensitivity.
- **Tier is crossed with set**, so RQ4 is unconfounded (§2).
- **The 6 shared questions carry 12 ratings each** and are the cross-set calibration block: they are how you demonstrate that Group A and Group B are measuring the same construct, and therefore that pooling the two sets in the main analysis is legitimate.

### 3.6 The arithmetic closes **[VERIFIED]**

Three independent routes to the same total; all were recomputed on 2026-09-14.

```
Route 1 — per evaluator
    12 evaluators × 15 questions × 3 conditions              = 540 tasks

Route 2 — per item
    set-unique:  18 questions × 3 conditions × 6 ratings     = 324
    shared:       6 questions × 3 conditions × 12 ratings    = 216
                                                    total    = 540

Route 3 — pool integrity
    6 shared + 9 A-unique + 9 B-unique                       =  24 questions
    per-type: 3 + 3 + 5 + 5 + 5 + 3                          =  24
    distinct items: 24 × 3                                   =  72
```

**Ordinal judgements.** H1 and H2 are *not applicable* on C1 (§5.2), so C1 tasks yield 3 ordinal scores and C2/C3 tasks yield 5:

```
per evaluator:  15×3 (C1)  +  15×5 (C2)  +  15×5 (C3)  = 195
total:          195 × 12                               = 2,340
```

**H1/H2 denominator.** Those two dimensions exist on C2 and C3 only, so their item base is **48 of 72 [VERIFIED]**. Report that denominator in the table itself, not in a footnote.

### 3.7 Differences from `paper/guideline.md` §7 — and what each one costs

The guideline's design was 30 questions, 6 expert raters, two sets of 15 with a 3-question swap. The team's design differs in four ways. Each is recorded here with its consequence, because the manuscript has to be able to defend all four.

| # | Guideline §7 | This design | Consequence |
| --- | --- | --- | --- |
| 1 | 30 questions | **24** | Detectable effect worsens from *d* ≈ 0.51 to **≈ 0.57** (§7.3). A real cost, and it must be reported. |
| 2 | 6 expert raters | **6 experts + 6 non-experts, tier crossed with set** | **A clear gain.** RQ4 becomes properly answerable on all 24 questions rather than on a 6-item anchor block. |
| 3 | 3 swapped questions, 6 carrying 6 ratings | **6 shared questions, each carrying 12 ratings** | **A gain.** A larger, better-stratified calibration block — one question per type instead of an arbitrary three. |
| 4 | 3 ratings per item | **6 per set-unique item, 12 per shared item** | **A large gain.** The guideline calls ≥3 ratings/item "non-negotiable" and notes its own design "satisfies it exactly, with no slack". This design has 2× that, and 3 per item *within each tier*. |

**Net assessment.** Three of the four changes strengthen the study. Only the reduction from 30 to 24 questions costs anything, and it buys the rater-power that makes RQ4 and the reliability analysis solid. That is a defensible trade for a paper whose contribution is judge validity (RQ2) rather than system superiority — but §7.3 must be written into the manuscript honestly.

---

## 4. Inputs

### 4.1 The question pool — `pool/questions.csv`

24 rows, authored and verified before anything else runs.

| Column | Meaning |
| --- | --- |
| `question_id` | `Q01`–`Q24`, stable forever |
| `type` | `T1`–`T6` |
| `question` | The question text, exactly as evaluators will see it |
| `answerable` | `true` / `false` (`false` ⇔ `type == T6`) |
| `set` | `shared` \| `A` \| `B` — filled by `02_split_sets.py`, empty when authored |
| `authored_by` | Author's initials |
| `notes` | Free text — ambiguities, why a T6 is unanswerable |

**Authorship rules, from `paper/guideline.md` §7.3.3.** They are cheap to follow and expensive to retrofit:

- Questions must be authored by someone who **did not tune the retrieval configuration** — in this team, the person who did not set `config/pipeline.yaml`.
- Author them **from the documents, not from system outputs**. Never write a question by looking at what the system answered well.
- **Author a surplus.** Aim for ~32 and select 24. The surplus absorbs questions dropped in provenance verification, supplies catch items (§5.5), and replaces any question the pilot shows to be ambiguous.
- The 28 existing questions in `data/good_queries.csv` **[VERIFIED]** are a legitimate starting pool — they were written *before* this design and so are uncontaminated by it. Say that in the paper. But they are not stratified and contain no T5 or T6 items, so expect to keep roughly half.

### 4.2 Gold provenance — `pool/gold_provenance.csv`

One or more rows per answerable question. Schema shared with [`authorTool/`](../authorTool/DESIGN.md) §7.3, which can append rows directly from the chunk inspector.

```
question_id, doc_folder, doc_name, chapter, section, subsection_id, page_numbers, marked_by, marked_at
```

Why this is worth the effort: the fields all exist in chunk metadata already **[VERIFIED]**, so capturing them is nearly free — and it yields a **retrieval ground truth**, enabling classical **recall@k / MRR / nDCG** alongside the LLM-judged `ctx_precision`. Reviewers trust those metrics, and no other part of this project produces them.

T6 questions have no provenance rows by definition. `01_validate_pool.py` asserts exactly that.

**Two people, independently.** `paper/guideline.md` §7.3.3 requires a second verifier and requires the disagreement rate to be reported. `marked_by` makes the second pass an append rather than an overwrite, so the two passes remain comparable.

### 4.3 Reference answers — `pool/reference_answers.csv`

Columns `Question,Answer`, matching `data/reference_answers_template.csv` **[VERIFIED — 2 example rows exist today]**.

Requirements from `paper/guideline.md` §7.3.4:

- Written by a domain expert, quoting or closely paraphrasing the governing subsection.
- **Include conditions, exceptions, units, and currency.** The `answer_correctness` rubric explicitly penalises dropping these **[VERIFIED — `prompts/judge/answer_correctness.j2`]**.
- Independently checked by a second expert; report agreement and how conflicts were resolved.
- **The reference-answer authors must not be the people who wrote the system prompts.** Otherwise `correctness` measures prompt-reference alignment rather than truth.
- **T6 questions still need a reference row**, whose text states that the corpus does not contain the answer and why. Both the judge and — in this study — the evaluator (§5.4) need something to compare against.

**The exact-match trap.** `README.md` records **[VERIFIED]** that reference matching trims surrounding whitespace but otherwise compares the question text **exactly**. A single stray character silently yields `correctness = 0`, which `_safe_avg` in `evaluation/judge/orchestrator.py` then drops as "not evaluated" **[VERIFIED]** — so the metric disappears rather than failing loudly. `01_validate_pool.py` must assert a 24/24 match and **fail the build** on any miss. This is the single cheapest catastrophic-bug prevention in the project.

### 4.4 Condition definitions — `conditions.yaml`

From `paper/guideline.md` §7.4.

| Label | `query_strategy` | `retriever` | `reranker` | `two_call` | Role |
| --- | --- | --- | --- | --- | --- |
| **C1** | — | *skip retrieval* | — | `false` | Generator alone, from parametric knowledge |
| **C2** | `simple` | `vector` | `voyage` | `false` | Flat dense retrieval + reranking. A credible field default, not a strawman |
| **C3** | `decompose` | `hierarchical` | `voyage` | `true` | Reformulation + hierarchical retrieval with sibling/neighbour expansion + corrective second round |

Held constant across all three **[VERIFIED from `config/pipeline.yaml`]**: `embedder: gemini`, `response_model: gemini`, `retrieval.top_k: 30`, `rerank_top_k: 20`, `relevance_threshold: 0.01`, `post_processing: [dedupe, relevance_filter]`, all `hierarchical.*` thresholds.

Three traps, all of which will silently corrupt the study if missed:

1. **The reranker is held constant across C2 and C3 — assert it.** This converts reranking from a confound into a control and removes the strongest objection a reviewer has: *"your gain came from an off-the-shelf reranker, not your retriever."* Note that `config/pipeline.yaml` currently ships `reranker: none` **[VERIFIED]**, so both conditions must set it explicitly. `03_build_item_bank.py` must assert equality rather than trusting the YAML.
2. **C1 needs its own prompt.** `prompts/generation/answer.j2` instruction 5 forces abstention when no context is present **[VERIFIED]**, so C1 run through it abstains on 100% of queries and the grounding comparison inverts. `prompts/generation/answer_no_context.j2` **does not exist yet [VERIFIED]** and must be written per `paper/guideline.md` §7.4.1. The build script must refuse to proceed without it.
3. **Disclose the reranker's input asymmetry.** The reranker *model* is identical in C2 and C3, but in C3 it operates over a larger merged candidate pool by design, because `decompose` fans out into multiple variants and two-call merges a second round before reranking **[VERIFIED — `README.md`]**. Volunteered, this reads as precision; discovered by a reviewer, it reads as a hidden confound.

---

## 5. The item bank

**This schema is authoritative.** `evaluatorTool/` loads exactly this. Changing it means changing both.

### 5.1 Generation

```
1.  python -m scripts.run_experiments   over the 24-question pool,
    with an axes file pinning exactly the C1 / C2 / C3 combinations
        → data/experiments/<label>/run.json      (full trace, per condition)

2.  python humanEvaluation/scripts/03_build_item_bank.py
        → humanEvaluation/build/item_bank.json
        → humanEvaluation/build/item_bank.sha256
```

`run.json` is written by `RunRecorder` **[VERIFIED — `pipeline/tracing.py`]** and per-query holds `query, reformulated_queries, round1_variants, merged_candidates, deduped_candidates, two_call_enabled, gap_analysis, round2_variants, round2_added, reranked_chunks, final_chunks, answer, reference, elapsed_seconds` **[VERIFIED]**. `final_chunks` is exactly what the generator saw, which is what makes H1 and H2 answerable from the item alone.

**Run the automatic judge on the same frozen outputs.** `paper/guideline.md` §7.10 is emphatic: if the judge scores one generation and the humans see another, **RQ2 is meaningless**. The judge run must read the frozen bank, not re-generate.

**[DECISION] Sweep breadth.** The three human conditions must come from the frozen 24-question run. The automatic-only ablations (`paper/guideline.md` §7.4.6 — operator family, retriever, two-call, sibling/neighbour expansion) may be swept over a wider question set for extra statistical density, since they never face a human. **Recommendation:** sweep the full grid over the same 24 first — one dataset, one frozen bank, nothing to reconcile — and widen only if the ablation section reads thin.

### 5.2 Item schema

```json
{
  "bank_version": "1.0",
  "created_at": "2026-09-14T10:00:00Z",
  "pool_sha256": "…",
  "conditions": {
    "C1": { "label": "C1", "config": { … }, "config_sha256": "…", "prompt": "answer_no_context.j2" },
    "C2": { "label": "C2", "config": { … }, "config_sha256": "…", "prompt": "answer.j2" },
    "C3": { "label": "C3", "config": { … }, "config_sha256": "…", "prompt": "answer.j2" }
  },
  "items": [
    {
      "item_id": "Q07-C3",
      "question_id": "Q07",
      "condition": "C3",
      "type": "T4",
      "answerable": true,
      "question": "What are the requirements for lawful interception (LI) for ISP?",
      "answer": "…",
      "reference_answer": "…",
      "chunks": [
        {
          "rank": 1,
          "doc_folder": "ISP",
          "doc_name": "REGULATORY AND LICENSING GUIDELINES FOR INTERNET SERVICE PROVIDER (ISP) IN BANGLADESH",
          "chapter": "…",
          "section": "30. CHANGES IN OWNERSHIP",
          "subsection_id": "30.1",
          "page_numbers": [16],
          "text": "…",
          "score": 0.83
        }
      ],
      "gold_provenance": [
        { "doc_folder": "ISP", "section": "…", "subsection_id": "…", "page_numbers": [16, 17] }
      ],
      "latency_ms": 8412,
      "trace_ref": { "run": "data/experiments/C3/run.json", "query_index": 6 }
    }
  ]
}
```

Field rules that carry weight:

- **`item_id` = `<question_id>-<condition>`.** Stable and human-readable in the export. It is **never sent to the evaluator's browser** — `evaluatorTool/` substitutes an opaque token (§5.3 there), because `Q07-C3` leaks the condition and destroys blinding.
- **`page_numbers` is a list of ints here**, already parsed from the comma-separated metadata string **[VERIFIED — the raw field is `str` for all 6,858 chunks, e.g. `"5, 6"`, and one NFAP chunk spans 57 non-contiguous pages]**. Parse once, at build time, so no consumer re-implements it.
- **`doc_folder` is resolved at build time** from `doc_name` via the 1:1 index described in [`authorTool/DESIGN.md`](../authorTool/DESIGN.md) §2.4a **[VERIFIED: each of the 25 folders carries exactly one distinct `doc_name`]**. `evaluatorTool/` must never do this lookup at request time — it serves PDFs from disk by folder name, and resolution belongs where it can be asserted.
- **C1 items carry `chunks: []`.** The rating UI must render H1 and H2 as **N/A**, never as 1. `paper/guideline.md` §7.4.2 is blunt about why: coding an undefined item as the lowest score "manufactures an enormous artificial condition effect and poisons every mean, every reliability coefficient and every model fit."
- **`reference_answer` is present on every item**, including T6 (§4.3).

### 5.3 Freezing

`05_freeze.py` computes `sha256` over the canonical-JSON bank, writes `item_bank.sha256`, and **commits the hash**. Report it in the paper's data-availability statement.

After freezing, the bank is immutable. If an item must change, cut a new version, re-freeze, and **discard every rating collected against the old hash.** `evaluatorTool/` stores the bank hash on every rating row so a mismatch is detectable rather than silent.

### 5.4 The rating instrument

Full anchors are in `paper/guideline.md` §7.6 and must be reproduced verbatim in `evaluatorTool/`. Summary:

| Item | Construct | Scale | Automatic counterpart | On C1 |
| --- | --- | --- | --- | --- |
| **H1** | Retrieval relevance | 1–5 | `ctx_precision` | **N/A** |
| **H2** | Groundedness / attribution | 1–5 | `faithfulness` | **N/A** |
| **H3** | Completeness | 1–5 | *none by design* | scored |
| **H4** | Correctness | 1–5 | `correctness` | scored |
| **H5** | Decision usability | 1–5 | *none by design* | scored |
| **H6** | Abstention appropriateness | categorical | *none* | scored — **this is the point of C1** |
| **H7** | Failure tags | multi-select, shown when any of H2–H5 ≤ 3 | — | scored |
| **H8** | Free-text comment | required when any of H2–H5 ≤ 3 | — | scored |

H1, H2 and H4 anchors are deliberately copied from `prompts/judge/context_relevance.j2`, `faithfulness.j2` and `answer_correctness.j2` **[VERIFIED — those files exist]**. Do not paraphrase them loosely: identical anchors are the *only* thing that makes the RQ2 agreement analysis interpretable. If the human item and the machine metric measure slightly different constructs, their disagreement is uninterpretable.

H6 values: `correct_abstention` · `over_abstention` · `confabulation` · `not_applicable`.

**The confabulation rate on the T6 stratum will be one of the most quoted numbers in the paper.** With 3 T6 questions × 3 conditions it is a *descriptive* figure with a wide Wilson interval — report it that way and do not test it across conditions (§7.3).

### 5.5 Catch items

`paper/guideline.md` §7.7 requires ~5% attention checks. At 45 tasks that is **2 per evaluator**.

- Built from surplus pool questions (§4.1), never from the 24.
- Two kinds: an answer to a *different* question, and an answer containing an obviously fabricated fee.
- Flag rule, **pre-specified before collection**: an evaluator who scores a catch item ≥ 4 on H4 is flagged; two flags means exclusion.
- Catch items are excluded from every analysis. Report how many evaluators were flagged and excluded.
- They occupy fixed positions in the assignment file (§6.2) so all evaluators meet them at comparable fatigue levels.

---

## 6. Assignment

### 6.1 Ordering rules

From `paper/guideline.md` §7.5.7 and §7.7:

- **The three answers to one question must never be adjacent**, and ideally fall in different sessions. An evaluator who sees all three at once compares them implicitly, which destroys the independence of the absolute ratings — and RQ2 depends on those being independent.
- Order is **randomised per evaluator** from a **seed recorded in the study log**, so the exact sequence is reproducible.
- **Three sessions.** At ~4 min/task, 45 tasks is ~3 hours; T6 items rate in ~1 min, so the realistic figure is nearer 2.5 hours. **[TO VERIFY]** The 4 min/task figure comes from `paper/guideline.md` §7.5.6, where it is flagged as an estimate, not a measurement. Measure it in the pilot and re-size.
- **Session 1 is the shared block: all 6 shared questions × 3 conditions = 18 tasks.** The remaining 27 split **14 / 13**. Running the cross-set block first makes it double as the calibration step (§10 step 10), so the calibration you already owe costs nothing extra — and it means every evaluator's first session is on byte-identical stimuli, which is exactly what a calibration discussion needs.
- Evaluators **never** see condition labels, model names, or retriever names.

### 6.2 Assignment file

One JSON per evaluator, at `build/assignments/<evaluator_code>.json`:

```json
{
  "evaluator_code": "E01",
  "tier": "expert",
  "set": "A",
  "bank_sha256": "…",
  "seed": 20260914,
  "generated_at": "2026-09-14T10:00:00Z",
  "phase1": [
    { "position": 1,  "item_id": "Q03-C2", "session": 1, "catch": false },
    { "position": 2,  "item_id": "Q11-C1", "session": 1, "catch": false },
    { "position": 3,  "item_id": "__catch_01", "session": 1, "catch": true }
  ],
  "phase2": [
    { "position": 1, "question_id": "Q03", "left": "C2", "right": "C3" },
    { "position": 2, "question_id": "Q11", "left": "C3", "right": "C2" }
  ]
}
```

`04_assign_evaluators.py` must **assert** before writing: 45 non-catch entries; every entry's `item_id` present in the bank; all 3 conditions present for each of the 15 questions; no two entries sharing a `question_id` within a distance of 2 positions; exactly 2 catch entries.

### 6.3 Phase 2 — pairwise

`paper/guideline.md` §7.2 pre-specifies the contrast as **C2 vs C3**, fixed in advance rather than chosen from Phase 1 results — picking the Phase 1 winner would be a post-hoc selection a reviewer would rightly flag.

- Run **after** Phase 1 is complete.
- **Left/right assignment randomised per item and recorded** — this is the human analogue of the position-swap already implemented in `evaluation/judge/modules/pairwise.py`, which runs each comparison twice with positions swapped and flags `pairwise_position_bias` on disagreement **[VERIFIED]**.
- Response: A / B / "no meaningful difference", plus one line of reasoning.
- **Default: all 15 of the evaluator's questions** (~25 min). If time is short, cut to the 6 shared questions — never cut Phase 2 entirely. A forced choice takes roughly half the time of an absolute rating and discriminates smaller differences, so at this sample size it buys more condition-comparison sensitivity per minute than anything else in the design.

This pairing is what lets you compute **human–machine preference agreement** and check whether the machine's position bias coincides with human disagreement — a clean, publishable methodological result that costs very little rater time.

---

## 7. Analysis

### 7.1 Input

`evaluatorTool/` exports tidy long format — **one row per (evaluator, item, criterion)** — as required by `paper/guideline.md` §7.9(f):

```
evaluator_code, tier, set, item_id, question_id, type, answerable,
condition, criterion, value, is_na, comment, failure_tags,
unsupported_quote, reference_revealed, duration_ms, submitted_at, bank_sha256
```

`06_ingest_ratings.py` validates it: bank hash matches; no unknown evaluator or item; H1/H2 rows on C1 carry `is_na = true` and no numeric value; catch items separated out; per-evaluator completion counts equal 45.

### 7.2 Reliability — `07_reliability.py`

From `paper/guideline.md` §7.12 step 2.

- **Krippendorff's α (ordinal metric)** as the primary statistic — it handles the unbalanced structure (6 ratings on most items, 12 on shared items) that Cohen's κ cannot. Report it **per set**, **pooled**, **within tier**, and **across sets on the shared block**. The last is the evidence that pooling the two sets is legitimate.
- **Gwet's AC2** alongside it, because α is unstable under high prevalence and regulatory answers will skew high on some criteria. Reporting both pre-empts a reviewer objection.
- **ICC(2,k)** for the reliability of the *averaged* rating, since the analysis uses averages.
- Bootstrap 95% CIs, ≥ 2,000 resamples, for all three.
- Per criterion. Expect H1 and H4 to agree better than H3 and H5; that pattern is itself reportable.
- **Do not report raw percent agreement alone.**

**A structural strength worth stating in the manuscript:** with 3 raters per (set × tier) cell, α is computable **within each tier separately** — 3 expert ratings and 3 non-expert ratings on every set-unique item, 6 and 6 on shared items. Most elicitation studies of this size cannot separate the two.

**And the matching fragility:** 3 is exactly the minimum. **One dropout breaks within-tier α for that set.** Recruit 8 experts and 8 non-experts and treat the surplus as insurance. `paper/guideline.md` §7.11.5 is explicit that if recruitment falls short you must **not** compensate by cutting ratings per item — merge the sets and run a smaller, fully-overlapped study instead. RQ2 is the paper; the condition ranking is not.

### 7.3 Condition effects — `08_condition_effects.py`

- **Primary: cumulative link mixed model.** `ordinal::clmm(score ~ condition + tier + (1|question) + (1|evaluator))` in R, fitted to the individual judgements — not to 24 question means. Ratings are ordinal and crossed-nested; treating 1–5 as interval and running ANOVA will draw a methods reviewer's fire.
- **Secondary / robustness:** Friedman across conditions on per-question mean ratings, then Wilcoxon signed-rank pairwise with **Holm** correction. Report both; if they agree, one sentence.
- Report effect sizes (odds ratios from the CLMM; rank-biserial *r* for Wilcoxon) with CIs, not only *p*-values.

**Pre-specify a single primary comparison: C2 vs C3 on H4 (correctness).** Everything else is secondary or exploratory. Correcting one primary test instead of six is a substantial power gain for free.

**Resolution limit.** At 24 distinct questions, a naive paired comparison at α = 0.05 two-sided and 80% power detects **d ≈ 0.57** — about 0.57 points on a 1–5 scale with SD ≈ 1.0. Computed as `(z₀.₉₇₅ + z₀.₈₀)/√n = 2.802/√24 = 0.572`, the **same normal approximation used in `paper/guideline.md` §7.11.2** (that table's n = 30 → 0.51, n = 45 → 0.42, n = 60 → 0.36 all reproduce exactly, confirming the method). **[TO VERIFY]** The exact non-central *t* value is slightly higher; after the pilot supplies a variance estimate, replace this approximation with a CLMM simulation and report it in supplementary material. That converts "our sample is small" into evidence of care.

Report ≈ 0.57 as an **upper bound on the resolution limit, not as the analysis.** Three features recover real sensitivity beyond it: the CLMM fits all 2,340 judgements; the design is fully paired within rater; and each per-question value averages 6 or 12 raters — double the guideline's design.

**Plan for a null on C2 vs C3 now.** The reranker is held constant, so the baseline is strong and the remaining delta is small. A null there is survivable: the contribution is judge validity, not system superiority, and C1 vs C2 is close to guaranteed to be large. But it must be **reported as bounded** — *"no evidence of a difference larger than 0.5 points on a 5-point scale (95% CI −0.21 to 0.38)"* — never as "no significant difference". An underpowered study that states its own resolution limit is publishable; one that reports a null as a finding is not.

**What this design cannot do**, to be stated in the manuscript before a reviewer states it:

- Detect condition differences below ~0.5 points.
- Test confabulation rates across conditions — 3 T6 questions. Report descriptively with a Wilson interval.
- Support per-type significance tests — 24 questions over 6 types is 3–5 per cell. **Descriptive and explicitly exploratory only.**
- Attribute C3's gain to one component. C3 bundles reformulation, hierarchical retrieval and two-call correction; attribution comes from the automatic sweep.
- Generalise to a population of practitioners. 12 raters is an elicitation panel — treat rater as a random effect, do not report population estimates.

### 7.4 Human↔machine agreement — `09_human_machine_agreement.py`

**This is the core analysis; RQ2 is the paper.** For each paired dimension (H1↔`ctx_precision`, H2↔`faithfulness`, H4↔`correctness`):

- **Quadratic-weighted Cohen's κ** between the machine score and the *median* human score.
- **Spearman ρ** and **Kendall τ-b** at item level.
- **Mean signed difference** (machine − human) with 95% CI — the bias estimate, and the number that answers *"is the LLM judge too generous?"*
- **Bland–Altman plot**: difference against mean, showing whether bias varies with quality level.
- **Confusion matrix** (machine 1–5 × human 1–5) per dimension, as a heatmap.
- **Disagreement case analysis**: the top ~20 items by |machine − human|, analysed qualitatively. This is what makes the section readable.

Two filters that must be applied explicitly and reported:

1. **Drop C1 before any H1/H2 comparison** (48 items, not 72). Do not rely on `_safe_avg` to do it — it drops zeros, so C1's retrieval composite arrives *empty* rather than *low*, which is easy to misread as a data-collection failure.
2. **Drop machine rows where the metric is 0.** Zero means "not evaluated", not a low score **[VERIFIED — `_safe_avg` in `evaluation/judge/orchestrator.py` and `stats.compute_summary` both skip zeros]**. Report how many items were dropped and why (`NO_REFERENCE`, `JUDGE_ERROR`). Silently dropping them is a reproducibility hole, and this convention is unusual enough that the manuscript must state it outright.

The Bland–Altman plot does double duty: `paper/guideline.md` §7.4.3 notes that the study validates the judge at three widely-separated quality levels and then applies it to fine-grained contrasts between adjacent configurations — an extrapolation. If judge bias varies with quality level, that plot will show it. Report it as evidence for or against the extrapolation, not as a generic calibration check.

### 7.5 Tier moderation (RQ4) — `10_tier_moderation.py`

- Add `tier` and `condition × tier` to the CLMM.
- Compute every agreement statistic from §7.4 **within tier**, and test the difference.
- **State the hypothesis up front:** non-experts will agree with the LLM judge more closely than experts do, because both are susceptible to fluent-but-wrong text. If it holds, it is a strong, quotable finding about automated evaluation and about who is qualified to supervise these systems — and it is the result most likely to interest this venue.
- Report the shared-block analysis separately: on those 6 questions, 6 experts and 6 non-experts rated **byte-identical stimuli**, which is the cleanest possible tier contrast.

**[DECISION] Aided vs unaided correctness.** `paper/guideline.md` §7.6 recommends unaided H4 for experts and reference-aided for non-experts, and notes the difference is itself an RQ4 finding. **The `evaluatorTool/` design shows the reference answer to every evaluator** (see [`evaluatorTool/DESIGN.md`](../evaluatorTool/DESIGN.md) §7), which makes H4 **reference-aided for both tiers**. That is a legitimate choice, but it must be (a) stated in the Method as reference-aided correctness, and (b) analysed using the `reference_revealed` telemetry the tool records. Do not describe H4 as unaided anywhere in the manuscript.

### 7.6 Failure modes (RQ5) — `11_failure_modes.py`

- H7 tag frequencies by condition and by type.
- Thematic analysis of H8 comments and debrief transcripts: two coders, open coding on a 20% subsample, codebook agreed, then full coding, with Cohen's κ on the double-coded portion reported.
- **Cross-reference against the judge's own free-text fields**, all already stored **[VERIFIED]**: `hallucinated_claims` and `factual_errors` are declared on the response models in `core/schemas.py`; `ctx_noise_analysis` and `ctx_missing_info` are emitted as output keys by `evaluation/judge/modules/context_relevance.py` and `context_sufficiency.py`, which also emit `ctx_relevance_reasoning` and `ctx_sufficiency_reasoning`. Reporting *what the judge said it found* next to *what the expert found* is a strong figure and costs nothing extra to produce.

  Note the sentinel these modules write on failure: `"JUDGE_ERROR"` in the free-text field alongside a score of `0` **[VERIFIED]**. That is the other source of the zeros §7.4 filters out, distinct from `"NO_REFERENCE"`, and the two should be counted separately when reporting dropped items.

### 7.7 Outputs — `12_report.py`

Writes to `analysis/`:

| Output | Feeds |
| --- | --- |
| `table_descriptives.csv` | Condition × criterion × tier: mean, SD, median, full 1–5 distribution |
| `table_reliability.csv` | α, AC2, ICC(2,k) with bootstrap CIs, per criterion, per set, per tier |
| `table_condition_effects.csv` | CLMM odds ratios + CIs; Friedman/Wilcoxon robustness |
| `table_agreement.csv` | κ_w, ρ, τ-b, mean signed difference + CI, per dimension, with denominators |
| `fig_bland_altman_*.png` | Judge calibration per dimension |
| `fig_confusion_*.png` | Machine × human heatmaps |
| `table_failure_tags.csv` | H7 frequencies by condition and type |
| `table_pairwise.csv` | Human vs machine preference agreement, cross-tabbed against `pairwise_position_bias` |
| `disagreement_cases.md` | Top 20 |machine − human| items for qualitative write-up |

**Show distributions, not just means.** Ordinal data with ceiling effects looks very different in a histogram than in a mean, and regulatory answers will have ceiling effects.

---

## 8. Folder layout

```
humanEvaluation/
├── README.md
├── DESIGN.md                       # this file
├── conditions.yaml                 # C1 / C2 / C3 definitions (§4.4)
├── pool/
│   ├── questions.csv               # 24 questions (§4.1)
│   ├── gold_provenance.csv         # (§4.2)
│   ├── reference_answers.csv       # (§4.3)
│   └── catch_items.csv             # surplus questions + fabricated answers (§5.5)
├── protocol/
│   ├── instrument.md               # H1–H8 verbatim anchors, copied from guideline §7.6
│   ├── consent_form.md             # (§9)
│   ├── evaluator_brief.md          # onboarding script; must not reveal conditions
│   ├── screening_questionnaire.md  # expert/non-expert tier assignment
│   └── debrief_guide.md            # semi-structured interview questions
├── scripts/
│   ├── 01_validate_pool.py         # stratification, provenance, reference exact-match
│   ├── 02_split_sets.py            # shared 6 + 9/9 within-type split (§3)
│   ├── 03_build_item_bank.py       # traces -> item_bank.json (§5)
│   ├── 04_assign_evaluators.py     # 12 assignment files (§6)
│   ├── 05_freeze.py                # hash and lock
│   ├── 06_ingest_ratings.py        # validate the export (§7.1)
│   ├── 07_reliability.py
│   ├── 08_condition_effects.py
│   ├── 09_human_machine_agreement.py
│   ├── 10_tier_moderation.py
│   ├── 11_failure_modes.py
│   ├── 12_report.py
│   └── clmm.R                      # the one step that needs R (§8.1)
├── build/                          # generated
│   ├── item_bank.json
│   ├── item_bank.sha256
│   └── assignments/E01.json … N06.json
└── analysis/                       # generated
```

Numbered scripts because the order is a dependency chain, and a reader should be able to see it without opening anything.

### 8.1 Tooling

**[DECISION]** Python does everything except the cumulative link mixed model. `pandas`, `numpy`, `matplotlib`, `seaborn` are already in `requirements.txt` **[VERIFIED]**; add `krippendorff` for α and `pingouin` (or a direct implementation) for ICC.

**R is required for `ordinal::clmm`** and for Gwet's AC2 via `irrCAC`. There is no mature CLMM implementation in the Python scientific stack — `statsmodels` has no ordinal mixed model. **Recommendation:** keep `clmm.R` as a single, small, clearly-documented R script invoked from `08_condition_effects.py`, rather than substituting a model that is easier to fit but wrong for ordinal crossed-random-effects data. The alternative — a Bayesian ordinal model in PyMC or `bambi` — is defensible but adds far more to review and explain than one R script does.

---

## 9. Ethics

Non-negotiable for an Elsevier journal with human participants. Full detail in `paper/guideline.md` §7.13; the operational requirements:

- **Ethics approval before a single rating is collected.** Retroactive approval is usually impossible and some journals will not publish without it. The protocol number goes in the manuscript.
- **Written informed consent** covering purpose, time commitment, voluntariness and right to withdraw, what is recorded, how stored, how long, who sees it, and how results are published.
- **Anonymity.** Evaluators identified only by code. **Never publish role + employer + tenure together** — Bangladesh's telecom regulatory community is small enough that the combination identifies a person. Report evaluator characteristics in aggregate only.
- **Compensation** — decide, disclose, apply consistently.
- **Conflicts** — disclose any professional relationship between an evaluator and the authors or BTRC.
- **Data availability**: release the question pool, gold provenance, reference answers, the frozen item bank, the anonymised rating table, and these scripts under a DOI. **Do not redistribute the source BTRC PDFs** unless their licence permits — link to them with retrieval dates. Releasing the ratings is a real strength for a paper whose claim is about evaluation methodology.
- **Pre-registration [DECISION]** — register design, instrument, sample size and analysis plan on OSF or AsPredicted before collection. It costs an afternoon and is worth several rounds of argument against reviewers who suspect post-hoc metric selection.

---

## 10. Sequence

| # | Step | Blocks |
| --- | --- | --- |
| 1 | Ethics approval | **Everything** |
| 2 | Author ~32 questions; select 24; verify provenance twice (§4.1, §4.2) | 3 |
| 3 | Write 24 reference answers; two experts; assert 24/24 exact match (§4.3) | 5 |
| 4 | Write `prompts/generation/answer_no_context.j2` (§4.4 trap 2) | 5 |
| 5 | `01_validate_pool.py`, `02_split_sets.py` | 6 |
| 6 | Run the sweep; `03_build_item_bank.py`; run the judge on the frozen bank | 7 |
| 7 | `04_assign_evaluators.py`, `05_freeze.py`; commit the hash | 8 |
| 8 | Recruit and screen; 8 + 8 for attrition insurance (§7.2) | 9 |
| 9 | Pilot: 2 evaluators × 20 tasks. **Measure time-per-task** and re-size (§6.1). Pilot data reported but excluded | 10 |
| 10 | Calibration: all 12 rate the shared block first; compute agreement; hold **one** discussion; revise anchors **once**; freeze; report that you did this | 11 |
| 11 | Main collection: 3 sessions of 18 / 14 / 13 tasks (§6.1) | 12 |
| 12 | Phase 2 pairwise (§6.3) | 13 |
| 13 | Debrief: 15–20 min semi-structured with 3–5 experts. **These quotes carry the Discussion section** | 14 |
| 14 | Export; `06`–`12` | Manuscript |

Steps 1 and 4 are the ones most likely to be underestimated. Step 1 has an external clock the team does not control. Step 4 is a single prompt file whose absence silently inverts the study's headline result.
