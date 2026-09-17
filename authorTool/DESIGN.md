# `authorTool/` — design

**Status:** built. Design and implementation, in sync as of 2026-09-14.
**Written:** 2026-09-14.
**Run it:** `streamlit run authorTool/app.py --server.address=127.0.0.1`
**Scope:** an **offline**, author-facing workbench for running the TelcoRAG pipeline under any configuration, reading the generated answer, and inspecting the exact evidence behind it — retrieved chunks side by side with the source PDF pages, navigable with left/right controls in a page overlay.

---

## 0. How to read this document

Same marker convention as [`paper/guideline.md`](../paper/guideline.md) §0.

| Marker | Meaning |
| --- | --- |
| **[VERIFIED]** | Checked directly against this repository's files on 2026-09-13/14. The check is named. |
| **[TO VERIFY]** | Not confirmed. Confirm before relying on it. |
| **[DECISION]** | A choice the team has to make. A recommendation is given; the call is yours. |

Paths are relative to the repository root (`/Users/sayemshahad/Desktop/research/TelcoRAG`).

Nothing here invents a file, a field, or a number. Where something was not checked, it says so.

---

## 1. Purpose

One sentence: **let an author drive the whole pipeline from a UI, and see precisely what the generator saw.**

Three jobs it has to do well.

1. **Configure.** Expose every pipeline axis — embedder, query strategy, retriever, reranker, two-call, top-k, thresholds, hierarchical parameters — without editing `config/pipeline.yaml` and without restarting.
2. **Ask.** Type a question, run it, read the answer, see latency and cost.
3. **Verify.** For every retrieved chunk, open an overlay showing the chunk text **and the actual PDF page it came from**, and walk pages with `←` / `→`.

### 1.1 Why this tool exists

Three concrete needs, all of which the current repository leaves unserved.

- **Authoring the question pool.** [`humanEvaluation/DESIGN.md`](../humanEvaluation/DESIGN.md) requires 24 questions with verified **gold provenance** — document, chapter, section, subsection id, page numbers. Verifying provenance means reading the source page. Today that means opening a 217-page PDF by hand.
- **Choosing a configuration.** Every axis in `config/pipeline.yaml` is a choice, and the combinations are not obvious from the YAML. Authors need to feel what each one returns — including the condition triples `humanEvaluation/` will later freeze — before committing to it.
- **Qualitative failure analysis (RQ5).** `paper/guideline.md` §7.12 step 7 asks for a disagreement case analysis. That is chunk-level reading work, and it needs a chunk-level reader.

### 1.2 Non-goals

Stating these prevents scope creep, and one of them is a hard constraint.

- **Not an evaluator interface.** It captures no ratings and has no evaluator accounts. That is [`evaluatorTool/`](../evaluatorTool/DESIGN.md).
- **Never deployed.** It runs on an author's machine, against the local `knowledge_base/`, with the author's own API keys. It has no authentication **by design**, so it must not be exposed to a network.
- **Does not replace `tool/`.** `tool/` is the public-facing deployed demo. Leave it alone.
- **Does not write to `config/pipeline.yaml`.** Configuration chosen in the UI is an **overlay** over the YAML, never a mutation of it. A tool that rewrites the file that defines the experiment is a reproducibility hazard.

---

## 2. What the repository already provides

Verified inventory. The tool is mostly assembly, not new machinery.

### 2.1 Pipeline entry points **[VERIFIED]**

| Need | Existing code |
| --- | --- |
| Discover available plugins | `core/registry.py` — `EMBEDDERS`, `QUERY_STRATEGIES`, `RETRIEVERS`, `RERANKERS`, `discover_plugins()` |
| Run retrieval | `pipeline/stage3_retrieval/orchestrator.py` — `RetrievalPipeline` |
| Generate an answer | `pipeline/stage3_retrieval/generator.py` — `generate_response` |
| Record everything that happened | `pipeline/tracing.py` — `QueryTrace`, `RunRecorder` |
| Resolve config | `config/settings.py` — `SETTINGS`, `KNOWLEDGE_BASE_DIR`, `RUNS_DIR`, `QUERIES_FILE`, `REFERENCE_FILE`, `get_chunker_name()`, `bm25_index_path()` |
| Domain wording | `config/domain.yaml` |

`scripts/run_retrieval.py` and `scripts/run_experiments.py` already wire these together for the CLI. The authorTool is the interactive sibling of `run_retrieval.py`, and should call the same functions rather than reimplementing them.

### 2.2 The configuration surface **[VERIFIED]**

From `config/pipeline.yaml`, the full set of knobs the UI must expose:

