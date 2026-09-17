# `sam_paper/` — sample papers

Reference material for the *Telematics and Informatics* submission described in [`../guideline.md`](../guideline.md).

Everything here was collected on **2026-09-13**. Bibliographic metadata comes from the Crossref API (journal record and works list for ISSN 0736-5853), OpenAlex, and Semantic Scholar. Nothing was written from memory; where a fact could not be verified, the file says so.

## What is in here

| File | Contents |
| --- | --- |
| [`journal_precedents.md`](journal_precedents.md) | **15 articles published in *Telematics and Informatics* itself.** Verified metadata, abstracts where openly available, and per-paper notes on why each matters and what to imitate. These are the models for *how to write the paper*. |
| [`technical_analogues.md`](technical_analogues.md) | **12 open-access papers** on telecom RAG, legal QA, and RAG evaluation — the technical foundation and the novelty yardstick. Each has a downloaded PDF. |
| [`pdfs/`](pdfs/) | The 12 PDFs, all openly licensed or preprints. |

## Why the journal precedents have no PDFs

ScienceDirect returns HTTP 403 to automated requests, so none of the Elsevier PDFs could be retrieved programmatically. Several of the 2026 articles are hybrid open access under **CC-BY** and download freely from a browser:

- `10.1016/j.tele.2026.102447` — Beyond accuracy (LLM information quality) — **CC-BY**
- `10.1016/j.tele.2026.102417` — Auditing Google's AI Overviews — **CC-BY**
- `10.1016/j.tele.2026.102415` — Automating High-Value Dataset identification — **CC-BY**
- `10.1016/j.tele.2026.102400` — Unequal AI readiness in EU e-government — **CC-BY**
- `10.1016/j.tele.2026.102418` — Digital public management reform — **CC-BY**

The rest are subscription-only; use institutional access. `10.1016/j.tele.2018.05.006` (the Bangladesh telecentres paper) has a green-OA author manuscript at Flinders Academic Commons (`http://hdl.handle.net/2328/38995`).

Nothing paywalled was scraped or redistributed here.

## Reading order

**Before drafting anything:**
1. `journal_precedents.md` → Lai & Li (2026), *Beyond accuracy…* — the structural template for the whole paper.
2. `journal_precedents.md` → Weinbrand (2026), *A search changer* — how an audit study is written for this venue.
3. `journal_precedents.md` → Quarati & Nikiforova (2026), *High-Value Datasets* — proof that an artefact paper can be published here, and how much socio-technical framing that takes.

**Before writing Related Work:**
4. `pdfs/01_TelcoRAG_Bornea2024.pdf` — the nearest published system; you must position against it.
5. `pdfs/07_LegalQA_LongForm_RAG_Louis2024.pdf` — the legal-domain analogue.

**Before finalising the evaluation design:**
6. `pdfs/04_ARES_SaadFalcon2024.pdf` — why automated judges need human anchoring.
7. `pdfs/05_LLMasJudge_MTBench_Zheng2023.pdf` — judge biases; already cited inside `evaluation/judge/modules/pairwise.py`.
8. `pdfs/03_RAGAS_EsMagdy2024.pdf` — the published definitions of the metrics this repo implements.
9. `pdfs/08_Benchmarking_LLMs_in_RAG_Chen2024.pdf` — "negative rejection", the published name for the unanswerable stratum in `../guideline.md` §7.3.2.

## Coverage note

Searching the journal's full 2,844-record back catalogue found **no article on retrieval-augmented generation** and effectively none on question answering. That absence is the central strategic fact behind `../guideline.md` §2 and §3: this venue has no precedent for a RAG systems paper, so the submission has to lead with the evaluation finding rather than the system.
