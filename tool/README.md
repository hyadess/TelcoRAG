# TelcoRAG feedback tool

This folder contains a Streamlit chat frontend and a FastAPI/PostgreSQL backend.
Every generated response and its retrieved subsections are persisted. A rater
can score retrieval relevance, completeness, and correctness from 1–5, add a
comment, and later update that rating. The admin view summarizes the scores.

## Configuration

The tool's retriever is selected in `tool/settings.py` with `RETRIEVER_NAME`.
It can also be overridden at runtime with `TELCORAG_RETRIEVER`. Valid values are
`vector`, `bm25`, `hybrid`, and `hierarchical`.

Copy the root `.env.example` to the root `.env` and set the required values
there. All pipeline, backend, synchronization, and local frontend commands read
that same file. Set `TELCORAG_ADMIN_PASSWORD` in production; when it is empty,
the analytics endpoint is intentionally open for local use.

## Run locally

From the repository root:

```bash
pip install -r requirements.txt -r tool/requirements.txt
docker-compose -f tool/docker-compose.yml up -d
uvicorn tool.backend.main:app --reload
```

This project uses the standalone `docker-compose` command. If your Docker
installation includes the Compose v2 plugin, the equivalent command is
`docker compose -f tool/docker-compose.yml up -d`.

In another terminal:

```bash
PYTHONPATH=. streamlit run tool/frontend/app.py
```

Run this command from the repository root. Setting `PYTHONPATH=.` makes the
top-level `tool` package available to Streamlit and prevents
`ModuleNotFoundError: No module named 'tool'`.

Open `http://localhost:8501`. FastAPI documentation is available at
`http://localhost:8000/docs`.

Tables are created on backend startup. For a larger deployment, replace
`create_all` with Alembic migrations and run one backend worker per process;
the pipeline is initialized lazily on the first chat request.

## Supabase upload and updates

Supabase stores feedback data plus the retrieval files that Vercel cannot read
from this machine. Pinecone still stores vectors. Supabase stores the full chunk
text and a compressed copy of each BM25 index.

### 1. Configure the database locally

Copy Supabase's **Transaction pooler** URI (port 6543) into the repository's
ignored `.env` file. Change only the URI scheme from `postgresql://` to
`postgresql+psycopg://` and replace the password placeholder:

```dotenv
DATABASE_URL=postgresql+psycopg://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres?sslmode=require
```

Do not commit `.env` or paste the password into source files.

### 2. Run the synchronization

From the repository root:

```bash
python -m scripts.sync_supabase_chunks --chunker baseline
```

The first run creates and fills:

- `chunk_baseline`: full text from every
  `structured_output_chunks__baseline.json` file.
- `chunk_upload_tracker`: source path, SHA-256 fingerprint, size, row count,
  and last upload time for every synchronized JSON file.
- `chunk_artifacts`: the gzip-compressed `.cache/bm25_index__baseline.pkl`.
- `chat_responses` and `ratings`: application feedback tables.

Run the same command whenever files are added or regenerated. New files are
uploaded, changed files are replaced, and unchanged files are skipped. A file
that is absent locally is retained remotely by default. To delete rows for
tracked files that were intentionally removed, run:

```bash
python -m scripts.sync_supabase_chunks --chunker baseline --prune-missing
```

Rebuild the matching BM25 pickle before synchronizing whenever chunk JSON
content changes. The synchronizer fingerprints the pickle and uploads it only
when it changed.

### Other chunking methods

Each chunking method gets an independent table and BM25 artifact. For a chunker
named `semantic`, the expected files are:

```text
knowledge_base/documents/**/structured_output_chunks__semantic.json
.cache/bm25_index__semantic.pkl
```

Synchronize it with:

```bash
python -m scripts.sync_supabase_chunks --chunker semantic
```

This creates `chunk_semantic`. To discover and synchronize every chunker variant
currently present under `knowledge_base/documents`, run:

```bash
python -m scripts.sync_supabase_chunks --all-chunkers
```

## Deploy the backend and frontend

Import the repository into Vercel. Configure these backend variables:

```dotenv
DATABASE_URL=postgresql+psycopg://...
TELCORAG_CHUNK_STORE=database
TELCORAG_CHUNKER=baseline
TELCORAG_RETRIEVER=vector
```

Also configure the Pinecone and selected model-provider credentials described
in `.env.example`. For `bm25` or `hybrid`, Vercel downloads the matching BM25
artifact from Supabase into its temporary cache on the first query. Dense and
hierarchical retrieval read matching full text from `chunk_<chunker>`.

In Streamlit Community Cloud, deploy `tool/frontend/app.py` and set:

```toml
TELCORAG_BACKEND_URL = "https://YOUR-BACKEND.vercel.app"
TELCORAG_ADMIN_PASSWORD = "YOUR-ADMIN-PASSWORD"
```
