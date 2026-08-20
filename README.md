# TelcoRAG

A pluggable Retrieval-Augmented Generation system for legal/regulatory documents.
Built around a three-stage pipeline (extract → index → retrieve) where every
component — embedder, query operator, retriever, reranker, judge module — is a
single file you swap by editing one line of YAML.

The system ships preconfigured for Bangladesh telecom regulations, but the
domain is fully decoupled from code: change `config/domain.yaml` and the prompts
adapt.

---

## Why use this

- **Plugin-first.** Adding a strategy is one decorated class + one YAML edit.
- **Prompts are files.** Every prompt is a Jinja template in `prompts/`; few-shot
  examples are YAML in `prompt_examples/`. Edit either without touching code.
- **One clean indexing convention.** A single `baseline` chunker: the dense
  vector embeds *document summary + chapter/section headers + subsection text*;
  BM25 indexes the *subsection text only*. No enrichment step.
- **Query reformulation as four composable operators** — `decompose`,
  `diversify`, `abstract`, `hyde` — organised by the retrieval failure mode each
  addresses (plus a `simple` control).
- **Structure-aware retrieval.** A `hierarchical` retriever filters coarse-to-fine
  down a configurable hierarchy (**document → chapter → section**) and then
  expands hits two ways: **sibling** expansion (missed subsections of a kept
  section) and **neighbour** expansion (splice in the reading-order prev/next
  chunks of a partially-relevant hit).
- **Two-call (corrective) retrieval.** After round 1, an LLM checks the query
  against what was retrieved and, if something's missing, issues follow-up
  queries for a second round — merged and reranked against the main query.
- **Full run traces + a Streamlit viewer.** Every run is saved as one JSON
  capturing config and, per query, the reformulations, per-variant retrieved
  chunks, gap analysis, reranked and final chunks, and the answer. Browse it all
  in `app.py`.
- **Modular experiment sweeps + LLM-as-a-judge** with a single ranked leaderboard.

---

## Project structure

```
TelcoRAG/
├── .env.example               # documented environment variables (copy to .env)
├── app.py                     # ← Streamlit run/trace viewer (streamlit run app.py)
├── config/
│   ├── pipeline.yaml          # ← STRATEGY CHOICES (edit me)
│   ├── domain.yaml            # ← DOMAIN WORDING (edit me for non-telecom)
│   └── settings.py            # internal constants + path/namespace helpers
│
├── prompts/                   # ALL prompts as .j2 files
│   ├── extraction/   document_metadata, page_analysis, subsection_summary
│   ├── query/        decompose, diversify, abstract, hyde, gap_analysis
│   ├── generation/   answer.j2
│   └── judge/        context_relevance, context_sufficiency, faithfulness,
│                     answer_correctness, answer_relevance, pairwise
│
├── prompt_examples/           # ← FEW-SHOT EXAMPLES as YAML (edit me)
│
├── core/                      # plugin registry + prompt loader + schemas
│
├── clients/                   # gemini, pinecone, cohere, voyage
│
├── pipeline/
│   ├── tracing.py             # QueryTrace + RunRecorder (full intermediate logs)
│   ├── stage1_extraction/     # parser → extractor → orchestrator (no enrichment)
│   ├── stage2_indexing/
│   │   ├── chunkers/          # baseline chunker (+ base)
│   │   ├── sequencing.py      # assigns reading-order neighbour ids per chunk
│   │   ├── bm25_index.py
│   │   ├── embedders/
│   │   └── orchestrator.py
│   └── stage3_retrieval/
│       ├── query_strategies/  # simple, decompose, diversify, abstract, hyde
│       ├── retrievers/        # vector, bm25, hybrid, hierarchical (+ hierarchical_ops)
│       ├── rerankers/         # voyage, cohere, rrf, llm, none
│       ├── refinement.py      # two-call gap analysis
│       ├── post_processing.py # dedupe, MMR, relevance filter
│       ├── generator.py       # final answer LLM call
│       └── orchestrator.py    # the pipeline (single-call + two-call, traced)
│
├── evaluation/judge/          # LLM-as-a-judge (one file per metric)
├── scripts/
│   ├── common.py              # shared query-loading + run loop
│   ├── run_ingestion.py
│   ├── run_retrieval.py       # → data/runs/run_<ts>.json (viewable in app.py)
│   └── run_experiments.py     # modular sweep + leaderboard
├── tests_offline.py           # offline smoke test (no keys/network)
└── experiment.md
```

---

## Setup

Create an isolated environment, install the full dependency set, and copy the
environment template. The application loads `.env` automatically.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Fill only the provider keys your configuration uses:

| Variable | Needed for |
| --- | --- |
| `PINECONE_API_KEY` | Dense vector indexing and retrieval |
| `GOOGLE_CLOUD_PROJECT` | Vertex AI project for Gemini calls |
| `GOOGLE_CLOUD_LOCATION` | Vertex AI region, such as `global` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Absolute path to a Google credential JSON file with Vertex AI access |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Complete service-account JSON for secret-based cloud deployments |
| `GCP_PROJECT_NUMBER`, `GCP_SERVICE_ACCOUNT_EMAIL`, `GCP_WORKLOAD_IDENTITY_POOL_ID`, `GCP_WORKLOAD_IDENTITY_POOL_PROVIDER_ID` | Keyless Vercel authentication through Google Workload Identity Federation |
| `LLAMAPARSE_API_KEYPOOL` | PDF-to-Markdown ingestion; use a Python-style list such as `['key']` |
| `OPENAI_API_KEY` | OpenAI embeddings |
| `COHERE_API_KEY` | Cohere embeddings or reranking |
| `VOYAGE_API_KEY` | Voyage embeddings or reranking |
| `PERPLEXITY_API_KEY` | Perplexity embeddings |

Never commit `.env`; it is ignored by Git. `.env.example` intentionally contains
names and placeholders only.

### First run

1. Put source PDFs in `resources/` (or pass a different folder with
   `--pdf-dir`).
2. Review `config/pipeline.yaml` and ensure its provider keys are present.
3. Run ingestion once, then retrieval:

```bash
python -m scripts.run_ingestion
python -m scripts.run_retrieval
streamlit run app.py
```

Ingestion writes extracted artifacts under `knowledge_base/documents/`, dense
vectors with compact structural metadata to Pinecone, and the sparse BM25 index
to `.cache/`. Chunk text (`subsection_text`, `full_subsection_text`, and
`bm25_text`) stays in the local `structured_output_chunks__<chunker>.json`
files; dense retrieval enriches Pinecone matches from those files by stable
chunk ID before reranking or generation. Successful dense uploads are recorded
per index, namespace, and document in
`.cache/pinecone_ingestion_tracker.json`; unchanged documents are skipped on
later ingestion runs. Retrieval reads
queries from `data/good_queries.csv`, writes `data/responses.csv`, and saves a
self-contained trace under `data/runs/`.

If you manually delete the selected Pinecone index, force a complete embedding
rebuild (while still reusing parsed, extracted, and chunked files) with:

```bash
python -m scripts.run_ingestion --reindex
```

Freshly recreated Pinecone indexes are also detected automatically and their
stale tracker entries are cleared.

---

## Configuring the pipeline

Open `config/pipeline.yaml`:

```yaml
embedder:        voyage        # openai | gemini | cohere | voyage | perplexity
chunker:         baseline      # baseline (single indexing convention)
query_strategy:  decompose     # simple | decompose | diversify | abstract | hyde
retriever:       hierarchical  # vector | bm25 | hybrid | hierarchical
reranker:        voyage        # voyage | cohere | rrf | llm | none

two_call:
  enabled: false               # turn on corrective second-round retrieval

post_processing:
  - dedupe
  - relevance_filter
```

List what's available for any field:

```python
from core.registry import (EMBEDDERS, CHUNKERS, QUERY_STRATEGIES,
                            RETRIEVERS, RERANKERS, discover_plugins)
discover_plugins()
print(CHUNKERS.list())         # ['baseline']
print(QUERY_STRATEGIES.list()) # ['abstract', 'decompose', 'diversify', 'hyde', 'simple']
print(RETRIEVERS.list())       # ['bm25', 'hierarchical', 'hybrid', 'vector']
print(RERANKERS.list())        # ['cohere', 'llm', 'none', 'rrf', 'voyage']
```

---

## Query reformulation operators

Four operator families, each targeting one retrieval failure mode (plus a
control). Selected via `query_strategy:`.

| Operator | Family | Failure mode it addresses |
| --- | --- | --- |
| `simple` | — (control) | baseline passthrough |
| `decompose` | decomposition | multi-aspect queries → focused sub-queries |
| `diversify` | diversification | vocabulary mismatch → semantically equivalent variants |
| `abstract` | abstraction | overly specific queries → recover the governing rule |
| `hyde` | hypothetical expansion | weak semantic signal → embed a synthetic answer |

Each operator's prompt lives in `prompts/query/<name>.j2` and its few-shot
examples in `prompt_examples/<name>.yaml`. The operators emit 1..N query
variants; the retriever runs all of them and the results are merged.

---

## Retrievers

| Retriever | When it helps |
| --- | --- |
| `vector` | Default dense search. |
| `bm25` | Exact regulatory terms (`ICX`, `section 4.05`). |
| `hybrid` | Dense + BM25 fused via Reciprocal Rank Fusion. |
| `hierarchical` | Structure-aware. Filters document → chapter → section, then sibling- and neighbour-expands. Best when answers span adjacent subsections. |

