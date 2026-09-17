# Publishing TelcoRAG in *Telematics and Informatics* — a working guideline

**Status:** working document, first version.
**Written:** 2026-09-13.
**Scope:** how to turn the code in this repository into a manuscript that *Telematics and Informatics* (Elsevier, ISSN 0736-5853) will send out for review, and how to design the human evaluation that the manuscript needs.

---

## 0. How to read this document, and what is verified

This document separates three kinds of statements. Please keep the distinction when you act on it.

| Marker | Meaning |
| --- | --- |
| **[VERIFIED]** | Checked directly against this repository's files, or against a machine-readable bibliographic source (Crossref API for ISSN 0736-5853, OpenAlex, Semantic Scholar) on 2026-09-13. |
| **[SOURCED]** | Taken from a public web page that I read on 2026-09-13. The source is named. Journal metrics and policies change; re-check before submitting. |
| **[TO VERIFY]** | I could not confirm this. `sciencedirect.com` returns HTTP 403 to automated requests, so the official *Guide for Authors* page could not be read directly. Open it in a browser and confirm. |
| **[DECISION]** | A choice the team has to make. I give a recommendation, but it is your call. |

Nothing in this document invents a number, a paper, or a result. Where a fact was unavailable, it says so rather than filling the gap.

**Files referenced** are given relative to the repository root (`/Users/sayemshahad/Desktop/research/TelcoRAG`).

---

## 1. The target journal, verified

### 1.1 Identity

| Field | Value | Source |
| --- | --- | --- |
| Title | *Telematics and Informatics* | **[VERIFIED]** Crossref journal record for ISSN 0736-5853 |
| Publisher | Elsevier | **[VERIFIED]** Crossref |
| ISSN | 0736-5853 | **[VERIFIED]** Crossref |
| Subtitle / self-description | "An Interdisciplinary Journal on the Social Impacts of New Technologies" | **[SOURCED]** Elsevier journal store page |
| Total DOIs registered | 2,844 (current 229, backfile 2,615) | **[VERIFIED]** Crossref |
| Output by year | 2023: 93, 2024: 73, 2025: 85, 2026: 71 (as registered by 2026-09-13) | **[VERIFIED]** Crossref `dois-by-issued-year` |
| Editor-in-Chief | T. Grubesic, PhD (University of California, Riverside) | **[SOURCED]** Elsevier editorial board page; **[TO VERIFY]** current as of submission |
| Impact Factor history | 2025: 9.9; 2024: 8.3; 2023: 7.6; 2022: 8.5; 2021: 9.14 | **[SOURCED]** bioxbio.com |
| CiteScore | 13.9 | **[SOURCED]** researcher.life journal page |
| SJR quartile | Q1 | **[SOURCED]** researcher.life |
| APC (gold OA option) | USD 4,420 excl. tax | **[SOURCED]** search result; **[TO VERIFY]** — this matters for budget, confirm on the Elsevier journal page |
| Review model | Double anonymised; editor triage first, then normally ≥2 reviewers | **[SOURCED]** journal guide-for-authors summary |
| Issues per year | 8 volumes, 8 issues | **[SOURCED]** Elsevier store page |

Note that it is a **hybrid** journal: several 2026 articles carry a CC-BY licence (**[VERIFIED]** via OpenAlex `best_oa_location.license` for e.g. `10.1016/j.tele.2026.102447`), while most are closed. Publishing closed-access costs nothing.

### 1.2 Aims and scope, as published

**[SOURCED]** — Elsevier journal store page, quoted:

> "Telematics and Informatics is an interdisciplinary journal publishing innovative theoretical and methodological research on the social, economic, geographic, political, and cultural impacts of digital technologies."

Application areas listed include: smart cities, sensors and information fusion, digital society and digital platforms, IoT, cyber-physical technologies, privacy, knowledge management, distributed work, emergency response and hazards, mobile and wireless communications, health informatics, psychosocial effects of social media, ICT for sustainable development, blockchain, e-commerce, and **e-government**.

Stated audience: "information scientists, data scientists, computer scientists, social informaticists, geographic information scientists, urban and regional planners, policy analysts, regional scientists, disaster scientists, and network scientists."

### 1.3 Article types and length

**[SOURCED]** — journal guide-for-authors summary:

| Type | Word limit |
| --- | --- |
| Research paper (favoured) | 8,000 words |
| Systematic review / meta-analysis | 10,000 words |
| Research note (new ideas, theoretical perspectives, methodological approaches) | 4,000 words |

**[DECISION]** Target the **8,000-word research paper**. A research note is tempting because the work is "methodological", but 4,000 words cannot carry a system description *and* a human evaluation *and* an agreement analysis.

**[TO VERIFY]** on the official Guide for Authors, before writing:
- whether the word limit includes or excludes references, tables, and the abstract;
- whether a **structured abstract** is required or only permitted;
- abstract word cap (Elsevier journals commonly 150–250);
- number of keywords;
- whether **Highlights** are mandatory (Elsevier standard: 3–5 bullets, ≤85 characters each including spaces);
- reference style (Elsevier journals in this space usually use an APA-like author–date style, but confirm);
- required declarations: Declaration of Competing Interest, CRediT author statement, Declaration of Generative AI in the writing process, Data Availability statement, ethics/informed-consent statement.

Official page: `https://www.sciencedirect.com/journal/telematics-and-informatics/publish/guide-for-authors`

---

## 2. What this journal actually publishes — and the hard truth about fit

This is the most important section. Read it before writing a single sentence of the manuscript.

### 2.1 Evidence

I pulled the 40 most recently published articles in ISSN 0736-5853 from Crossref **[VERIFIED]**. A representative sample of titles:

- Media multiplexity, face-to-face communication, and romantic relationship quality: A daily diary study (`10.1016/j.tele.2026.102451`)
- Beyond accuracy: assessing the information quality of large language models for systematic literature reviews (`10.1016/j.tele.2026.102447`)
- Psychological needs and AI delegation across four social domains — A cross-cultural analysis of 35 nations (`10.1016/j.tele.2026.102438`)
- Can open government data promote urban–rural public service equalization? Evidence from China (`10.1016/j.tele.2026.102437`)
- When AI lies to me: understanding user recognition, attribution, and response to AI hallucinations in human-AI interaction (`10.1016/j.tele.2026.102434`)
- Evaluating the socioeconomic effects of a digital public policy: the case of FTTH deployments in Uruguay (`10.1016/j.tele.2026.102420`)
- Digital public management reform: assessing the impact of e-government initiatives on administrative transparency (`10.1016/j.tele.2026.102418`)
- A search changer: auditing Google's AI overviews interface in political and news search (`10.1016/j.tele.2026.102417`)
- Automating the identification of High-Value Datasets in open government data portals: A US municipalities case study (`10.1016/j.tele.2026.102415`)
- Unequal AI readiness: institutional and digital disparities in e-government across the European Union (`10.1016/j.tele.2026.102400`)

I then searched the journal's whole 2,844-record back catalogue **[VERIFIED]** for the terms this project is built on:

| Query against ISSN 0736-5853 | Result |
| --- | --- |
| "retrieval augmented generation" | **No matching article.** Top hits were about *augmented reality* and a 1997 paper on knowledge-based multimedia retrieval. |
| "question answering" | Effectively nothing relevant (one 2018 link-prediction paper on health forums). |
| "large language model" | A handful, all social-science framed: clickstream segmentation (`102359`), on-device LLM business models (`102395`), LLM information quality for SLRs (`102447`), anthropomorphism and user aggression (`102194`). |
| "chatbot" | Several, all adoption/perception studies: government chatbots in China (`102380`), chatbot digital competence scale (`102392`), forgiveness of chatbot errors (`102189`), AI psychotherapy chatbot profile pictures (`102052`). |
| "Bangladesh" | Exactly two articles ever: telemedicine (`10.1016/j.tele.2011.02.002`) and Union Digital Centre telecentres (`10.1016/j.tele.2018.05.006`). |

### 2.2 The conclusion you need to accept

**A paper whose contribution is "we built a modular RAG pipeline with a hierarchical retriever and four query-reformulation operators, and here is the ablation leaderboard" will be desk-rejected by this journal.** Not because the work is weak, but because the contribution type does not exist in this venue. There is not a single RAG systems paper in 2,844 records.

What *does* get published, and is close to your work, is one of two things:

1. **Audit / evaluation studies of an AI information system**, where the finding is about *quality, failure modes, and consequences* — e.g. `102447` (LLM information quality for systematic reviews, with human-coded ground truth and qualitative error analysis) and `102417` (systematic audit of Google AI Overviews).
2. **Build-and-assess studies in a public-sector information context**, where an artefact is constructed but the framing is governance and public value — e.g. `102415` (automating High-Value Dataset identification in open government data portals).

Your work can be written as either. It should be written as a blend led by (1).

---

## 3. Three candidate framings, and the recommendation

### Framing A — "Evaluation study": *Can automated LLM evaluation substitute for expert judgement in regulatory question answering?* **(RECOMMENDED)**

- **Unit of contribution:** an empirical finding about evaluation validity, not a system.
- **The system is the apparatus.** TelcoRAG becomes the instrument that generates the answers being judged; the pipeline configurations become the experimental conditions.
- **The headline result:** where LLM-as-a-judge scores agree with, and where they systematically diverge from, the judgement of telecom regulatory practitioners on Bangladeshi licensing and spectrum documents — plus a qualitative account of *why*.
- **Why it fits:** it is structurally the same paper as `102447` ("Beyond accuracy…"), which this journal published in 2026. That paper used 1,325 articles, human-coded ground truth, two LLMs, quantitative agreement plus qualitative error analysis, and concluded that LLMs "can reliably assist, but not replace, human judgment." You would be doing the same for a different, higher-stakes task.
- **Why it suits your situation:** you already have the automatic evaluation. The human evaluation you are about to run becomes the *centre* of the paper rather than a bolt-on validation. Nothing is wasted.
- **Risk:** you must genuinely run a rigorous human study. The design in §7 is what that costs.

### Framing B — "Public-value artefact": *Reducing the regulatory information gap in Bangladesh's telecom sector*

- **Unit of contribution:** a deployable system plus evidence that it changes information access for a specific stakeholder group (licensees, applicants, consultants, regulator staff).
- **The framing:** compliance burden and information asymmetry in a developing-country telecom regime; 25 BTRC guideline documents that are legally binding but practically unsearchable; who currently pays the cost of that (small ISPs, new applicants) and who does not (large operators with in-house legal teams).
- **Why it fits:** structurally like `102415` and the e-government cluster (`102418`, `102400`, `102380`).
- **Risk:** needs real user evidence — deployment data, practitioner interviews, or an adoption study. The feedback tool in `tool/` supports this but has not collected data in this repo yet.

### Framing C — "Adoption study": TAM/UTAUT survey of practitioners using the tool

- Statistically the *best* fit to this journal's taste (it publishes many of these).
- But it discards the engineering contribution almost entirely and requires a large N of real users. **Not recommended** given where the project stands.

### Recommendation

**Lead with A, absorb B as the framing of the Introduction and Discussion.**

The paper is: *an expert-grounded evaluation of retrieval-augmented generation for telecom regulatory question answering in Bangladesh, which tests whether automated LLM evaluation can stand in for domain-expert judgement in a high-stakes public-information setting.*

That single sentence carries a system, a dataset, a human study, an agreement analysis, and a governance implication — all of which you either have or can get.

---

## 4. The contribution claims — write these down before writing the paper

A T&I reviewer will ask "what do we learn that we did not know?" Answer with four falsifiable claims. Do not add a fifth.

**C1 (empirical, evaluation validity).** On regulatory question answering over Bangladeshi telecom licensing documents, LLM-as-a-judge scores and domain-expert scores agree on *X* dimensions and diverge on *Y*; the divergence is largest for [dimension], where the automatic judge is systematically [more/less] generous by [effect size]. → Requires §7.