| Group | Keys |
| --- | --- |
| Component selection | `embedder`, `chunker`, `query_strategy`, `retriever`, `reranker` |
| Model overrides | `models.embedding.<provider>`, `models.reranking.<provider>`, `embedding_dimensions` |
| Generation / judging | `response_model`, `judge_model` |
| Post-processing | `post_processing` (ordered list: `dedupe`, `relevance_filter`, `mmr`) |
| Retrieval | `retrieval.top_k` (30), `retrieval.rerank_top_k` (20), `retrieval.relevance_threshold` (0.01), `retrieval.mmr_lambda` (0.7) |
| Hybrid | `hybrid.rrf_k` (60), `hybrid.bm25_weight` (0.5) |
| Two-call | `two_call.enabled` (false), `two_call.max_rounds` (1) |
| Hierarchical | `pool_factor` (3), `count_bonus` (0.25), `level_bonus` (0.10), `levels[]` (`doc_name`/3, `chapter`/4, `section`/5), `expand_siblings` (true), `sibling_level` (`section`), `siblings_per_section` (5), `expand_neighbors` (true), `neighbor_high` (0.65), `neighbor_low` (0.30), `neighbor_moderate` (0.40), `neighbor_max_hops` (2) |
| Throttling | `embedding_request_delay_seconds.<provider>` |
| Chunking (ingestion-time, read-only here) | `chunking.max_size`, `chunking.overlap`, `chunking.neighbor_window` |

Plugin values currently registered **[VERIFIED]** from `pipeline/stage*/`:
`embedder` ∈ {openai, gemini, cohere, voyage, perplexity} · `chunker` ∈ {baseline} · `query_strategy` ∈ {simple, decompose, diversify, abstract, hyde} · `retriever` ∈ {vector, bm25, hybrid, hierarchical} · `reranker` ∈ {voyage, cohere, rrf, llm, none}.

**These lists must not be hardcoded in the UI.** §4.1 explains why and how.

### 2.3 The knowledge base layout **[VERIFIED]**

```
knowledge_base/documents/<FOLDER>/
├── markdowns/page_1.md … page_N.md
├── pdfs/page_1.pdf     … page_N.pdf
├── structured_output.json
└── structured_output_chunks__baseline.json
```

25 document folders: `4G_cellular, BPO, BWA, CMS, Fee, ICT_policy, ICX, IGW, IIG_Guideline, IIG_operator, IPTSP, ISP, ITC, MNPS, NFAP, NTTN, RFC, Satelite, Submarine_cable, TVAS, Telecom_policy, VSAT, VTS, infra_sharing, nix_guide`.

Totals **[VERIFIED]**: 6,858 chunks, 1,172 split page PDFs, 261 MB of page PDFs, 63 MB of chunk JSON, 336 MB for `knowledge_base/` overall. Full-document PDFs also exist in `resources/*.pdf` (166 MB).

### 2.4 Three facts that make the PDF overlay possible — all verified

These are the load-bearing facts of §5. Each was checked directly.

**(a) `doc_name` → folder is 1:1.**
Chunk metadata carries `doc_name` as the *full document title*, not the folder name — e.g. folder `ISP` carries `doc_name = "REGULATORY AND LICENSING GUIDELINES FOR INTERNET SERVICE PROVIDER (ISP) IN BANGLADESH"`. **[VERIFIED]** by scanning all 25 chunk files: every folder contains exactly one distinct `doc_name`, and no title is shared between folders. So a `doc_name → folder` index is well-defined and can be built by a single scan.

> Do not try to match folder names against `doc_name` with string heuristics. Build the index from the data.

**(b) `page_numbers` is a comma-separated string of 1-indexed page numbers.**
**[VERIFIED]**: the field is `str` for all 6,858 chunks. 232 distinct values. Most are a single number (`"7"`, `"12"`); many are short runs (`"5, 6"`, `"8, 9, 10"`); the largest observed spans 57 pages — an NFAP chunk with `"51, 52, 53, ... 114"` (note it is *not* contiguous; it skips 62, 65, 70, …). **The parser must handle a sparse, comma-separated, arbitrarily long list.**

**(c) Those page numbers index the page files directly.**
**[VERIFIED]** on three documents of different sizes: the maximum page number appearing in chunk metadata equals the count of `pdfs/page_*.pdf` and of `markdowns/page_*.md`.

| Folder | max page in metadata | `pdfs/page_*.pdf` | `markdowns/page_*.md` |
| --- | --- | --- | --- |
| ISP | 47 | 47 | 47 |
| NFAP | 217 | 217 | 217 |
| Fee | 4 | 4 | 4 |

Spot-checked further: the first ISP chunk has `page_numbers = "2"`, and `markdowns/page_2.md` begins `# TABLE OF CONTENTS` — matching that chunk's text. So `page_numbers = "16"` resolves to `pdfs/page_16.pdf`, with **no offset correction**.