### Hierarchical retriever (configurable, modular)

Three independent, fully configurable stages under `pipeline.yaml → hierarchical`:

1. **Multi-level filtering.** `levels` is an ordered list (outermost first) of
   `{field, top_n}`. The default keeps the top documents, then the top chapters
   within them, then the top sections within those:

   ```yaml
   levels:
     - {field: doc_name, top_n: 3}
     - {field: chapter,  top_n: 4}
     - {field: section,  top_n: 5}
   ```
   Drop or reorder levels freely (e.g. keep only `section` for the old
   section-only behaviour, or drop `doc_name` for a single-document KB).

2. **Sibling expansion** (`expand_siblings`): per surviving section, a
   metadata-filtered query surfaces relevant subsections the flat pool missed.

3. **Neighbour expansion** (`expand_neighbors`): for a hit whose relevance is
   *medium* (between `neighbor_low` and `neighbor_high`), score its reading-order
   neighbours (prev/next, up to `neighbor_max_hops`) and splice the contiguous
   ones that clear `neighbor_moderate` into the hit (standard continuation:
   prev2, prev1, hit, next1, next2). High-relevance hits already contain the
   answer; very low ones don't — neither is expanded. All thresholds are cosine
   similarities and are configurable.

The scoring/grouping/decision logic is pure (`retrievers/hierarchical_ops.py`)
and unit-tested in `tests_offline.py`.

---

## Two-call (corrective) retrieval

Set `two_call.enabled: true`. After the normal round-1 retrieval, the
gap-analysis LLM (`prompts/query/gap_analysis.j2`) judges the **main** query
against the retrieved chunks. If it reports missing information, it returns
focused follow-up queries; each is reformulated by the chosen operator (so
multi-query operators fan out again), retrieved, merged in, and the whole set is
reranked against the main query. Degrades safely to single-call if the LLM call
fails. Works with any retriever and any operator.

---

## Run traces & the Streamlit viewer

`run_retrieval.py` and each experiment combo write a single self-contained JSON
(`data/runs/run_<timestamp>.json`, and `data/experiments/<combo>/run.json`)
recording the run config and, per query: the reformulated variants and the
chunks each retrieved, the two-call gap analysis and round-2 follow-ups, the
reranked chunks, the post-processed final chunks, and the final answer.

```bash
streamlit run app.py
```

The viewer lets you pick any run and step through every query's pipeline stages,
with score bars, hierarchy ranks, and badges marking sibling/neighbour-expanded
chunks. A bundled `data/runs/sample_demo.json` lets you explore the UI before
running anything.

---

## Switching domains

Edit `config/domain.yaml` (`domain`, `expert_role`, `document_type`,
`terminology_hints`). The values flow into every prompt. No code change.

---

## Evaluation

Create `data/reference_answers.csv` from
`data/reference_answers_template.csv` when reference-based correctness scores
are required, then run:

```bash
python -m scripts.run_experiments --dry-run
python -m scripts.run_experiments --limit 10
```

The generation composite contains three non-overlapping signals:

- `faithfulness`: whether claims are supported by retrieved context;
- `correctness`: whether factual claims agree with the expert reference;
- `answer_relevance`: whether the response addresses the question.

Correctness deliberately does not score completeness or relevance. Missing
references produce a not-evaluated score (`0`) and are excluded from composite
averages. See `experiment.md` for sweep configuration and output layout.

---

## Testing

```bash
python tests_offline.py
```

Stubs the vendor SDKs and verifies the plugin wiring, the baseline chunker's
embed/BM25 text, chunk sequencing, multi-level hierarchy filtering, the
neighbour-expansion decision logic, the hierarchical retriever's sibling +
neighbour expansion end-to-end, and the two-call gap-analysis fallback — all
without API keys or network.

---

## Troubleshooting

- **Missing credentials:** the selected client reports the exact missing
  API key or Vertex AI variable. Compare `.env` with `.env.example`.
- **BM25 index missing:** run ingestion with the same `chunker` before using
  `bm25` or `hybrid` retrieval.
- **Pinecone dimension mismatch:** a changed embedding model or
  `embedding_dimensions` value needs an index with matching dimensions. Index
  names are defined in `config/settings.py` to prevent accidental cross-model
  reuse.
- **No correctness score:** add a query-matched row to
  `data/reference_answers.csv`; matching trims surrounding whitespace but
  otherwise uses the query text exactly.

---

## What's NOT included

Persisted multi-tenant history or authentication. This is a backend pipeline
plus a local viewer; clients read API keys from `.env`.