**C2 (empirical, system).** Structure-aware retrieval over hierarchically parsed regulatory documents changes answer quality relative to flat dense retrieval by [effect], as judged by experts and by the automatic harness. → Requires running the sweep in `scripts/run_experiments.py`.

**C3 (diagnostic, qualitative).** The failure modes of RAG on regulatory text are [taxonomy], derived from expert free-text comments and trace inspection — e.g. conflating fee schedules across licence categories, dropping conditions/exceptions, answering confidently when the corpus does not contain the answer. → Requires §7.12 thematic analysis.

**C4 (governance implication).** What C1–C3 imply for deploying generative AI in regulatory information services in low- and middle-income regulatory environments — the "assist, not replace" boundary, drawn concretely rather than as a platitude.

C4 is what makes this a *Telematics and Informatics* paper rather than an IR paper. Give it real space (see the word budget, §10).

---

## 5. What the repository already gives you — verified inventory

Everything in this section was read from the files. Use these numbers in the paper; do not re-estimate them.

### 5.1 Corpus **[VERIFIED]**

| Property | Value | Where checked |
| --- | --- | --- |
| Source documents | 25 PDFs | `resources/*.pdf` |
| Documents ingested | 25 | `knowledge_base/documents/` |
| Parsed page markdowns | 1,170 | `knowledge_base/documents/*/markdowns/page_*.md` |
| Indexed chunks (baseline chunker) | **6,858** | sum over `structured_output_chunks__baseline.json` |
| Mean chunk length | 768 characters | computed over all 6,858 |
| Median chunk length | 590 characters | " |
| Max chunk length | 2,778 characters | " |
| Chunk metadata fields | `doc_name, document_summary, chapter, section, subsection_id, subsection_text, full_subsection_text, bm25_text, context_summary, page_numbers, prev_ids, next_ids, seq, chunk_index, total_chunks, is_split` | `metadata` keys |

Per-document chunk counts (top of the distribution): NFAP 1,374; CMS 533; BWA 501; 4G_cellular 395; IGW 371; ICX 356; MNPS 346; Satelite 336; Submarine_cable 304; VSAT 303. Smallest: IIG_operator 3; Fee 14; RFC 27; infra_sharing 33.

The document set spans ISP, IIG, ICX, IGW, NTTN, IPTSP, BWA, VSAT, VTS, TVAS, BPO, MNPS, CMS, NIX, submarine cable, satellite, infrastructure sharing, 4G/LTE licensing, the National Frequency Allocation Plan, radio-frequency charges, the national telecom policy and the national ICT policy. **That breadth is a genuine asset — say so.** It is not a toy corpus; it is close to the complete operative licensing framework of one national regulator.

**[TO VERIFY]** For the paper you must state, per document: official title, issuing authority (BTRC / Ministry of Posts, Telecommunications and Information Technology), publication or amendment date, and the retrieval date of your snapshot. Regulatory corpora are versioned; a reviewer will ask. Build this as Appendix A.

### 5.2 Pipeline **[VERIFIED]**

Three stages, plugin-registered, selected by YAML (`config/pipeline.yaml`):

- **Stage 1, extraction** (`pipeline/stage1_extraction/`): PDF → page markdown (LlamaParse) → LLM page analysis into typed items (`chapter_header`, `section_header`, `new_subsection`, `continuation`, see `core/schemas.py`) → structured subsections.
- **Stage 2, indexing** (`pipeline/stage2_indexing/`): one `baseline` chunker; dense vector embeds *document summary + chapter/section headers + subsection text*, BM25 indexes *subsection text only*; `sequencing.py` records reading-order neighbour IDs; embedders available: `openai`, `gemini`, `cohere`, `voyage`, `perplexity`.
- **Stage 3, retrieval** (`pipeline/stage3_retrieval/`):
  - query operators: `simple` (control), `decompose`, `diversify`, `abstract`, `hyde` — each mapped in `README.md` to one retrieval failure mode;
  - retrievers: `vector`, `bm25`, `hybrid` (RRF), `hierarchical`;
  - the `hierarchical` retriever does multi-level coarse-to-fine filtering (`doc_name` top-3 → `chapter` top-4 → `section` top-5, configurable), then **sibling expansion** (metadata-filtered query for missed subsections) and **neighbour expansion** (splice in reading-order prev/next chunks for medium-relevance hits, thresholds `neighbor_high 0.65 / neighbor_low 0.30 / neighbor_moderate 0.40`, `max_hops 2`);
  - rerankers: `voyage`, `cohere`, `rrf`, `llm`, `none`;
  - **two-call corrective retrieval**: after round 1 an LLM gap analysis (`prompts/query/gap_analysis.j2`, schema `GapAnalysis`) decides sufficiency and emits follow-up queries for round 2.

**The neighbour/sibling expansion is the most novel engineering element**, because it is specific to the structure of legal text (an obligation and its exception often live in adjacent subsections). Frame it as a domain-motivated design choice, not as a generic trick.

### 5.3 Automatic evaluation, as it exists today **[VERIFIED]**

`evaluation/judge/` — five registered metrics, each a separate module and prompt, each scored **1–5 integer** with a reasoning field (`core/schemas.py`):

| Metric | Module | Prompt | Needs reference? | Output keys |
| --- | --- | --- | --- | --- |
| Context relevance (precision) | `modules/context_relevance.py` | `prompts/judge/context_relevance.j2` | no | `ctx_precision`, `ctx_relevant_chunks`, `ctx_total_chunks`, `ctx_noise_analysis` |
| Context sufficiency | `modules/context_sufficiency.py` | `prompts/judge/context_sufficiency.j2` | no | `ctx_sufficiency`, `ctx_missing_info` |
| Faithfulness | `modules/faithfulness.py` | `prompts/judge/faithfulness.j2` | no | `faithfulness`, `hallucinated_claims` |
| Answer correctness | `modules/answer_correctness.py` | `prompts/judge/answer_correctness.j2` | **yes** | `correctness`, `factual_errors` |
| Answer relevance | `modules/answer_relevance.py` | `prompts/judge/answer_relevance.j2` | no | `answer_relevance`, `off_topic_content` |

Plus `modules/pairwise.py`: head-to-head A/B comparison run **twice with positions swapped**; if the two passes disagree it returns `tie`, confidence 1, and sets `pairwise_position_bias = True`. The docstring cites Zheng et al. (MT-Bench) as the motivation. **[VERIFIED]** This is good practice and should be reported in the paper as a methodological safeguard.

Composites in `evaluation/judge/orchestrator.py`: `retrieval_score` = mean of (`ctx_precision`, `ctx_sufficiency`); `generation_score` = mean of (`faithfulness`, `correctness`, `answer_relevance`); `overall_score` = mean of the two. **A score of 0 means "not evaluated" and is excluded from every average** (`_safe_avg`, and `stats.compute_summary` skips zeros). You must state this convention explicitly in the paper — it is unusual and a reviewer will otherwise read 0 as a valid low score.

### 5.4 Run tracing **[VERIFIED]**

`pipeline/tracing.py` writes one self-contained JSON per run. From `data/runs/sample_demo.json`, a run record holds `run_id, label, created_at, elapsed_seconds, config, n_queries, queries`, and each query trace holds:

```
query, reformulated_queries, round1_variants, merged_candidates,
deduped_candidates, two_call_enabled, gap_analysis, round2_variants,
round2_added, reranked_chunks, final_chunks, answer, reference, elapsed_seconds
```

**This is your most valuable research asset and you should say so in the paper.** Full provenance from query to answer, per configuration, makes both the quantitative analysis and the qualitative failure-mode analysis reproducible. It is also exactly what you will export to build the human-rating item bank (§7.10).

### 5.5 The human-feedback tool that already exists **[VERIFIED]**

`tool/` is a FastAPI + PostgreSQL backend with a Streamlit frontend, deployable to Vercel + Streamlit Community Cloud, with Supabase as the chunk/feedback store.

- `tool/backend/models.py::ChatResponse` stores `session_id, question, answer, retriever, retrieved_subsections (JSON), latency_ms, created_at`.
- `tool/backend/models.py::Rating` stores `response_id, rater_id, retrieval_relevance, completeness, correctness, comment, created_at, updated_at`, with a unique constraint on `(response_id, rater_id)` — **so multiple raters per response are already supported**, and a rater can revise a rating.
- `tool/backend/schemas.py::RatingRequest` constrains each criterion to `ge=1, le=5`.
- `tool/frontend/app.py` renders three `select_slider`s and a comment box in a popover, labelled "Score each criterion from 1 (poor) to 5 (excellent)."
- `tool/backend/main.py::admin_stats` returns per-criterion mean, count, 1–5 distribution, rating coverage, and a per-retriever breakdown.

This is a real head start. §7.9 lists what still has to change before it can produce study-grade data.

### 5.6 What the repository does NOT yet contain **[VERIFIED]**

Be honest with yourselves about this; the timeline in §14 depends on it.

- **No experiment results.** There is no `data/experiments/` directory. The sweep has not been run and committed.
- **No reference answers.** Only `data/reference_answers_template.csv` with **2 example rows**. Until `data/reference_answers.csv` exists, `answer_correctness` returns 0 ("NO_REFERENCE") for every query and drops out of `generation_score`.
- **No collected human ratings** in the repository.
- **Query set is 28 questions** (`data/good_queries.csv`, header `Question`, 28 non-empty rows, 0 duplicates). This is too small for the study in §7 and is not stratified.
- **Only one run trace**, `data/runs/sample_demo.json`, which is a one-query UI demo.
- `todo.txt` records the planned division of labour (Sifat: dataset filtering, 5 complex questions, references; Sayem: ingestion, running the dataset, paper introduction) and a meeting on 12 Aug. Treat §14 as a replacement for that plan, not an addition to it.

---

## 6. Gap analysis — what stands between the repository and a submission

| # | Gap | Severity | Section that fixes it |
| --- | --- | --- | --- |
| G1 | No socio-technical framing; the README is engineering-facing | Fatal for this venue | §3, §10 |
| G2 | No human evaluation | Fatal for Framing A | §7 |
| G3 | Query set too small (28) and not stratified; no unanswerable queries | Major | §7.3 |
| G4 | No expert reference answers, so `correctness` cannot run | Major | §7.3.4 |
| G5 | Generator and judge are the **same model family** (`response_model: gemini`, `judge_model: gemini` in `config/pipeline.yaml`) → self-preference bias | Major, and a reviewer *will* catch it | §9.1 |
| G6 | `tool/` does not record which pipeline configuration produced an answer (`ChatResponse` has `retriever` only) | Blocks comparative human eval | §7.9 |
| G7 | `rater_id` is a fresh `uuid4` per browser session (`tool/frontend/app.py`) → no stable rater identity, no inter-rater reliability | Blocks IRR | §7.9 |
| G8 | No blinding, no randomisation, no fixed item order; raters type their own questions | Blocks causal comparison | §7.7, §7.9 |
| G9 | Human criteria (3) and automatic metrics (5) are not aligned; "completeness" has no automatic counterpart, "faithfulness" has no human counterpart | Blocks the central claim C1 | §8 |
| G10 | No ethics approval, consent form, or data-sharing plan | Blocks submission | §7.13 |
| G11 | No corpus provenance table (document titles, dates, versions) | Reviewer objection | §5.1 |
| G12 | No sweep results committed | Blocks C2 | §14 |

---

## 7. The human evaluation — full protocol

This is the part you asked for, and it is the part that decides whether the paper is publishable. Design it as a study, not as a feedback form.

### 7.1 Purpose and research questions

State these verbatim in the manuscript (Section 3.1), then answer each one in Results.

- **RQ1.** How do domain experts rate the quality of RAG-generated answers to Bangladeshi telecom regulatory questions, across retrieval relevance, groundedness, completeness, correctness, and usability-for-decision?
- **RQ2.** To what extent do automated LLM-as-a-judge scores agree with expert ratings, per dimension? Where the two diverge, in which direction and by how much?
- **RQ3.** Do pipeline design choices that the automatic harness ranks as better (structure-aware retrieval, query reformulation operator, two-call corrective retrieval) also rank as better under expert judgement?
- **RQ4.** Does rater expertise moderate the agreement in RQ2 — i.e. do informed non-experts agree with the automatic judge more than experts do?
- **RQ5.** What failure modes do experts identify that no automatic metric captures?

