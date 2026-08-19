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
