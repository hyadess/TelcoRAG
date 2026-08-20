# TelcoRAG feedback tool

This folder contains a Streamlit chat frontend and a FastAPI/PostgreSQL backend.
Every generated response and its retrieved subsections are persisted. A rater
can score retrieval relevance, completeness, and correctness from 1–5, add a
comment, and later update that rating. The admin view summarizes the scores.

## Configuration

The tool's retriever is selected in `tool/settings.py` with `RETRIEVER_NAME`.
It can also be overridden at runtime with `TELCORAG_RETRIEVER`. Valid values are
`vector`, `bm25`, `hybrid`, and `hierarchical`.

Copy `tool/.env.example` values into the project's existing `.env` and set the
usual TelcoRAG provider credentials. Set `TELCORAG_ADMIN_PASSWORD` in production;
when it is empty, the analytics endpoint is intentionally open for local use.

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

## Deploy

The production layout uses Supabase PostgreSQL, Vercel for FastAPI, and
Streamlit Community Cloud for the UI.

1. Create a Supabase project and copy its transaction-pooler connection string
   (port 6543). Set it as `DATABASE_URL`, using the
   `postgresql+psycopg://` prefix.
2. From the repository root, seed the subsection text once:

   ```bash
   DATABASE_URL='postgresql+psycopg://...' python -m scripts.seed_supabase_chunks
   ```

3. Import the repository into Vercel. Set `DATABASE_URL`,
   `TELCORAG_CHUNK_STORE=database`, provider credentials, and the remaining
   `TELCORAG_*` values. Vercel loads `tool.backend.main:app` from
   `pyproject.toml`.
4. In Streamlit Community Cloud, deploy `tool/frontend/app.py`. Its only
   required secret is `TELCORAG_BACKEND_URL` pointing to the Vercel deployment;
   add `TELCORAG_ADMIN_PASSWORD` to enable the admin view.