RQ4 and RQ5 are the ones that make it a *Telematics and Informatics* paper. RQ4 speaks directly to the journal's long-running interest in the gap between technical performance and lived competence; RQ5 is where the governance implications come from.

### 7.2 Design

**Within-subjects, blind, counterbalanced, two-phase.**

- **Phase 1 — absolute rating.** Every rater rates answers from every system condition, on the same set of queries. Condition identity is hidden. Presentation order randomised per rater.
- **Phase 2 — forced-choice pairwise.** On the **pre-specified primary contrast C2 vs C3** (§7.11.5), each rater sees paired answers to the same query, side by side, labelled A/B, with **A/B assignment randomised per item**. Rater picks A, B, or "no meaningful difference", and gives a one-line reason. Fixing the contrast in advance rather than picking the Phase 1 winner avoids a post-hoc selection that a reviewer would rightly flag.

**Why Phase 2 matters more in the reduced design.** A forced choice takes roughly half the time of a full absolute rating and discriminates smaller differences, because the rater compares two texts directly instead of mapping each onto a 5-point scale. With 3 conditions and a 45-task budget, adding ~10 pairwise judgements per rater (~20 minutes) buys more condition-comparison sensitivity than adding 10 more absolute ratings would. Phase 1 is still required — RQ2 needs absolute human scores to compare against the judge's absolute scores — but do not let Phase 2 be the part that gets cut for time.

Phase 2 exists for one reason: `evaluation/judge/modules/pairwise.py` already produces machine pairwise verdicts with a position-bias flag. Running the human analogue lets you compute **human–machine preference agreement** and check whether the machine's position bias coincides with disagreement. That is a clean, publishable result and costs little extra rater time.

### 7.3 Query set

#### 7.3.1 Size

**[DECISION — settled]** **30 queries**, 6 types × 5 (§7.3.2). All 30 are rated by humans across 3 conditions (§7.5.1), and all 30 also feed the automatic sweep across the full design space.

Earlier drafts of this document said 75, then 45. Both were sized for designs with more conditions and a much heavier per-rater load than an expert panel would realistically complete. 30 is what follows from 6 raters × 15 queries at 3 ratings per item, and it is defensible — see §7.11.4.

The existing 28 queries in `data/good_queries.csv` are a natural starting pool: they were authored **before** this study design and so are not contaminated by it. Say that in the paper. But do not simply adopt all 28 — they are not stratified, contain no unanswerable items, and contain no cross-document (T5) items. Expect to keep roughly half and author the rest.

**Author more than 30.** Aim for ~40 and select 30. The surplus absorbs queries dropped in gold-provenance verification (§7.3.3), supplies the catch items for §7.7, and gives you replacements if a query turns out to be ambiguous in the pilot.

#### 7.3.2 Stratification

Stratify on two axes and report the cell counts in a table. Do not sample opportunistically.

**Six query types, 5 queries each. Types T1–T5 are content types; T6 is the answerability control.**

| Type | Definition | Example from the existing set |
| --- | --- | --- |
| T1 Single-fact lookup | Answer is one value or short phrase in one subsection | "What is the evaluation charge for a Nationwide ISP license application?" |
| T2 Enumerative | Answer is a closed list that must be complete | "What are the four categories of ISP licenses available?" |
| T3 Numeric / tariff | Answer is a fee, rate, or threshold, often from a schedule or table | "What is the annual fee for a VHF transceiver with 10W power output?" |
| T4 Procedural / conditional | Answer is a process, or an obligation with conditions and exceptions, typically spanning adjacent subsections | "What are the requirements for lawful interception (LI) for ISP?" |
| T5 Cross-document | Answer requires combining two or more of the 25 documents | *(none exist yet — author these; they are the strongest test of the hierarchical retriever)* |

**Axis 2 — answerability (crossed with Axis 1):**

**T6 — Unanswerable / out-of-scope (5 queries).**

**[DECISION — settled]** Do **not** cross answerability with the content types as a second axis. With 15 queries per rater a 5×2 grid leaves cells that some raters never see. Make unanswerable a **sixth type** instead, so the stratified split (§7.5.3) guarantees every rater gets 2–3 of them by construction.

A T6 query is one the corpus does not answer — a genuinely different jurisdiction, a repealed provision, or a plausible-but-absent topic. **This stratum is not optional.** It is the only way to measure whether the system abstains or confabulates, and abstention is precisely the governance question a T&I reviewer cares about.

Note honestly that **no current automatic metric scores abstention.** `faithfulness` penalises a confident wrong answer only if the retrieved chunks contradict it, and `answer_relevance` states in its own docstring that "a response that is completely wrong but on-topic can still score 5." Abstention is therefore measured by human item H6 (§7.6), and C1 (§7.4.2) is the condition on which it matters most. T6 items also rate fast — roughly 1 minute rather than 4 — so they cost little rater time.

#### 7.3.3 Query authorship and contamination control

- Queries must be authored by someone who did **not** tune the retrieval configuration. In this team, that means the person who did not set `config/pipeline.yaml`.
- Author them from the *documents*, not from system outputs. Never write a query by looking at what the system answered well.
- Record, per query, the **gold provenance**: document, chapter, section, subsection ID(s), page number(s). You already have all of these in chunk metadata, so this is cheap and it gives you a retrieval ground truth for free — enabling classical **recall@k / MRR / nDCG** alongside the LLM-judged `ctx_precision`. Reviewers trust those.
- Have a second person independently verify each gold provenance. Report the disagreement rate.

#### 7.3.4 Reference answers (closes G4)

Create `data/reference_answers.csv` with columns `Question,Answer`, matching the template. Requirements:

- Written by a domain expert, quoting or closely paraphrasing the governing subsection.
- Include conditions, exceptions, units, and currency — the `answer_correctness` rubric explicitly penalises dropping these (`prompts/judge/answer_correctness.j2`).
- Independently checked by a second expert; report agreement and how conflicts were resolved.
- **The reference-answer authors must not be the people who wrote the system prompts.** Otherwise correctness measures prompt-reference alignment, not truth.
- Note the matching rule from `README.md`: matching trims surrounding whitespace but otherwise uses the query text **exactly**. A single stray character silently yields a 0. Add an assertion to the pipeline that every query has a matched reference before a scored run.

### 7.4 System conditions

**[DECISION — settled]** **Three conditions, forming a grounding ladder:** no retrieval → plain retrieval → the full system. This is the team's design and it is the right one. It spans the widest possible quality range, which is exactly what the human↔judge agreement analysis (RQ2) needs, and it puts the no-retrieval arm in front of human raters rather than leaving it to the automatic judge — see §7.4.2.

| Paper label | Working name | `query_strategy` | `retriever` | `reranker` | `two_call` | Role |
| --- | --- | --- | --- | --- | --- | --- |
| **C1 — No retrieval** | basic | — | none | — | false | The generator alone, answering from parametric knowledge. Measures whether the model knows Bangladeshi telecom law at all. |
| **C2 — Standard RAG** | goto | `simple` | `vector` | **`voyage`** | false | Flat dense retrieval plus reranking, no reformulation. A credible, deployable field default — not a strawman. |
| **C3 — Structure-aware RAG** | expert | `decompose` | `hierarchical` | **`voyage`** | **true** | Adds reformulation, hierarchical retrieval with sibling/neighbour expansion, and corrective second-round retrieval. |

**The reranker is held constant across C2 and C3.** This is deliberate and it is the most important structural decision in the design: it converts reranking from a confound into a control, and it removes the strongest objection available to a reviewer — *"your gain came from an off-the-shelf reranker, not from your retriever."* C3's remaining delta over C2 is exactly three things, and all three are contributions of this work rather than commodity components.

**[TO VERIFY]** Fix the reranker plugin and keep it identical in both arms — `voyage` (`rerank-2.5`) or `cohere` (`rerank-v3.5`), per the `models.reranking` block in `config/pipeline.yaml` **[VERIFIED]**. The table above assumes `voyage`; correct it if you choose otherwise.

**Held constant across all three conditions** (and reported in an appendix table dumped from `config/pipeline.yaml`):

| Parameter | Value in the repo **[VERIFIED]** |
| --- | --- |
| `embedder` | `gemini` |
| `response_model` | `gemini` |
| `retrieval.top_k` | 30 |
| `retrieval.rerank_top_k` | 20 |
| `retrieval.relevance_threshold` | 0.01 |
| `post_processing` | `dedupe`, `relevance_filter` |
| all `hierarchical.*` thresholds | as configured |

Any silent drift in `post_processing` or `relevance_threshold` between C2 and C3 confounds the comparison invisibly. Assert them equal in the run script rather than trusting the YAML.

**Pre-specify the primary comparison as C2 vs C3** (§7.11.5) — that is the contribution. **C1 vs C2, the grounding effect, is the secondary comparison** and supplies the governance headline for claim C4 (§4): what an ungrounded model does with questions about a jurisdiction it has barely seen.

**[DECISION — act on this] Rename the third condition in the manuscript.** "Expert" is fine as a working name but must not reach the paper: it collides with *expert rater*, and "expert ratings of the expert condition" is a sentence no reader recovers from. "Basic" and "goto" are also informal, and "ours" — should it creep in — reads as advocacy and is a small identity leak under double-anonymised review. Use **C1 / C2 / C3** with the table above.

#### 7.4.1 C1 needs its own generation prompt — otherwise the condition is rigged

**[VERIFIED — this will break the study if missed.]** `prompts/generation/answer.j2` instructs the model to *"Answer the following question using ONLY the information provided in the context chunks below"*, and instruction 5 reads:

> *"If the chunks do not contain relevant information at all, respond with: 'The available documents do not contain sufficient information to answer this question.'"*

Run C1 through this prompt with an empty `context_window` and **instruction 5 fires on every query**. C1 abstains 100% of the time, scores a perfect confabulation rate, and the entire grounding comparison inverts.

Write a second prompt, `prompts/generation/answer_no_context.j2`:

- same `{{ domain }}` expert role, drawn from `config/domain.yaml`;
- same output conventions (instructions 3, 6, 7, 8 — exact figures, bullets, no source references, precision);
- **no** context-grounding clause, **no** forced-abstention clause;
- the model answers from its own knowledge and abstains only if it genuinely does not know.

Report both prompts in the appendix and state explicitly that C1 used a different prompt and why. A reviewer who assumes a single prompt will otherwise wonder about exactly this, and the explanation reads much better volunteered than extracted.

#### 7.4.2 What C1 buys, and what cannot be scored on it

Putting the no-retrieval arm in front of human raters — rather than judging it automatically, as an earlier draft of this document proposed — is a strict improvement. It means the paper's **governance headline is anchored on expert judgement, not on the LLM judge whose reliability the paper is questioning.** That tension is now gone. Keep it.

**But two rating items are undefined for C1, and coding them wrongly will corrupt the whole analysis.**

C1 shows the rater no passages. Therefore:

| Item | On C1 | Why |
| --- | --- | --- |
| **H1** retrieval relevance | **N/A** | There are no retrieved passages to rate. |
| **H2** groundedness | **N/A** | There is nothing to be grounded *in*. Redefining it as "grounded in the actual regulations" would measure a different construct and break commensurability with `faithfulness`. |
| H3 completeness | scored | |
| H4 correctness | scored | |
| H5 decision usability | scored | |
| H6 abstention | scored — **this is the point of C1** | |
| H7 / H8 failure tags and comments | scored | |

**Record H1 and H2 as *not applicable*, never as 1.** Coding an undefined item as the lowest score manufactures an enormous artificial condition effect and poisons every mean, every reliability coefficient and every model fit.