**[VERIFIED — all 25, 2026-09-14.]** The max-page-equals-file-count assertion was run across every document and holds: `max(page_numbers) <= count(pdfs/page_*.pdf)` everywhere, so **no document needs a page offset**. One document deviates in a way that does not affect PDF resolution:

| Folder | max page in metadata | `pdfs/page_*.pdf` | `markdowns/page_*.md` |
| --- | --- | --- | --- |
| nix_guide | 41 | 43 | 41 — `page_34.md` and `page_36.md` absent |

So `nix_guide` resolves correctly in the PDF view, and those two pages fall back to the "no markdown page file" branch in §5.3. `evidence.py` re-runs this assertion on every index build, so a re-ingestion that breaks the property is reported rather than silently mis-resolved.

### 2.5 Streamlit capabilities on the installed version **[VERIFIED]**

Installed: **Streamlit 1.61.1**. Checked by introspection:

- `st.pdf(data, *, height=500, key=None)` — **exists**, and is the page renderer. **Correction [VERIFIED 2026-09-14]:** the API being present is not enough — it renders through the separate `streamlit-pdf` frontend package, which was **not installed**. `import streamlit_pdf` failed, and `streamlit-pdf 2.0.1` is incompatible with Streamlit 1.61.1 (it raises `StreamlitAPIException` at import: the component wants `asset_dir` declared). **`streamlit-pdf==1.0.8` works** and is what `authorTool/requirements.txt` pins. The viewer checks for it and falls back to the markdown page plus a per-page PDF download rather than failing inside the dialog.
- `st.dialog` — **exists**. This is the overlay mechanism.
- `st.segmented_control` — **exists**. This is the chunk switcher.

So the overlay needs no third-party component and no custom JS. `requirements.txt` pins only `streamlit` (unpinned) and `tool/requirements.txt` pins `streamlit>=1.40`. **`st.pdf` requires ≥ 1.49** — see §8.1.

---

## 3. Architecture

### 3.1 Stack

**Single Streamlit application, in-process with the pipeline. No backend service, no database.**

This is the right choice here, and the reasoning is worth recording because it is the opposite of the choice made for `evaluatorTool/`:

- The tool is offline and single-user, so there is nothing for a client/server split to buy.
- The pipeline is a Python library in this repo; calling it in-process removes serialization, a network hop, and a second place for configuration to drift.
- It must read `knowledge_base/` from local disk — 336 MB that will never be uploaded anywhere.
- The repo already runs Streamlit (`app.py`, `tool/frontend/app.py`), so there is no new stack to learn.
- Verified above: `st.pdf` + `st.dialog` cover the hard UI requirement natively.

### 3.2 Folder layout

```
authorTool/
├── README.md                  # orientation, 10 lines
├── DESIGN.md                  # this file
├── requirements.txt           # streamlit>=1.49, streamlit-pdf==1.0.8 (§8.1)
├── app.py                     # Streamlit entrypoint; tabs, page layout, state
├── config_panel.py            # renders the config form from the registry + YAML
├── config_resolver.py         # YAML -> UI overlay -> effective config
├── runner.py                  # builds the pipeline, runs a query, returns a QueryTrace
├── evidence.py                # doc_name -> folder, page_numbers -> page files
├── viewer.py                  # the page overlay: chunk text + PDF deck + nav
├── compare.py                 # single-axis comparison mode (§6.3)
└── .cache/
    └── document_index.json    # generated; doc_name -> folder map (§5.2)
```

`.cache/` is generated and should be git-ignored.

### 3.3 Screen layout

```
┌───────────────────────────────────────────────────────────────────────┐
│  SIDEBAR                    │  MAIN                                   │
│                             │                                         │
│  Ask │ Compare │ Saved runs │  Question ______________________ [Run]  │
│  ▸ Components               │                                         │
│      embedder    [gemini ▾] │  ── Answer ──────────────────────────   │
│      query_strat [decompose]│  The evaluation charge for a ...        │
│      retriever   [hierarch.]│                                         │
│      reranker    [voyage ▾] │  ⏱ 8.4 s · 4 LLM calls · 20 chunks      │
│  ▸ Retrieval                │                                         │
│      top_k         [30]     │  ── Retrieved chunks (20) ───────────   │
│      rerank_top_k  [20]     │  #1  ISP · §30 CHANGES IN OWNERSHIP     │
│      threshold     [0.01]   │      p.16 · score 0.83      [Inspect]   │
│  ▸ Two-call   [x] enabled   │  #2  Fee · Schedule-2                   │
│  ▸ Hierarchical  ▾          │      p.3  · score 0.79      [Inspect]   │
│  ▸ Post-processing ▾        │  …                                      │
│                             │                                         │
│  [Reset to pipeline.yaml]   │  ── Pipeline trace ▾ ────────────────   │
│  Effective config ▾  (diff) │  variants · gap analysis · round 2      │
└───────────────────────────────────────────────────────────────────────┘
```