The same applies on the machine side: `ctx_precision`, `ctx_sufficiency` and `faithfulness` are meaningless with zero chunks. Note that `_safe_avg` in `evaluation/judge/orchestrator.py` treats 0 as "not evaluated" **[VERIFIED]**, so C1's `retrieval_score` will come out *empty* rather than *low* — a silent gap, not a visible zero. Filter C1 out of those metrics explicitly and report that you did.

**Consequence for power:** the RQ2 agreement analysis for H1 and H2 runs on **60 items (C2, C3), not 90**. Those two dimensions therefore have less resolution than H3/H4/H5. State it in §7.11.3 rather than letting a reader discover it in a table footnote.

#### 7.4.3 C3 is a bundle — and why that is acceptable here

C3 changes three things at once relative to C2: reformulation (`decompose`), hierarchical retrieval with sibling/neighbour expansion, and corrective two-call retrieval. Reranking is **not** among them — it is held constant (§7.4.4), which removes the most damaging version of this objection. But **if C3 wins, the human study alone still cannot say which of the three caused it**, and the hierarchical retriever's sibling/neighbour expansion is the genuinely novel element (§5.2) whose contribution you most want to isolate.

This is acceptable — the three remaining elements are all contributions of this work rather than commodity components — but only if the paper says the following out loud:

> The human study establishes **whether the automatic judge can be trusted**. The automatic sweep, having been licensed by that validation, performs the fine-grained component attribution. The three human conditions are chosen to span the quality range — the requirement of the agreement analysis — not to isolate components.

Written that way, the bundling stops being a compromise and becomes the reason the two halves of the study fit together. Left unsaid, it reads as a confound.

**State the residual caveat in Limitations.** You validate the judge at three widely separated quality levels and then apply it to fine-grained contrasts between adjacent configurations, where differences are small. That is an extrapolation. The Bland–Altman analysis (§7.12, step 4) partly addresses it — if judge bias varies with quality level, it will show — so report that plot explicitly as evidence for or against the extrapolation, rather than as a generic calibration check.

#### 7.4.4 Reranking is held constant — the consequence, and how to write it up

**[DECISION — settled]** Reranking sits in **both** C2 and C3, so it is a control rather than a manipulated variable. This is the right call and it should be defended explicitly in the Method section, not buried in a config table.

**Accept the cost up front: the C2 vs C3 effect will be smaller than it would have been with a bare-vector baseline.** At n = 30 the design detects roughly *d* ≈ 0.51 (§7.11.2), so **C2 vs C3 may return a null.** Plan for that outcome now rather than discovering it during analysis.

A null there is survivable, for three reasons:

1. **The paper's contribution is judge validity (C1 in §4), not system superiority.** RQ2 does not depend on C3 winning.
2. **C1 vs C2 is close to guaranteed to be large.** An ungrounded model answering questions about Bangladeshi licensing fees, spectrum charges and NTTN ownership limits will not do well. You have at least one effect that will land, and it is the one that carries the governance argument.
3. **A well-powered, well-reported null on a fair baseline is a more credible result than a large win over a strawman** — and reviewers in this venue read it that way.

What you must not do is report it as "no significant difference". Report it as bounded (§7.11.5), and let the automatic sweep — which runs on the same 30 queries at far greater statistical density — carry the finer-grained design conclusions.

#### 7.4.4.1 One asymmetry to disclose

The reranker *component* is identical in C2 and C3, but **its input is not.** Per `README.md` **[VERIFIED]**, two-call retrieval merges the round-2 chunks and reranks *the whole set* against the main query, so in C3 the reranker operates over a larger merged candidate pool by construction. Likewise `decompose` fans out into multiple query variants whose results are merged before reranking.

This is inherent to the designs being compared, not a flaw — but state it precisely:

> The same reranker model and `rerank_top_k` are applied in both retrieval conditions; in C3 the reranker operates over a larger merged candidate pool by design, as a consequence of multi-variant reformulation and corrective second-round retrieval.

Volunteered, it reads as precision. Discovered by a reviewer, it reads as a hidden confound.

#### 7.4.5 Report cost as well as quality

C3 runs query reformulation, a second retrieval round and a reranking call, so it is materially more expensive and slower than C2, which is in turn more expensive than C1. For a journal whose readers care about deployability in resource-constrained public agencies, a quality-versus-cost table is genuinely interesting rather than boilerplate.

This is nearly free to produce: run traces already record `elapsed_seconds` per query **[VERIFIED]** in `data/runs/*.json`, and `tool/backend/models.py::ChatResponse` records `latency_ms` **[VERIFIED]**. Add a token counter to the generator and report, per condition: median latency, LLM calls per query, and estimated cost per 1,000 queries.

#### 7.4.6 The ablations do not disappear — they move to the machine

**Humans rate 3 conditions. The automatic harness sweeps all of them.**

`scripts/run_experiments.py` already runs the full grid over the whole query set for API cost only. So the fine-grained ablations — including the component attribution that C3's bundle cannot provide on its own (§7.4.3) — stay in the paper as an **automatic-only results subsection** (§10, Results 5.1):

- operator family: `simple` / `decompose` / `diversify` / `abstract` / `hyde`
- retriever: `vector` / `bm25` / `hybrid` / `hierarchical`
- two-call: on / off
- sibling and neighbour expansion: on / off (tuned in `config/pipeline.yaml → hierarchical`, not as a sweep axis)

State this division of labour explicitly in the Method section: *the automatic sweep maps the design space; the human study validates the judge and anchors the three headline conditions.* Written that way it reads as deliberate design. Left unexplained, it reads as a corner cut.

**Consequence for the claims (§4).** C2 becomes primarily supported by the automatic sweep, with the human ratings confirming the single headline contrast (C2 vs C3). Say so plainly rather than implying the human study adjudicated every design choice.

### 7.5 Raters, allocation, and per-rater load

**[DECISION — settled]** The design below is the team's, refined. It replaces the incomplete-block scheme in earlier drafts, which it beats: because every rater sees **all three conditions for every query they are given**, the condition comparison is paired *within rater*, so rater severity cancels completely.

#### 7.5.1 The design

| Parameter | Value |
| --- | --- |
| Queries | **30** = 6 types × 5 (see §7.3.2) |
| Sets | **A** and **B**, 15 queries each, **stratified** — 2–3 per type per set |
| Shared anchor block | **6 queries** (3 swapped from each set), rated by *all* raters |
| Conditions rated by humans | **3** — baseline / default / ours (§7.4) |
| Conditions run automatically | the full sweep, on all 30 queries (§7.4.6) |
| Raters | **6** — three assigned to Set A, three to Set B |
| Rating tasks per rater | **54** = (15 own queries + 3 swapped) × 3 conditions |
| Ratings per item | **3**; **6** on the anchor block |
| Distinct items | 90 (30 queries × 3 conditions) |
| Total rating tasks | 324 |
| Total ordinal judgements (× 5 items H1–H5) | ~1,620 |

The arithmetic closes exactly: 90 items × 3 ratings = 270, plus 18 anchor items × 3 extra ratings = 54, giving 324.

#### 7.5.2 The constraint that binds

Per-rater load does not set the study's power. This does:

```
distinct queries covered = (n_raters × queries_per_rater) / ratings_per_item
```

**`ratings_per_item ≥ 3` is non-negotiable.** Below three you cannot compute Krippendorff's α, and without a stable human value per item RQ2 — the central research question — has nothing to compare the judge against. This, not the number of conditions or the per-rater load, is the parameter whose violation causes rejection. The design above satisfies it exactly, with no slack: **if one rater drops out, that set's items fall to 2 ratings and the reliability analysis breaks.** Recruit 7 or 8 and treat the surplus as insurance.

#### 7.5.3 Stratify the set split — do not randomise it

"Split 30 into two sets of 15" taken literally means a random cut, which can hand Set A five T1 queries and one T5. Split **within** each type: of the 5 queries in a type, 3 go to one set and 2 to the other, alternating which set gets the extra so both sets total 15.

| Type | Set A | Set B |
| --- | --- | --- |
| T1 single-fact | 3 | 2 |
| T2 enumerative | 2 | 3 |
| T3 numeric / tariff | 3 | 2 |
| T4 procedural / conditional | 2 | 3 |
| T5 cross-document | 3 | 2 |
| T6 unanswerable | 2 | 3 |
| **Total** | **15** | **15** |

Without this, question type is confounded with rater group and the per-type breakdown becomes uninterpretable.

#### 7.5.4 Why the sets must overlap

Two disjoint sets rated by two disjoint rater groups means **you can never check whether the groups are calibrated to each other.** You get two separate α estimates on 45 items each, never a pooled one, and no evidence that Group A and Group B are measuring the same construct. A reviewer will ask; "we did not check" is not an answer.

**Fix: swap 3 queries between the groups.** Each rater additionally rates 3 queries from the other set — +9 tasks, roughly 35 extra minutes. Six queries then carry 6 ratings each. From that block, report:

- agreement **between** groups (Group A's mean vs Group B's mean per item, and α computed across all 6 raters);
- agreement **within** each group, for comparison.

If the two are similar, you have earned the right to pool the sets in the main analysis and can say so. If they diverge, that is a finding about rater calibration worth a paragraph.

Run this block first and use it as the calibration step in §7.8 — then the cross-group anchor costs nothing beyond the calibration you already owe.

#### 7.5.5 Rater tiers, and the fate of RQ4

**[DECISION]** With 6 raters split across disjoint sets, **any expert / non-expert contrast is confounded with set**, so RQ4 (expertise moderation) is not answerable as designed. Two honest options:

1. **Drop RQ4.** The paper stands on RQ1, RQ2, RQ3 and RQ5; RQ2 is the contribution. Remove it from §7.1 rather than leaving it unanswered.
2. **Recruit 3 informed non-experts who rate only the 6-query anchor block** (18 tasks each, ~1 hour). That yields 3 tier-N ratings against 6 tier-E ratings on byte-identical stimuli — a small but clean tier comparison, and enough for a descriptive RQ4 subsection. **Recommended**, because it is cheap and it restores the finding this journal is most likely to find interesting.

Whichever you choose, all six primary raters should be **tier E** (domain experts). Screening: a short qualification questionnaire (e.g. name two licence categories and one obligation attached to each). Report how many were screened out.

Report, for every rater: tier, years of relevant experience, role, and whether they have previously used an AI assistant for regulatory work — **aggregated only**. Bangladesh's telecom regulatory community is small enough that role plus employer plus tenure identifies a person.

#### 7.5.6 Load and timing

54 tasks at ~4 min is roughly 3.5 hours; unanswerable items rate faster (~1 min), so the realistic figure is nearer 3 hours. Split into **three sessions of ~18 tasks**, with the 18-task anchor block run first as calibration.

**[TO VERIFY]** The 4 min/task figure is mine, not measured — H1 requires reading up to 20 retrieved subsections. Measure it in the pilot (§7.8 step 3) and re-size before the main round.

#### 7.5.7 Task ordering — do not show the three answers together

Each query has three answers. **Do not place them on one screen.** A rater who sees all three at once compares them implicitly, which destroys the independence of the absolute ratings that RQ2 depends on — and RQ2 is the paper.

Randomise the 54 tasks so that the three answers to any one query are **never adjacent** and ideally fall in different sessions. The rater re-reads the query three times, but the retrieved passages differ by condition anyway, so H1 must be redone regardless; only the query text is duplicated effort.

Comparative sensitivity comes from **Phase 2 pairwise** (§7.2), which is designed for exactly that and costs half the time per judgement. If the schedule slips, cut anything before cutting Phase 2.

### 7.6 The instrument — rating items with full anchors

This replaces the current 3-slider form. **Five ordinal items plus two categorical items plus free text.** Every item gets written anchors; unanchored 1–5 sliders are the single biggest source of noise in human evaluation, and the current tool has none beyond "1 (poor) to 5 (excellent)".

**C1 exception (§7.4.2): H1 and H2 are recorded as *not applicable* for the no-retrieval condition, never as 1.** The interface must offer N/A as a distinct, non-numeric response on those two items, and the export must preserve it as missing rather than coercing it to a number.

Present to the rater, per item: **the query**, **the generated answer**, and **the retrieved subsections that were shown to the generator** (the tool already renders these — `tool/frontend/app.py`, "Retrieved subsections" expander). Do **not** show the reference answer for items H1–H4; show it only for H5 if you choose reference-aided correctness (see note below).

---

**H1 — Retrieval relevance** *(maps to `ctx_precision`)*
> "Of the source passages shown, how many are actually useful for answering this question?"

| 5 | All shown passages are relevant. |
| 4 | Most relevant; one or two are noise. |
| 3 | About half relevant, half noise. |
| 2 | Only one or two relevant; mostly noise. |
| 1 | None relevant. |

*(Anchors deliberately mirror `prompts/judge/context_relevance.j2` so that H1 and `ctx_precision` are measuring the same construct. Do not paraphrase them loosely — identical anchors are what makes the agreement analysis in RQ2 interpretable.)*

---

**H2 — Groundedness / attribution** *(maps to `faithfulness`)* — **NEW, no current human counterpart**
> "Is every factual statement in the answer supported by the source passages shown?"

| 5 | Every claim traces to a shown passage. |
| 4 | Almost every claim supported; one minor unsupported addition. |
| 3 | Most claims supported, but several are added without support. |
| 2 | Many claims unsupported; the answer invents details. |
| 1 | The answer is largely unsupported by the passages. |

Add a required follow-up when H2 ≤ 4: *"Quote the unsupported statement."* This gives you machine-comparable evidence against the judge's `hallucinated_claims` field.

---

**H3 — Completeness** *(currently in the tool; NO automatic counterpart — see §8)*
> "Does the answer cover everything the question asks for, including conditions, exceptions, and limits?"

| 5 | Fully complete; nothing material omitted. |
| 4 | Substantively complete; a minor detail omitted that would not change a decision. |
| 3 | Core answer present but a material element (a condition, an exception, one item of a list) is missing. |
| 2 | Substantially incomplete; a reader would act wrongly on it. |
| 1 | Barely addresses what was asked. |

---

**H4 — Correctness** *(maps to `correctness`)*
> "Are the factual claims correct with respect to the governing regulation?"

| 5 | All assessable claims are correct; no material distortion. |
| 4 | Substantively correct; at most one minor imprecision that would not change a reader's decision. |
| 3 | Mixed; the core answer is usable but one material claim is wrong, or several details are imprecise. |
| 2 | Major errors or contradictions substantially undermine the answer. |
| 1 | The central answer is false or not meaningfully assessable. |

*(Anchors taken from `prompts/judge/answer_correctness.j2` so H4 and `correctness` are commensurable.)*

**[DECISION]** Whether experts judge H4 against their own knowledge (**unaided**) or against the reference answer (**aided**). Unaided is a stronger test of real-world usefulness and avoids anchoring; aided is faster and more reliable. **Recommendation: unaided for tier E, aided for tier N**, and report the difference — it is itself an RQ4 finding. Whichever you choose, state it and keep it constant within tier.

---

**H5 — Decision usability**
> "Would you rely on this answer in professional work without checking the source document first?"

| 5 | Yes, without reservation. |
| 4 | Yes, with a quick confirmation of one detail. |
| 3 | Only as a starting point; I would verify the substance. |
| 2 | No; it would mislead more than it helps. |
| 1 | No; it is actively dangerous to rely on. |

This is the item that turns a technical evaluation into a socio-technical one, and it is the item a T&I reviewer will find most interesting. It has **no automatic counterpart by design** — that is the point.

---

**H6 — Abstention appropriateness** *(categorical; shown for every item, scored only for the unanswerable stratum)*
> "Does the answer correctly signal that the source documents do not contain this information?"

- `correct_abstention` — says it cannot answer, and indeed the corpus does not contain it.
- `over_abstention` — refuses although the corpus does contain the answer.
- `confabulation` — gives a confident answer although the corpus does not contain it.
- `not_applicable` — the corpus contains the answer and the system answered.

Report the confabulation rate on the unanswerable stratum as a headline number. It will be one of the most quoted figures in the paper.

---

**H7 — Failure tag** *(multi-select; only shown when any of H2–H5 ≤ 3)*

Seed the list from what the corpus makes likely, then let the pilot extend it:
`wrong_licence_category` · `wrong_fee_or_amount` · `dropped_condition_or_exception` · `outdated_or_superseded_provision` · `conflated_two_documents` · `missing_part_of_list` · `right_document_wrong_section` · `vague_non_answer` · `contradicts_itself` · `other (specify)`

Pre-coded tags make the qualitative analysis in RQ5 tractable and let you report inter-rater agreement on the *taxonomy*, not just the scores.

---

**H8 — Free-text comment** *(required when any of H2–H5 ≤ 3, optional otherwise)*
> "In one or two sentences: what is wrong, and what should the answer have said?"

The existing `Rating.comment` column (`Text`, max 5,000 chars in `RatingRequest`) already supports this.

---

**Phase 2 item — pairwise preference**
> "Which answer would you rather receive? A / B / No meaningful difference." plus "Why, in one line."

### 7.7 Blinding, randomisation, and order control

- Raters never see condition labels, model names, or retriever names.
- Item order randomised per rater with a fixed seed recorded in the study log.
- In Phase 2, A/B mapping to conditions randomised per item and recorded; this is the human analogue of the position-swap in `modules/pairwise.py`.
- Raters cannot see other raters' scores. (The current admin dashboard shows recent feedback — restrict it during collection.)
- Raters must not be told which condition is "ours". Ideally the rater-facing materials never mention that the team built any of the systems.
- **Attention checks:** insert ~5% catch items — e.g. an answer to a *different* query, or an answer with an obviously fabricated fee. A rater who scores a catch item ≥4 on H4 is flagged. Report how many raters were excluded and why; pre-specify the exclusion rule before collection.

### 7.8 Procedure

1. **Rater onboarding** (~20 min): consent form, study purpose stated at a level that does not reveal the conditions, walkthrough of the interface, the rubric with anchors available on-screen throughout (not just in a briefing document).
2. **Calibration set** (10 items, shared by all raters, not counted in the main analysis): all raters rate the same 10 items, then the team computes agreement and holds a single calibration discussion clarifying anchors that split people. Revise anchor wording once, freeze it, and report that you did this.
3. **Pilot** (2 raters × 20 items): checks interface, timing, and whether any item is systematically confusing. Report median time per item; use it to size the main round honestly. **Pilot data is reported but excluded from the main analysis.**
4. **Main collection**, in sessions of at most ~40 items to limit fatigue. Log timestamps per rating (the `created_at`/`updated_at` columns already exist) so you can report median time-on-item and check for speeding.
5. **Phase 2** after Phase 1 is complete, so that Phase 1 conditions can be chosen from Phase 1 results.
6. **Debrief**: short semi-structured interview (15–20 min) with 3–5 tier-E raters. Ask what would have to be true for them to use such a system in practice, and what they would never trust it with. **These quotes carry the Discussion section.** Record with consent, transcribe, code thematically.

### 7.9 Required changes to `tool/` — concrete, with file paths

The existing tool is close but cannot produce study-grade data as written. These are the minimum changes. Each is small.

**(a) Record the full pipeline configuration per answer — closes G6.**
`tool/backend/models.py::ChatResponse` currently stores only `retriever: Mapped[str]`. Add:
```python
condition_label: Mapped[str] = mapped_column(String(64), index=True)   # "C3"
pipeline_config: Mapped[dict] = mapped_column(JSON)                    # full resolved config
```
Populate `pipeline_config` from the same dict that `pipeline/tracing.py` writes into `run.json`, so the tool's records and the offline traces are joinable.

**(b) Give raters stable identities — closes G7.**
`tool/frontend/app.py` line ~50 does `st.session_state.setdefault("rater_id", uuid.uuid4().hex)`. Replace with an assigned rater code entered at login (e.g. `E03`, `N01`) and validated against a roster. The `(response_id, rater_id)` unique constraint in `models.py` then becomes meaningful, and re-rating after a browser reload stops creating phantom raters.

**(c) Switch from free chat to an assigned, ordered item queue — closes G8.**
Today the rater types a question and rates the response (`tool/frontend/app.py::main`). For the study, add a **task mode**: the backend serves pre-generated items from the offline run traces in a per-rater randomised order, and the frontend renders query + answer + retrieved subsections + the rubric. Free chat stays available for the exploratory/deployment part of the paper, but it must not be the source of study data.

**(d) Extend the rating schema to the instrument in §7.6.**
`tool/backend/schemas.py::RatingRequest` currently has exactly `retrieval_relevance`, `completeness`, `correctness`, `comment`. Add `groundedness`, `decision_usability` (both `ge=1, le=5`, **nullable** so C1 can store N/A), `abstention` (enum), `failure_tags` (list of str), and `unsupported_quote` (str). `retrieval_relevance` must also become nullable for the same reason — it is currently a non-null `Integer` in `models.py`. Mirror in `models.py::Rating` and in the `AdminStats` aggregation in `main.py::_criterion_stats`.

**(e) Add a pairwise endpoint and table for Phase 2**: `(item_pair_id, rater_id, shown_left, shown_right, choice, reason)`. `shown_left`/`shown_right` must store the *condition* each side actually carried, so you can un-blind at analysis time.

**(f) Export.** One command that dumps ratings joined to `pipeline_config` and to the offline trace, as a tidy CSV with one row per (rater, item, criterion). Everything in §7.11 assumes tidy long format.

**(g) Lock the admin dashboard during collection** (`TELCORAG_ADMIN_PASSWORD` is already supported and, per `tool/README.md`, the analytics endpoint is intentionally open when it is empty — set it).

**Alternative worth considering [DECISION]:** since every item can be generated offline from `scripts/run_experiments.py` traces, you could skip live generation entirely and build the rating app as a thin form over a static item bank. That removes latency, API cost, and non-determinism from the rating sessions, and guarantees every rater sees byte-identical stimuli. **I recommend this.** Keep `tool/` for the deployment/exploratory story, and rate from frozen traces.

### 7.10 Building the item bank from existing traces

Concretely, once the sweep has run:

1. `python -m scripts.run_experiments` over the **full** axis grid on the 30-query set, **including a no-retrieval arm** → `data/experiments/<label>/run.json` per combination. This single sweep serves both purposes: the three combinations matching C1/C2/C3 (§7.4) become the human item bank, and every other combination becomes the automatic-only ablation results (§7.4.6).
2. A small export script walks each `run.json`, and for each query emits an item: `{item_id, query_id, condition_label, query, answer, final_chunks[], gold_provenance, stratum}`. `final_chunks` is exactly what the generator saw, so H1 and H2 are answerable from the item alone.
3. Freeze the item bank (hash it, commit the hash) before any rating begins. Report the hash in the paper's data-availability statement.

This also means the human ratings and the automatic judge scores are computed over **the same frozen outputs**, which is a precondition for the agreement analysis in RQ2. If the judge runs on one generation and the humans see another, RQ2 is meaningless.

### 7.11 Sample size, power, and what the design can and cannot detect

Be honest in the paper: this is a feasibility-constrained expert-elicitation study, not a large-N survey. Say so in the Method, put a number on the resolution limit, and the design reads as rigour rather than as thinness.

#### 7.11.1 The design, in numbers

| Parameter | Value |
| --- | --- |
| Conditions rated by humans | 3 (C1 no-retrieval, C2 standard RAG, C3 structure-aware — §7.4) |
| Conditions run automatically | full sweep (§7.4.6) |
| Queries | 30 (6 types × 5) |
| Query sets | A and B, 15 each, stratified |
| Shared anchor block | 6 queries |
| Tier-E raters | 6 (recruit 7–8 for attrition insurance) |
| Rating tasks per rater | 54 |
| Ratings per item | 3; **6** on the anchor block |
| Distinct items | 90 (but 60 for H1/H2 — §7.4.2) |
| Total rating tasks | 324 |
| Total ordinal judgements (× 5 items H1–H5) | ~1,620 |