Clicking **[Inspect]** opens the overlay described in §5.

---

## 4. Configuration — the flexibility requirement

"Make sure the tool is flexible" is the requirement most easily lost during implementation. It has one definition and four rules.

**The definition.** A configuration is *any combination of the keys in `config/pipeline.yaml`* — nothing more and nothing less. The tool ships **no presets and no named conditions**: naming a few blessed combinations would quietly make them the default thing to try, which is the opposite of what a workbench is for. Condition definitions belong to [`humanEvaluation/`](../humanEvaluation/DESIGN.md) and `paper/guideline.md`, which own the experiment; this tool's job is to make every combination equally reachable and to hash whatever you land on.

### 4.1 Rule 1 — enumerate choices from the registry, never from a literal

The plugin lists in §2.2 must be read at runtime:

```
core.registry.discover_plugins()
options = sorted(RETRIEVERS.keys())      # and EMBEDDERS, QUERY_STRATEGIES, RERANKERS
```

**Consequence, and the point of the rule:** when someone adds `pipeline/stage3_retrieval/retrievers/graph.py`, it appears in the dropdown with **zero edits to `authorTool/`**. A hardcoded `["vector", "bm25", "hybrid", "hierarchical"]` silently makes the tool wrong the day the pipeline grows, and the failure is invisible — the new retriever simply never appears.

### 4.2 Rule 2 — render scalars generically from the YAML, not from a hand-written form

Do not hand-write a widget per key. Walk the parsed `config/pipeline.yaml` tree and map by type:

| YAML type | Widget |
| --- | --- |
| `bool` | `st.checkbox` |
| `int` | `st.number_input(step=1)` |
| `float` | `st.number_input(format="%.3f")` |
| `str` with registry options | `st.selectbox` over registry keys |
| `str` free | `st.text_input` |
| `list[str]` | `st.multiselect` (order preserved — matters for `post_processing`) |
| `list[dict]` | repeatable row editor (only `hierarchical.levels`) |
| `None` | `st.text_input`, empty means `null` (e.g. `embedding_dimensions`) |

A new scalar in `pipeline.yaml` then gets a widget for free. Only `hierarchical.levels` needs bespoke handling, because it is an ordered list of `{field, top_n}` records whose **order is semantic** — it is the coarse-to-fine filtering order.

> **Grouping.** Use the YAML's own top-level keys as the sidebar section headers (`retrieval`, `hybrid`, `two_call`, `hierarchical`, `post_processing`). Then the UI's shape tracks the config file's shape automatically, and an author reading one can navigate the other.

### 4.3 Rule 3 — the effective config is a layered merge, and the layers stay visible

```
  config/pipeline.yaml        (base — read from disk, never written)
        ↓ deep merge
  UI overrides                (only keys the author actually touched)
        =
  EFFECTIVE CONFIG            (what the run uses; hashed; written into the trace)
```

Implemented in `config_resolver.py`. The effective config is installed into the in-memory `SETTINGS` singleton by `applied()` for the duration of a run — the pipeline reads `SETTINGS.pipeline` both when it is constructed and again during a search (`hierarchical.*`, `hybrid.*` are read at search time **[VERIFIED — `retrievers/hierarchical.py:88`, `retrievers/hybrid.py:81`]**), so build and run both happen inside that block. The YAML on disk is untouched.

Requirements on this:

- **Only touched keys enter the override layer.** If the author never opens the Hierarchical section, those keys must not be pinned into the override — otherwise a later change to `pipeline.yaml` is silently masked.
- **Show the diff.** An always-available "Effective config ▾" expander renders the merged config with every key that differs from `pipeline.yaml` marked. Without this, an author cannot tell whether a surprising result came from their change or from a stale widget.
- **"Reset to pipeline.yaml"** clears the override layer entirely.
- **Hash it.** `sha256` of the canonical-JSON effective config, shown in the UI and written into the trace. This is what makes an author's finding reproducible, and it is the same hash the frozen item bank uses ([`humanEvaluation/DESIGN.md`](../humanEvaluation/DESIGN.md) §6). It is also the pipeline cache key: one built `RetrievalPipeline` per effective config, so switching a knob rebuilds and switching back reuses.

### 4.4 Rule 4 — greying out beats hiding

Retriever-specific parameters (`hybrid.*` when the retriever is not `hybrid`; `hierarchical.*` when it is not `hierarchical`) should be **disabled and annotated**, not hidden:

> `hybrid.rrf_k` — *inactive: retriever is `hierarchical`*

Hiding them teaches the author the knob does not exist. Disabling them teaches the author the knob is conditional, which is the truth.

### 4.5 No presets

There is deliberately no preset file, no preset picker, and no saved-condition concept.