#### 7.11.2 Detectable effects

Naive paired comparison on per-query mean ratings, α = 0.05, two-sided, 80% power:

| Distinct queries | Detectable *d* | On a 1–5 scale with SD ≈ 1.0 |
| --- | --- | --- |
| 60 | ≈ 0.36 | ~0.36 points |
| 45 | ≈ 0.42 | ~0.42 points |
| **30 (this design)** | **≈ 0.51** | **~0.51 points** |
| 28 (current query file) | ≈ 0.54 | ~0.54 points |
| 20 | ≈ 0.63 | ~0.63 points |

**Report ≈ 0.51 as an upper bound on the resolution limit, not as the analysis.** Three features of the design recover real sensitivity beyond it:

1. The primary analysis is the **cumulative link mixed model** (§7.12, step 3) fitted to all ~1,620 individual judgements with random intercepts for query and rater — not to 30 query means.
2. The design is **fully paired within rater**: every rater rates all three conditions for each of their queries, so between-rater severity differences cancel exactly. This is the single biggest gain, and it is the reason this design beats the incomplete-block scheme in earlier drafts.
3. Each per-query value averages 3 raters (6 on the anchor block), shrinking measurement error.

**[TO VERIFY]** Once the pilot gives a variance estimate, run the power analysis properly by simulating from a CLMM rather than relying on the t-test approximation above. Report the simulation in supplementary material — it converts "our sample is small" from a weakness into evidence of care.

#### 7.11.3 What this design cannot do

State these limits in the paper before a reviewer states them for you:

- **It cannot detect small condition differences.** Anything under ~0.4 points will not reach significance. If C2 vs C3 is a genuine but modest improvement, this study will not prove it — and that is an acceptable outcome provided you report it as bounded (§7.11.5).
- **It cannot compare confabulation rates across conditions** on the unanswerable stratum. With 5 T6 queries, report the rate descriptively with a wide CI (Wilson interval) and do not test it.
- **It cannot support subgroup analysis by question type.** 30 queries over 6 types is 5 per cell. Report category breakdowns as **descriptive only**, explicitly labelled exploratory. Do not run per-category significance tests.
- **H1 and H2 have less resolution than the rest.** Because those two items are not applicable to C1 (§7.4.2), their agreement analysis runs on 60 items rather than 90. Report the differing denominators in the table itself, not in a footnote.
- **It cannot attribute C3's gain to a single component.** C3 bundles reformulation, hierarchical retrieval and two-call correction (§7.4.3); component attribution comes from the automatic sweep, not from the raters.
- **C2 vs C3 may return a null**, because reranking is held constant and the baseline is consequently strong (§7.4.4). Pre-commit to reporting it as bounded.
- **It cannot generalise to a population of practitioners.** Six experts is an elicitation panel. Use mixed models that treat rater as a random effect; do not report population estimates.

#### 7.11.4 Does the reduced design risk rejection?

Separate what actually causes rejection from what merely looks small.

| Does **not** cause rejection | **Does** cause rejection |
| --- | --- |
| 3 conditions instead of 4 | Fewer than 3 ratings per item |
| 15 queries / 45 tasks per rater | Claiming significance from an underpowered comparison |
| 30 distinct queries | Reporting a null as "no difference" rather than as bounded |
| A 6-person expert panel | Hiding the constraint instead of pre-specifying it |
| Null results, reported honestly | No ethics approval (§7.13) |
| Ablations run by machine, not by humans | Framing the paper as a RAG systems paper (§2–§3) |

Nothing in the left column is unusual for this journal. Published *Telematics and Informatics* work routinely compares two things with modest samples. What the venue does not forgive is overclaiming.

#### 7.11.5 Two things that must go in the manuscript

1. **Pre-specify a single primary comparison: C2 vs C3 on H4 (correctness).** Label everything else secondary or exploratory. Correcting one primary test instead of six is a substantial power gain for free, and pre-registration (§7.13) makes the claim credible.
2. **Report nulls as bounded, never as absent.** Write *"no evidence of a difference larger than 0.47 points on a 5-point scale (95% CI −0.21 to 0.38)"*, not *"no significant difference"*. An underpowered study that states its own resolution limit is publishable; one that reports a null as a finding is not.

**[DECISION]** If rater recruitment falls short of 6, do **not** compensate by cutting to 2 ratings per item. Merge the two sets instead and run a smaller, fully-overlapped study — all raters rate all queries, fewer queries, but reliability and RQ2 stay intact. RQ2 is the paper; the condition ranking is not.

### 7.12 Analysis plan — pre-specify this before you collect

Write this into the manuscript's Method section, and ideally pre-register it (§7.13).

**(1) Descriptives.** Per condition × criterion × tier: mean, SD, median, full 1–5 distribution. Show distributions, not just means — ordinal data with ceiling effects looks very different in a histogram than in a mean.

**(2) Inter-rater reliability.**
- **Krippendorff's α (ordinal metric)** as the primary statistic — it handles the unbalanced structure (3 ratings on most items, 6 on the anchor block) that Cohen's κ cannot. Report α **per set**, **pooled**, and **across groups on the anchor block** (§7.5.4); the third is the evidence that pooling the two sets is legitimate.
- **Gwet's AC2** alongside it, because α is unstable under high prevalence (and regulatory answers will skew high on some criteria). Reporting both pre-empts a reviewer objection.
- **ICC(2,k)** for the reliability of the *averaged* rating, since the analysis uses averages.
- Bootstrap 95% CIs (≥2,000 resamples) for all three.
- Report per criterion. Expect H1 and H4 to agree better than H3 and H5; that pattern is itself reportable.
- Do **not** report raw percent agreement alone.

**(3) Condition effects (RQ3).**
- Primary: **cumulative link mixed model** (ordinal logistic with random intercepts for query and for rater), e.g. `ordinal::clmm(score ~ condition + tier + (1|query) + (1|rater))` in R. Ratings are ordinal and crossed-nested; treating 1–5 as interval and running ANOVA will draw a methods reviewer's fire.
- Secondary / robustness: Friedman test across conditions on per-query mean ratings, followed by Wilcoxon signed-rank pairwise with **Holm** correction. Report both; if they agree, say so in one sentence.
- Report effect sizes (odds ratios from the CLMM; rank-biserial r for Wilcoxon) and CIs, not only p-values.

**(4) Human–machine agreement (RQ2) — the core analysis.**
For each paired dimension (H1↔`ctx_precision`, H2↔`faithfulness`, H4↔`correctness`, and H-answer-relevance if you add it):
- **Quadratic-weighted Cohen's κ** between the machine score and the *modal* or *median* human score.
- **Spearman ρ** and **Kendall τ-b** at the item level.
- **Mean signed difference** (machine − human) with a 95% CI: this is the bias estimate, and it is the number that answers "is the LLM judge too generous?".
- **Bland–Altman-style plot**: difference against mean, to show whether bias varies with quality level. Expect the judge to be well-calibrated at the top and over-generous in the middle; if so, that is a finding.
- **Confusion matrix** (machine 1–5 × human 1–5) per dimension, as a heatmap figure.
- **Disagreement case analysis:** take the top ~20 items by |machine − human| and analyse them qualitatively. This is exactly what `102447` did and it is what makes the section readable.

**(5) Pairwise agreement (Phase 2).**
- Human preference vs. `pairwise_winner` from `modules/pairwise.py`: agreement rate, κ.
- Cross-tabulate against `pairwise_position_bias`: does the machine disagree with humans more often on items where its two position-swapped passes disagreed? A clean result here is a genuine methodological contribution.

**(6) Expertise moderation (RQ4).**
Add `tier` and `condition × tier` to the CLMM. Compare human–machine agreement statistics computed within tier E vs. tier N. **Hypothesis worth stating up front:** non-experts will agree with the LLM judge more closely than experts do, because both are susceptible to fluent-but-wrong text. If that holds, it is a strong, quotable, T&I-appropriate finding about automated evaluation and about who is qualified to supervise these systems.

**(7) Failure-mode analysis (RQ5).**
- Frequencies of H7 tags by condition and by query stratum.
- Thematic analysis of H8 comments and debrief transcripts: two coders, open coding on a 20% subsample, codebook agreed, then full coding, with Cohen's κ on the double-coded portion reported.
- Cross-reference against the judge's own `hallucinated_claims`, `factual_errors`, `ctx_missing_info`, and `ctx_noise_analysis` free-text fields — you already store all four. Reporting *what the judge said it found* next to *what the expert found* is a strong figure.

**(7b) Handling C1's undefined dimensions.** Before any comparison involving H1/H2 or `ctx_precision`/`ctx_sufficiency`/`faithfulness`, filter C1 out explicitly and report the denominator for every cell. Do **not** rely on `_safe_avg` to do this silently — it drops zeros, so C1's retrieval composite arrives *empty* rather than *low*, which is easy to misread as a data-collection failure. Condition effects on H3/H4/H5/H6 use all three conditions; effects on H1/H2 use C2 and C3 only, and should be reported in a separate panel.

**(8) Handling the "0 = not evaluated" convention.**
`orchestrator._safe_avg` and `stats.compute_summary` drop zeros. Human ratings never contain 0. Before any comparison, filter machine rows where the relevant metric is 0 and **report how many items were dropped and why** (`NO_REFERENCE`, `JUDGE_ERROR`). Silently dropping them is a reproducibility hole.

### 7.13 Ethics, consent, and data — closes G10

Non-negotiable for an Elsevier journal with human participants.

- **Ethics approval** from your institution's review board *before* collecting a single rating. Retroactive approval is usually impossible and some journals will not publish without it. Record the protocol number; it goes in the manuscript.
- **Informed consent**: written, covering purpose, time commitment, voluntariness and right to withdraw, what is recorded, how it is stored, how long, who sees it, and how results will be published.
- **Anonymity**: raters identified only by code (`E03`). Never publish a combination of attributes (role + employer + years) that identifies someone in a small professional community — Bangladesh's telecom regulatory bar is small. Report rater characteristics only in aggregate.
- **Compensation**: decide, disclose in the paper, and apply consistently.
- **Conflicts**: if any rater has a professional relationship with the authors or with BTRC, disclose it.
- **Data availability**: **[DECISION]** plan to release the query set, the gold provenance, the reference answers, the frozen item bank, the anonymised rating table, and the analysis scripts, under a DOI (Zenodo / OSF). Do **not** redistribute the source BTRC PDFs unless their licence permits — link to them instead and give retrieval dates. Releasing the ratings is a real strength for a paper whose claim is about evaluation methodology.
- **Declaration of Generative AI**: required by Elsevier for AI used in the *writing* process. Note that AI use as the *object of study* and as a *research instrument* is different from AI-assisted writing; describe the former in Methods and the latter in the declaration.
- **Pre-registration [DECISION]**: register the design, instrument, sample size, and analysis plan on OSF or AsPredicted before collection. It costs an afternoon, and against reviewers who suspect post-hoc metric selection in an LLM paper it is worth several rounds of argument.

---

## 8. Mapping the automatic evaluation to the human evaluation

This table is the spine of the paper. Build it early; it will become **Table 3** in the manuscript.

| Construct | Automatic metric (**[VERIFIED]** in repo) | Current human item (**[VERIFIED]** in `tool/`) | Proposed human item (§7.6) | Status |
| --- | --- | --- | --- | --- |
| Retrieval precision | `ctx_precision` (1–5), `context_relevance.j2` | `retrieval_relevance` (1–5) | **H1** | **Aligned.** Reuse the judge's own anchors so the two are commensurable. |
| Retrieval sufficiency | `ctx_sufficiency` (1–5), `context_sufficiency.j2` | — | *(optional H1b)* | **Machine-only.** About the *context*, not the answer. Either add a matching human item or state explicitly that it is excluded from RQ2. |
| Groundedness / hallucination | `faithfulness` (1–5) + `hallucinated_claims` (text) | **— none —** | **H2** *(new)* | **Gap (G9).** Today there is no human check on the metric that carries the paper's hallucination claims. This is the single most important addition. |
| Factual correctness | `correctness` (1–5) + `factual_errors`; requires `data/reference_answers.csv` | `correctness` (1–5) | **H4** | **Aligned in name, not yet in procedure.** The judge scores against a written reference; the human currently scores against their own knowledge. Decide and document which (§7.6, H4). |
| Completeness | **— none —** *(the `answer_correctness.j2` prompt explicitly says "Do not lower the score merely because the response omits a separate correct point")* | `completeness` (1–5) | **H3** | **Gap (G9), mirror image.** The human tool measures something no automatic metric measures. Either present H3 as a purely human dimension — a legitimate and interesting choice — or add a new `answer_completeness` judge module. **Recommendation: keep it human-only and say why.** It strengthens the "automation cannot replace expertise" argument. |
| Answer relevance / on-topicness | `answer_relevance` (1–5) + `off_topic_content` | — | *(optional)* | **Machine-only.** Low value for experts; its own docstring notes a completely wrong answer can score 5. Mention this limitation in the paper. |
| Decision usability | **— none, by design —** | — | **H5** | **Human-only.** The socio-technical payload. |
| Abstention / confabulation | **— none —** | — | **H6** | **Gap.** No metric currently rewards saying "not in the corpus". Add as a human item; optionally add a machine check. |
| Failure taxonomy | free-text `hallucinated_claims`, `factual_errors`, `ctx_missing_info`, `ctx_noise_analysis` | free-text `comment` | **H7 + H8** | Pre-coded tags make RQ5 tractable and comparable to the judge's own free-text diagnoses. |
| Preference | `pairwise_winner`, `pairwise_confidence`, `pairwise_position_bias` (position-swapped, `modules/pairwise.py`) | — | **Phase 2** | **Aligned and unusually strong.** The machine side already mitigates position bias; the human side randomises A/B. Direct comparison is available for free. |

**Three things to take from this table:**

1. Three of your automatic metrics have **no** human counterpart, and one human criterion has **no** automatic counterpart. Saying this plainly in the paper is a contribution, not an admission — it is the operational meaning of "automated evaluation is not a substitute".
2. For RQ2 to be interpretable, the paired items must share rubric wording. Copy the anchors from `prompts/judge/*.j2` into the human instrument verbatim. Do not improve the wording on one side only.
3. The pairwise comparison is the cleanest human–machine contrast you have, because both sides already control for position. Do not skip Phase 2.

---

## 9. Threats to validity — and how the paper must handle each

Write these into a dedicated Limitations subsection. Reviewers forgive acknowledged limitations; they do not forgive discovering one you hid.

**9.1 Self-preference bias in the judge (G5) — the most serious.**
`config/pipeline.yaml` sets `response_model: gemini` **and** `judge_model: gemini` **[VERIFIED]**. The same model family generates and grades. Published work on LLM judges documents self-preference. Mitigations, in order of strength:
1. Re-run the judge with a **different model family** on the full set, and report both, plus their agreement. This is the strongest answer and costs one extra pass.
2. If budget forbids a full re-run, do it on a **random 30% subsample** and report the agreement between the two judges alongside the human agreement. A three-way comparison (human vs. judge A vs. judge B) is a better figure than a two-way one.
3. At minimum, name the issue explicitly in Limitations with a citation. Do not leave it unmentioned.

**9.2 Reference-answer authorship.** If the same people wrote the system prompts and the references, `correctness` measures agreement with the team's own framing. Mitigate as in §7.3.4 and report who wrote what.

**9.3 Query construction.** 28 existing queries were authored in-house and may favour the system. Mitigate by authoring ~40 and selecting 30 with stratification and independent authorship (§7.3), and by reporting results **separately** for whichever of the original 28 survive selection and the newly authored ones. If they differ, say so.

**9.4 Rater pool size and selection.** 5–7 experts is small. Frame the study honestly as an expert-elicitation design, report per-rater descriptives, and use mixed models that treat raters as a random effect rather than pretending to a population estimate.

**9.5 Corpus recency and versioning.** Regulations are amended. Give the snapshot date for every document and state that the findings are conditional on that snapshot.

**9.6 Language.** The corpus and the system are English-only, while regulatory practice in Bangladesh operates in both Bangla and English. This is a real limitation **and** a T&I-relevant point about linguistic access — put it in Discussion as future work, not buried in Limitations.

**9.7 Generalisability.** One jurisdiction, one sector. Argue transferability structurally: hierarchically organised licensing instruments with numbered subsections, schedules, and cross-references are the norm across regulators, so the retrieval design should transfer even where the content does not. Do not overclaim.

**9.8 Non-determinism.** LLM generation is stochastic. Freeze the item bank (§7.10). If you report any re-generated numbers, report the temperature/seed settings and, ideally, variance across repeated generations for a subsample.

**9.9 Ecological validity of the rating task.** Rating 150 items in a form is not doing regulatory work. H5 and the debrief interviews partially address this; say so, and do not claim the study measures real-world adoption. (If you want that claim, it is a second paper — Framing C.)

---

## 10. Manuscript structure and word budget

Target 8,000 words. **[TO VERIFY]** whether the limit excludes references and tables.

| § | Section | Words | Content, mapped to what you have |
| --- | --- | --- | --- |
| — | Title, abstract, keywords, highlights | ~300 | See §11 |
| 1 | **Introduction** | 1,000 | The regulatory information problem: 25 binding BTRC instruments, 1,170 pages, navigable in practice only by specialists; who bears the compliance cost. Generative AI as a plausible remedy *and* a new risk in a legally consequential setting. The evaluation-validity problem: the field grades these systems with LLM judges, largely unvalidated against expertise in regulated domains. State C1–C4 (§4). End with contributions as a bulleted list. |
| 2 | **Related work** | 1,100 | Four strands, deliberately balanced: (a) e-government and public-sector AI information services — cite the T&I cluster in §12 so the editor sees the conversation you are joining; (b) RAG for specialised/regulated domains — telecom (Telco-RAG, TeleQnA, TelecomGPT, 3GPP RAG) and legal QA; (c) evaluation of RAG — RAGAS, ARES, LLM-as-a-judge and its biases; (d) human evaluation and the limits of automatic proxies. **Strand (a) must not be thinner than (c)** or the paper will read as an IR submission sent to the wrong venue. |
| 3 | **Context and system** | 1,200 | 3.1 The Bangladeshi telecom regulatory corpus (Table 1: the 25 documents with issuing authority and dates). 3.2 Pipeline (Figure 1: three stages). 3.3 The structure-aware retriever, with a worked example of sibling/neighbour expansion on a real licensing subsection (Figure 2). 3.4 Two-call corrective retrieval. **Compress ruthlessly.** The engineering deserves 1,200 words here, not 3,000; the rest goes to an appendix or the public repository. |
| 4 | **Evaluation design** | 1,600 | 4.1 RQs. 4.2 Query set and stratification (Table 2). 4.3 Conditions (Table 3 — the §7.4 table). 4.4 Automatic metrics (the five judges + composites + the 0-convention). 4.5 Human study: raters, instrument with anchors (Table 4), blinding, procedure, pilot, calibration. 4.6 The metric-mapping table (§8). 4.7 Analysis plan. 4.8 Ethics. |
| 5 | **Results** | 1,900 | 5.1 Automatic results across conditions (Table 5 + Figure 3). 5.2 Human results across conditions, by tier (Figure 4: distributions, not bars-of-means). 5.3 Inter-rater reliability (Table 6). 5.4 **Human–machine agreement per dimension** (Table 7 + Figure 5 confusion heatmaps + Figure 6 Bland–Altman) — the centrepiece. 5.5 Pairwise agreement and position bias. 5.6 Expertise moderation (RQ4). 5.7 Abstention and confabulation on the unanswerable stratum. 5.8 Failure taxonomy (Table 8 + Figure 7). |
| 6 | **Discussion** | 1,400 | Where automatic evaluation is trustworthy and where it is not, stated as an operational rule a practitioner could follow. What the failure taxonomy implies for deploying AI in regulatory information services. The expertise-moderation finding and what it means for who supervises these systems. Implications for regulators, for licensees, and for the design of public AI information services in low- and middle-income jurisdictions. **This section is why the journal takes the paper. Do not let it shrink.** |
| 7 | **Limitations and future work** | 400 | §9, plainly. |
| 8 | **Conclusion** | 300 | Four claims, answered. No new material. |
| — | References | — | ~60–80, weighted toward the journal's own conversation |
| — | Appendices / supplementary | — | Full corpus table, full config dump, full rubric, consent form, per-document results, prompt templates |

**Title [DECISION].** Candidates, in descending order of fit:

1. *Beyond automated scores: expert evaluation of retrieval-augmented generation for telecom regulatory question answering in Bangladesh*
2. *Can LLM judges replace regulatory experts? Human and automated evaluation of a retrieval-augmented question-answering system for Bangladeshi telecom regulation*
3. *Grounding generative AI in regulatory text: a structure-aware RAG system and its expert evaluation in a developing-country telecom regime*

(1) and (2) foreground the evaluation finding and signal the journal's register. (3) foregrounds the system and is the weakest fit here — though it is the best title if you go to a technical venue instead (§15).

---

## 11. Abstract, highlights, keywords

**Abstract [TO VERIFY: structured or unstructured, and word cap].** Write it last, in six moves, and put a number in moves 4 and 5:
1. Problem — regulatory information access, high stakes, low-resource jurisdiction.
2. Gap — RAG systems in regulated domains are evaluated almost entirely by automated proxies of unknown validity.
3. What you did — built a structure-aware RAG system over 25 BTRC instruments (6,858 indexed subsections); evaluated *N* answers across *K* configurations with *M* domain experts and *M'* informed non-experts against five automated LLM-judge metrics.
4. Key quantitative findings — agreement coefficients per dimension; direction and magnitude of judge bias; confabulation rate on unanswerable queries.
5. Key qualitative finding — the failure taxonomy, in a clause.
6. Implication — the concrete boundary between what automated evaluation can certify and what requires expert review, and what that means for deploying AI in public regulatory information services.

**Highlights** — **[TO VERIFY]** Elsevier's standard is 3–5 bullets, ≤85 characters each including spaces. Each must state a *result*, not an activity. Bad: "We conducted a human evaluation." Good: "LLM judges over-score faithfulness by X points against expert raters."

**Keywords** — pick 5–6 that a T&I editor recognises. Suggested: `retrieval-augmented generation`; `large language models`; `human evaluation`; `telecommunications regulation`; `e-government`; `Bangladesh`. Including `e-government` and `Bangladesh` materially improves the odds of reaching a relevant handling editor and reviewers.

---

## 12. Figures and tables to produce

Plan these now; they drive what your analysis scripts must output.

| ID | Type | Content | Data source |
| --- | --- | --- | --- |
| T1 | Table | The 25 corpus documents: title, issuing authority, date, pages, chunks | `knowledge_base/documents/`, plus manual provenance |
| T2 | Table | Query set: strata × counts, with one example per cell | expanded `data/good_queries.csv` |
| T3 | Table | System conditions and every held-constant parameter | `config/pipeline.yaml` |
| T4 | Table | The human rubric with full anchors | §7.6 |
| T5 | Table | Automatic metrics by condition: mean ± SD, n | `data/experiments/leaderboard.csv`, `judge_results.csv` |
| T6 | Table | Inter-rater reliability per criterion, per tier, with CIs | ratings export |
| T7 | Table | **Human–machine agreement per dimension**: weighted κ, ρ, τ-b, mean signed difference with CI | joined export |
| T8 | Table | Failure-tag frequencies by condition and stratum | H7 |
| F1 | Diagram | Three-stage pipeline | hand-drawn from `pipeline/` |
| F2 | Diagram | Worked example of hierarchical filtering + sibling/neighbour expansion on a real subsection | a `run.json` trace |
| F3 | Chart | Automatic scores by condition | `judge_results.csv` |
| F4 | Chart | Human rating **distributions** by condition and tier (stacked 1–5 or violin) | ratings |
| F5 | Heatmap | Machine × human score confusion, one panel per dimension | joined export |
| F6 | Chart | Bland–Altman: (machine − human) against mean | joined export |
| F7 | Chart | Failure-mode taxonomy frequencies | H7 |