- **A configuration is the YAML keys.** Any combination is one form away, so a preset would only save typing on the combinations someone guessed in advance.
- **Presets drift.** A stored partial config silently masks later edits to `pipeline.yaml` on exactly the keys it names — the same failure mode Rule 3 exists to prevent, in file form.
- **Naming is the experiment's job, not the tool's.** `paper/guideline.md` §7.4 defines the human-evaluation conditions and `humanEvaluation/` freezes them into the item bank by config hash. If the tool also carried a copy, there would be two definitions of C3 and no rule saying which wins.

What replaces them: the **effective-config hash** is shown next to every answer and written into every saved run, so a configuration worth returning to is identified by a hash rather than a nickname, and the run JSON carries the full config that hash refers to.

Two facts an author will still hit, recorded here because the YAML does not state them:

- **`reranker: none` is a real registry value [VERIFIED]** — `RERANKERS` contains `none`, so "no reranking" is a legal combination like any other.
- **"No retrieval at all" is not a configuration.** `RETRIEVERS` contains `vector, bm25, hybrid, hierarchical` **[VERIFIED]** and nothing else; generating with an empty context is a separate code path, which this tool does not implement. It also needs its own prompt — `prompts/generation/answer.j2` instruction 5 forces abstention when the context does not answer the question **[VERIFIED]**, so running an empty context through it would abstain every time. If that condition is needed, it belongs in the pipeline (and in `prompts/generation/`), not in a UI checkbox here.

## 5. The evidence overlay

This is the feature the tool is being built for, so it gets specified in full.

### 5.1 Requirement restated

From a retrieved chunk, open an overlay that shows the chunk **and the PDF page(s) it came from**, with `←` / `→` moving between pages.

### 5.2 The document index

Built once, cached at `authorTool/.cache/document_index.json`, rebuilt when any chunk file's mtime is newer than the cache.

```json
{
  "built_at": "2026-09-14T10:00:00Z",
  "chunker": "baseline",
  "documents": {
    "REGULATORY AND LICENSING GUIDELINES FOR INTERNET SERVICE PROVIDER (ISP) IN BANGLADESH": {
      "folder": "ISP",
      "page_count": 47,
      "pdf_dir": "knowledge_base/documents/ISP/pdfs",
      "markdown_dir": "knowledge_base/documents/ISP/markdowns",
      "page_offset": 0,
      "source_pdf": "resources/ISP.pdf"
    }
  }
}
```

- `page_count` — count of `pdfs/page_*.pdf`.
- `page_offset` — **reserved, `0` for all 25 documents [VERIFIED — §2.4c]**. It exists so that a document failing the max-page assertion can be corrected in data rather than in code. The resolver applies `file_page = metadata_page + page_offset`.
- `missing_markdown_pages` — pages with a PDF but no markdown (`nix_guide`: 34, 36). The markdown toggle falls back for exactly these.
- `source_pdf` — the whole-document PDF in `resources/`, offered as a "open full document" affordance.

**Build-time assertion.** While building, assert `max(page_numbers) <= page_count` per document. On failure, record the document in a `warnings` list in the index and surface it in the UI. Do not fail the build — a single bad document should not block the tool.

### 5.3 Page resolution

```
chunk.metadata.doc_name    → index.documents[...].folder
chunk.metadata.page_numbers→ [int(p) for p in value.split(",") if p.strip().isdigit()]
                           → sorted, de-duplicated
folder + page              → knowledge_base/documents/<folder>/pdfs/page_<n>.pdf
                           → knowledge_base/documents/<folder>/markdowns/page_<n>.md
```

Defensive cases, all of which occur or plausibly occur in this corpus:

| Case | Handling |
| --- | --- |
| `page_numbers` empty or unparseable | Show chunk text only; banner "no page reference recorded". |
| `doc_name` not in the index | Show chunk text only; banner naming the unknown `doc_name`; offer "rebuild index". |
| Page file missing | Skip that page in the deck; name it in the banner (`page file missing for p.N`). |
| Markdown page missing but PDF present (`nix_guide` 34, 36 — **[VERIFIED]**) | PDF renders; the Markdown toggle says so and leaves the PDF available. |
| 57-page span (NFAP, **[VERIFIED]**) | Handled by the deck (§5.4); a long span is normal, not an error. |
| Non-contiguous span (`51,52,…,63,64,66` — **[VERIFIED]**) | The deck follows the recorded list, gaps included. **Never** expand a span into a contiguous `range()`; that fabricates provenance. |

### 5.4 The page deck — the navigation model

The decision to make here is what `←` / `→` means when a chunk spans multiple pages and there are 20 chunks. Three models were considered:

| Model | Behaviour | Problem |
| --- | --- | --- |
| Per-chunk only | `←`/`→` change chunk; multi-page chunks show a stacked scroll | A 57-page chunk becomes an unusable scroll |
| Two independent controls | One pair for chunk, one for page | Two controls doing the same-shaped job; the author must think about which |
| **Flattened deck (recommended)** | `←`/`→` walk one linear list of `(chunk, page)` pairs, crossing chunk boundaries | Needs a clear breadcrumb, else the author loses their place |

**Recommendation: the flattened deck, with a chunk-level jump alongside it.**

Build the deck once when the overlay opens:

```
deck = [ (chunk_rank, folder, page_no) ]
       for each chunk in displayed rank order,
       for each page in that chunk's sorted page list
```

- `←` / `→` step one position through `deck`, crossing chunk boundaries. Disabled at the ends — do **not** wrap; wrapping hides the fact that you have reached the end of the evidence.
- `st.segmented_control` over chunk ranks jumps to the **first page of that chunk**.
- Breadcrumb, always visible:
  `Chunk 3 of 20 · ISP · page 16 of 47 · deck 7 of 58`
  Both denominators matter: *page 16 of 47* locates the reader in the document; *deck 7 of 58* locates them in the evidence.
- Deck position is the single piece of overlay state. Keep it in `st.session_state` keyed by the run hash, so re-opening the overlay returns to where the author was.

### 5.5 Overlay contents

`st.dialog(width="large")`, two columns:

**Left — what the retriever returned**

- Rank, retrieval score, reranker score if present.
- `doc_name`, `chapter`, `section`, `subsection_id`, `page_numbers` — the metadata fields that exist **[VERIFIED]**.
- The chunk `text`.
- **[DECISION]** Which text to show. Chunk metadata carries several variants: `subsection_text`, `full_subsection_text`, `bm25_text`, `context_summary`, plus the composed `text` field that prefixes `Document:` / `Chapter:` / `Section:` **[VERIFIED — visible in the sample chunk]**. **Resolved (D1):** the composed `text` is shown by default, because *that is what was embedded and what the generator saw*, with a radio switching to `subsection_text` / `full_subsection_text` / `bm25_text` for debugging — only the variants a given chunk actually carries are offered. Showing a cleaner variant by default would misrepresent the retrieval, which defeats the tool's purpose.

**Right — the source of truth**

- `st.pdf(page_path, height=760)` for the current deck page — falling back to the markdown page plus a download when the `streamlit-pdf` package is absent (§2.5).
- Above it: `←` `→`, the breadcrumb, and a **"Markdown"** toggle that swaps the PDF for `markdowns/page_<n>.md`.
- **"Open full document"** → `resources/<FOLDER>.pdf` (a download button; Streamlit cannot open a local file in a new tab).
- **"Mark as gold provenance"** (§7.3).

**[DECISION] Highlighting.** Highlighting the chunk inside the PDF requires a text-layer search and an annotation pass — `pymupdf` can do it, but it is **not currently installed [VERIFIED — `import fitz` fails]** and it is not in `requirements.txt`. **Resolved (D2): no PDF highlighting in v1.** Instead, the Markdown view marks the chunk inside the page by line match, in either direction — a page line contained in the chunk, or a line containing the whole chunk. Page text and chunk text come from the same extraction, so containment is reliable; a reflowed line simply does not match and the page renders unmarked, which is a visible and honest outcome rather than a wrong one. No dependency added. Revisit only if provenance verification proves slow in practice.

### 5.6 Keyboard navigation

Streamlit has no built-in key binding. Buttons are the contract; keyboard is a convenience.

**[DECISION]** Add `streamlit-shortcuts` (or a small `components.html` key listener) to bind `←`/`→`, `Esc`, and `j`/`k`. **Deferred, as recommended.** Ship buttons first, measure whether provenance verification is actually slow, and add key binding only if it is. A third-party component that breaks on a Streamlit upgrade is a poor trade for a tool whose whole value is being dependable offline.

---

## 6. Running a query

### 6.1 Flow