**A note on charts:** show distributions wherever you have ordinal data. A bar chart of means over 1–5 ratings hides the thing reviewers most want to see — whether disagreement is symmetric noise or a split population.

---

## 13. Submission mechanics — checklist

**[TO VERIFY]** every line against the official Guide for Authors before submitting.

**Manuscript**
- [ ] Word count within limit for a research paper
- [ ] Anonymised for double-blind: no author names, affiliations, acknowledgements, or funding in the main file
- [ ] **Self-citations neutralised** — and check the *repository* too: if the manuscript links a public GitHub repo bearing your names, the review is no longer blind. Either omit the link during review and offer it on acceptance, or use an anonymised mirror (Anonymous GitHub / an anonymised OSF component)
- [ ] Separate title page with authors, affiliations, corresponding author, ORCIDs
- [ ] Abstract within cap; keywords
- [ ] Highlights file
- [ ] Figures at required resolution; tables editable, not images
- [ ] Reference style matches the journal
- [ ] Line numbers and double spacing if required

**Declarations**
- [ ] Declaration of Competing Interest
- [ ] CRediT author statement (conceptualisation, methodology, software, validation, formal analysis, investigation, data curation, writing, supervision — assign each explicitly)
- [ ] Funding statement
- [ ] **Ethics approval** statement with protocol number, plus informed-consent statement
- [ ] **Data Availability** statement (repository + DOI, or an explicit reason for restriction)
- [ ] **Declaration of Generative AI in the writing process** — and keep it separate from the description of AI as the object of study

**Supplementary**
- [ ] Full corpus provenance table
- [ ] Full prompt templates (`prompts/`) and resolved configs
- [ ] Query set, gold provenance, reference answers
- [ ] Anonymised rating export
- [ ] Analysis scripts
- [ ] Item-bank hash

**Before you click submit**
- [ ] Read three recent T&I articles end-to-end and match their register (see `sam_paper/journal_precedents.md`)
- [ ] Have someone outside the project read the Introduction and say what the paper is about. If they say "a RAG system", rewrite it.
- [ ] Check the aims and scope page once more against your final abstract

---

## 14. A realistic sequence

No dates, because they depend on rater recruitment and ethics turnaround — which is the single most commonly underestimated step. Dependencies matter more than a calendar.

**Stage 0 — Decisions (blocking).** Confirm Framing A (§3). Assign roles for query authorship vs. system tuning (§7.3.3). **Start the ethics application now** — it blocks Stage 3 and typically has the longest lead time of anything here.

**Stage 1 — Corpus and queries.** Build the provenance table (T1). Author ~40 queries and select 30, stratified across the six types, with gold provenance and independent verification. Write and cross-check `data/reference_answers.csv` for all 30 (T6 items get a reference stating that the corpus does not answer them).

**Stage 2 — Runs. This is now a hard dependency of Stage 3.** Run the **full** sweep (all axes, plus the C1 no-retrieval arm with its own prompt, §7.4.1) on the 30-query set. Run the judge. Commit `data/experiments/`. **Then** freeze the three human conditions, confirm the held-constant parameters match across C2 and C3, and hash the item bank (§7.10). Use the sweep to check that reranking behaves comparably in both arms before freezing. Run the second-judge-family pass for §9.1. Do not build the rating app's item bank before this stage completes.

**Stage 3 — Human study.** Build the rating app changes (§7.9) or the static item-bank form. Recruit and screen raters. Onboard, calibrate, pilot, revise anchors once, freeze. Collect Phase 1, then Phase 2. Debrief interviews.

**Stage 4 — Analysis.** Everything in §7.12. Produce T5–T8 and F3–F7.

**Stage 5 — Writing.** Draft in the order 3 → 4 → 5 → 2 → 6 → 1 → abstract. Writing the Introduction last, once you know what you found, is what keeps the framing honest.

**Stage 6 — Internal review and submission.** External read by someone in ICT policy rather than in NLP. Anonymise. Submit.

**Parallelisable:** Stage 1 and the ethics application; the related-work reading and Stage 2; the rating-app build and Stage 1.

**The critical path runs through ethics approval and rater recruitment, not through code.** Plan accordingly.

---

## 15. If *Telematics and Informatics* is not the right home

Keep these in reserve; a desk rejection should cost days, not months. Prepare the manuscript so the framing can be re-weighted without rewriting the study.

| Venue | Why it fits | What to re-weight |
| --- | --- | --- |
| **Telecommunications Policy** (Elsevier) | Telecom regulation is its core subject; a licensing-regime information study is squarely in scope | Expand the regulatory-regime analysis; foreground compliance burden; trim the technical detail further |
| **Government Information Quarterly** (Elsevier) | The canonical venue for e-government and public-sector AI; the government-chatbot literature lives there | Foreground public value and citizen/licensee access; add a governance framework |
| **Information Processing & Management** (Elsevier) | Takes rigorous IR/RAG evaluation work with real methodological contribution | Foreground retrieval design, add standard IR metrics (recall@k, nDCG) from your gold provenance |
| **Journal of the Association for Information Science and Technology (JASIST)** | Human information behaviour plus system evaluation; human–machine agreement studies fit well | Foreground the evaluation-validity contribution and the expertise moderation |
| **Expert Systems with Applications** / **Applied Sciences** | Will take the engineering paper as-is | Foreground the system and the ablations; drop most of the socio-technical framing |
| **Information Technology for Development** | Explicit developing-country ICT focus; the Bangladesh framing is an asset rather than a caveat | Foreground the development and access argument |
| **Telematics and Informatics Reports** (companion, ISSN 2772-5030) | Same family, broader remit, open access | A fallback if the main journal says "interesting but not our scope" |

**Note:** *Telecommunications Policy* and *Government Information Quarterly* are arguably better structural fits than T&I for the substance of this work. T&I is the better fit if and only if the paper genuinely leads with the human-versus-automated-evaluation finding. If you cannot commit to running the study in §7 properly, go to *Telecommunications Policy* or IP&M instead.

---

## 16. Reference starter set

Full bibliographic detail and abstracts are in `sam_paper/`. The PDFs of everything openly available are in `sam_paper/pdfs/`.

**Journal-internal (cite these — they show the editor you know the venue).** All **[VERIFIED]** in Crossref/OpenAlex:
- Lai & Li (2026), *Beyond accuracy: assessing the information quality of large language models for systematic literature reviews*, 109, 102447 — **the closest methodological precedent in this journal**
- Weinbrand (2026), *A search changer: auditing Google's AI Overviews interface in political and news search*, 107, 102417
- Quarati & Nikiforova (2026), *Automating the identification of High-Value Datasets in open government data portals*, 107, 102415
- Wang & Teo (2026), *Human–chatbot interaction, social support and public value co-creation: Evidence from users of government chatbots in China*, 105, 102380
- Amaral, Naranjo-Zolotov & Bação (2026), *Unequal AI readiness: institutional and digital disparities in e-government across the European Union*, 107, 102400
- Fan, Wang, Zhang & Sun (2026), *When AI lies to me: understanding user recognition, attribution, and response to AI hallucinations*, 108, 102434
- Nikiforova & McBride (2020), *Open government data portal usability: A user-centred usability analysis of 41 open government data portals*, 58, 101539
- Faroqi, Siddiquee & Ullah (2018), *Sustainability of telecentres in developing countries: Lessons from Union Digital Centre in Bangladesh*, 37, 113–127
- Chelliah, Thurasamy, Alzahrani, Alfarraj & Alalwan (2016), *E-Government service delivery by a local government agency: The case of E-Licensing*, 33, 925–935

**Technical foundations.** All **[VERIFIED]**, PDFs downloaded:
- Bornea, Ayed, De Domenico, Piovesan & Maatouk (2024), *Telco-RAG* — the closest system to yours
- Maatouk et al. (2023), *TeleQnA* — telecom QA benchmark
- Zou et al. (2024), *TelecomGPT*; Erak et al. (2024), 3GPP fine-tuned RAG; Lee et al. (2024), *TelBench*
- Es, James, Espinosa-Anke & Schockaert (2024), *RAGAS*; Saad-Falcon, Khattab, Potts & Zaharia (2024), *ARES*
- Zheng et al. (2023), *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena* — **already cited in `evaluation/judge/modules/pairwise.py`; cite it in the paper too**
- Gao et al. (2023), *RAG for LLMs: A Survey*; Chen, Lin, Han & Sun (2024), *Benchmarking LLMs in RAG*; Wang et al. (2024), *Searching for Best Practices in RAG*
- Louis, van Dijck & Spanakis (2024), *Interpretable Long-Form Legal QA with Retrieval-Augmented LLMs*

**Still to source yourselves (not verified here — find current citations):**
- Krippendorff's α and Gwet's AC2 methodology references
- Self-preference / self-enhancement bias in LLM judges
- Inter-rater reliability practice in NLP human evaluation
- BTRC annual reports and Bangladesh telecom sector statistics, for the Introduction's framing of the compliance problem

---

## 17. Open questions for the team

These are genuine **[DECISION]** points I cannot settle from the code.

1. **Do you have access to real domain experts?** Everything in Framing A depends on recruiting ≥5 telecom regulatory practitioners. If you cannot, say so early — the paper becomes Framing B or moves venue. This is the first question to answer.
2. **Ethics route.** Which institution's review board, and what is its realistic turnaround?
3. **Budget.** API cost for the automatic sweep (the full grid × 30 queries × generation + 5 judges, plus the no-retrieval arm and a second judge family — the sweep is far larger than the 3 human conditions, §7.4.6), compensation for 6–8 expert raters plus any tier-N raters, and possibly an APC.
4. **Authorship and CRediT split**, agreed in writing before the work, not after.
5. **Can `data/reference_answers.csv` realistically be authored for 30 queries by a qualified person, and independently checked?** If not, `correctness` drops out and the paper leans harder on H2/H3/H5.
6. **Is the corpus snapshot current?** If any of the 25 documents has been superseded, either refresh or state the snapshot date prominently.
7. **Second judge family** — yes on the full set, or on a subsample? (§9.1)
8. **Open data** — can the rating export and query set be released? (Strongly recommended.)
9. **Anonymised repository during review** — decide the mechanism now, not at submission.

---

## 18. Summary — the ten things that matter

1. This journal has **never** published a RAG systems paper. Do not submit one.
2. Lead with the **evaluation-validity finding**, not the system.
3. `102447` ("Beyond accuracy…") is your structural template. Read it first.
4. The human study is the contribution, so design it as a study: blind, randomised, stratified, pre-specified. **The one parameter you cannot trade away is ≥3 ratings per item** — everything else (conditions, per-rater load, query count) is negotiable; that is not, because RQ2 dies without it (§7.5.2).
5. Add **groundedness (H2)**, **decision usability (H5)**, and **abstention (H6)**. Keep **completeness (H3)** as a human-only dimension and explain why.
6. Copy the judge's rubric anchors verbatim into the human instrument, or RQ2 is uninterpretable.
7. **30 queries, 6 types × 5** (five content types plus unanswerable), gold provenance, stratified 15/15 split with a 6-query overlap between rater groups. Three human conditions forming a grounding ladder — no retrieval → standard RAG → structure-aware — with **the reranker held constant across the two retrieval arms** (§7.4.4). The automatic sweep covers the rest of the design space (§7.4.6).
8. Fix the same-model-family judge problem (`response_model` = `judge_model` = `gemini`), or a reviewer will fix it for you.
9. Start the ethics application before anything else; it is the critical path. And write `answer_no_context.j2` before running C1 — the current generation prompt forces abstention on every query when the context is empty (§7.4.1).
10. Give the Discussion 1,400 words on governance implications. That is what this journal buys.