1. Resolve the effective config (§4.3) and hash it.
2. Get or build a `RetrievalPipeline` for that hash — **cache by hash** (`st.cache_resource`). Rebuilding the pipeline per query would re-open the Pinecone index and reload the BM25 artifact on every keystroke-triggered rerun.
3. Run retrieval with tracing on, producing a `QueryTrace` **[VERIFIED — `pipeline/tracing.py`]**.
4. Call `generate_response`.
5. Fill `trace.answer`; if the question matches a row in `data/reference_answers.csv`, fill `trace.reference` too.
6. Render answer, chunks, and the trace panel.
7. On **Save**, append to a `RunRecorder` and write `data/runs/<timestamp>__author.json` (`RunRecorder`'s own `<timestamp>__<label>` naming, so the file sorts and reads like every other run).

Reusing `RunRecorder` rather than inventing a session format is deliberate: author sessions land in the same schema as `scripts/run_experiments.py` output, so they are readable by the same viewers and joinable in analysis.

### 6.2 The trace panel

`QueryTrace` records more than the final chunks **[VERIFIED]**, and all of it should be inspectable, collapsed by default:

`reformulated_queries` · `round1_variants` (per-variant hits) · `merged_candidates` / `deduped_candidates` · `gap_analysis` · `round2_variants` / `round2_added` · `reranked_chunks` · `final_chunks` · `elapsed_seconds`

Two panels earn their space:

- **Query fan-out** — the variants `decompose` / `diversify` / `hyde` produced, each with its hit count. This is how an author sees *why* a reformulation helped or hurt.
- **Gap analysis** — the round-1 sufficiency verdict and the follow-up queries it emitted, shown only when `two_call_enabled`. This is the most opaque part of the pipeline and the part authors will most often need to explain in the paper.

Chunks should be inspectable at **every** stage, not only `final_chunks`. Watching a chunk survive round 1, survive reranking, then get dropped by `relevance_filter` is exactly the diagnostic the tool exists to provide.

### 6.3 Comparison mode

**Run one question under several configurations at once and show the answers side by side.** This is what makes the tool useful for *choosing* a configuration rather than merely browsing one, so it is in v1.

With no presets, a comparison is defined the way a run is: take the configuration currently in the sidebar and **vary exactly one key**. That is the whole control surface — an axis (any scalar key in `pipeline.yaml`, component choices first) and the values to sweep.

- Values are typed like the key: registry options for the five component keys, `true`/`false` for booleans, comma-separated numbers otherwise.
- **One axis at a time, on purpose.** Whatever differs between the columns is the axis and nothing else, so a difference in the answers is attributable. Sweeping two axes at once produces a grid an author cannot read and a comparison they cannot defend.
- Runs are **sequential, never concurrent** — the Gemini embedder is throttled via `embedding_request_delay_seconds.gemini: 5` **[VERIFIED]**, and parallel runs would fight that throttle.
- Each column shows answer · latency · LLM calls · chunk count · config hash, with its own **[Inspect]** opening its own deck.
- All the runs are written into **one** `RunRecorder` file with distinct labels (`retriever=hybrid`, …), so the comparison is a single reproducible artifact.
- The tool states up front how many full pipeline runs the sweep will perform, because each one spends API credit.

**Do not show a quality verdict.** No judge scores, no winner marking, no ranking. Comparison mode is for authoring; scoring answers is `evaluation/judge/`'s job, and putting a verdict here would invite authors to select configurations by eyeballing a handful of questions.

### 6.4 Saved runs

Any run JSON on disk — `data/runs/*.json` from this tool or `scripts/run_retrieval.py`, and `data/experiments/*/run.json` — opens in the same chunk list and the same evidence overlay, with **no API calls**. Provenance reading, which is most of the work in §7, therefore costs nothing and does not depend on re-running anything.

## 7. Reference and provenance support

Small features, disproportionate payoff for the work in `humanEvaluation/`.

### 7.1 Question source

The question box should accept free text, but also offer:

- the 28 rows of `data/good_queries.csv` **[VERIFIED — header `Question`, 28 non-empty rows, 0 duplicates]**;
- the 24-question pool at `humanEvaluation/pool/questions.csv` once it exists.

### 7.2 Reference answer

If `data/reference_answers.csv` exists, look the question up and show the reference beside the answer, collapsed.

**Note the matching rule [VERIFIED, from `README.md`]:** matching trims surrounding whitespace but otherwise compares the query text **exactly**. One stray character yields no match — and downstream that silently produces a `correctness` score of 0, which `_safe_avg` then drops. The tool should therefore say **"no reference found for this exact question text"** explicitly rather than just showing nothing. Surfacing the near-miss here is the cheapest place in the whole project to catch it.

### 7.3 Provenance capture — the bridge to `humanEvaluation/`

While inspecting a chunk, a **"Mark as gold provenance"** button appends a row to `humanEvaluation/pool/gold_provenance.csv`:

```
question_id, doc_folder, doc_name, chapter, section, subsection_id, page_numbers, marked_by, marked_at
```

This turns provenance capture from a separate transcription chore into a by-product of reading the page — and transcription is where provenance errors come from. The schema matches [`humanEvaluation/DESIGN.md`](../humanEvaluation/DESIGN.md) §4.2 exactly; keep the two in sync.

**Independent verification is still required.** `paper/guideline.md` §7.3.3 requires a second person to verify each provenance and the disagreement rate to be reported. The button records `marked_by`, so a second pass appends rather than overwrites, and the two passes can be compared.

---

## 8. Risks

### 8.1 Streamlit version

`st.pdf` requires **Streamlit ≥ 1.49**. Installed here: **1.61.1 [VERIFIED]**. But `requirements.txt` pins `streamlit` unpinned and `tool/requirements.txt` pins `>=1.40` **[VERIFIED]** — so a clean install on a teammate's machine could resolve below 1.49 and the overlay would fail with an `AttributeError` at the moment it is needed.

And `hasattr(st, "pdf")` is not the real check: the API exists on 1.61.1 while the `streamlit-pdf` frontend package it renders through does not ship with Streamlit and **was not installed here [VERIFIED]**.

**Done:** `authorTool/requirements.txt` pins `streamlit>=1.49` and `streamlit-pdf>=1.0.8` (2.0.1 is incompatible with Streamlit 1.61.1 — see §2.5). The viewer checks `import streamlit_pdf` rather than `hasattr`, and when it is missing renders the markdown page plus a per-page PDF download with the install hint, instead of raising inside the dialog.

### 8.2 Cost

Every run spends API credit, and `decompose` + `two_call` multiplies calls per question. The sidebar carries a per-session counter (runs, LLM calls, elapsed), and comparison mode states up front how many runs it is about to perform.

The LLM-call count is **measured, not inferred**: `runner.py` wraps every module-level binding of `general_response` / `structured_response` for the duration of a run and restores them after. The pipeline modules do `from clients.gemini import general_response` **[VERIFIED]**, so each holds its own reference and patching `clients.gemini` alone would undercount.

### 8.3 Index staleness

If chunks are re-ingested, the cached document index goes stale and pages resolve to the wrong document. Compare cache mtime against the newest `structured_output_chunks__*.json` on startup and rebuild automatically.

### 8.4 The tool is unauthenticated

Stated in §1.2 and repeated here because it is the only security-relevant property: `streamlit run` binds `0.0.0.0` by default on some setups. Document `--server.address=127.0.0.1` in the README and do not deploy this folder anywhere.

---

## 9. Build order

Each step left the tool usable, so work could stop at any point without a broken artifact. All of it is built.

| # | Step | Gives you | State |
| --- | --- | --- | --- |
| 1 | `evidence.py` + index builder, with the 25-document assertion from §2.4/§5.2 | Verified page resolution; settles the **[TO VERIFY]** | **done** — 25/25, no offsets needed |
| 2 | `app.py` skeleton: question → `RetrievalPipeline` → `generate_response` → answer + chunk list | A working offline Q&A | **done** |
| 3 | `viewer.py`: the overlay, deck, `←`/`→`, breadcrumb, markdown toggle | **The core feature** | **done** |
| 4 | `config_panel.py` + `config_resolver.py`: registry-driven form, layered merge, diff, hash | The flexibility requirement | **done** |
| 5 | Trace panel (§6.2) and `RunRecorder` output | Reproducible author sessions | **done** |
| 6 | `compare.py` — single-axis sweep (§6.3) | Side-by-side configuration inspection | **done** |
| 7 | Saved-runs tab (§6.4) | Evidence reading at zero API cost | **done** |
| 8 | Provenance capture (§7.3) | Feeds `humanEvaluation/pool/` | **done** |

Step 1 before step 2 was deliberate: if page resolution had not held across all 25 documents, the overlay's design would have changed, and that is better known before anything is built on top of it.

**What was checked, and how.** The index assertion ran over all 25 chunk files. The UI was exercised headlessly with `streamlit.testing.v1.AppTest`: the script renders with no exceptions, the overlay opens from a chunk list, `→` advances the deck across a chunk boundary, and the 57-page NFAP chunk produces a 59-position deck whose breadcrumb reads `Chunk 2 of 3 · NFAP · page 51 of 217 · deck 2 of 59`. **Not exercised: any path that calls the LLM or Pinecone APIs** — retrieval, generation and comparison were not run against live services, so they are verified by construction (same call sites as `scripts/run_retrieval.py`) rather than by execution.

## 10. Decisions

| # | Decision | Resolution |
| --- | --- | --- |
| D1 | Which chunk text variant to show by default (§5.5) | Composed `text` — what the generator actually saw; a radio switches variants |
| D2 | PDF highlighting (§5.5) | Deferred; the markdown view highlights by line match, no `pymupdf` dependency |
| D3 | Keyboard shortcuts (§5.6) | Deferred until buttons are shown to be slow |
| D4 | Whether comparison mode may show judge scores (§6.3) | **No** |
| D5 | Whether the tool may write `config/pipeline.yaml` | **No** — overlay only (§1.2) |
| D6 | Where author run traces are written | `data/runs/<timestamp>__author.json`, same schema as experiments |
| D7 | Whether to ship presets / named conditions | **No** — a configuration is any combination of `pipeline.yaml` keys, identified by its hash (§4.5) |
| D8 | How comparison mode is specified without presets | Vary **one** key of the current config; one axis keeps the difference attributable (§6.3) |
