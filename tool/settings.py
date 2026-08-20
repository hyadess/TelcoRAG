"""Configuration for the feedback tool.

The retriever used by the web application is intentionally selected here,
independently of ``config/pipeline.yaml``. Other pipeline components still use
the project's normal configuration unless overridden below.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


# Change this value to: vector | bm25 | hybrid | hierarchical
RETRIEVER_NAME = os.getenv("TELCORAG_RETRIEVER", "vector").strip().lower()

# Optional pipeline overrides. ``None`` means use config/pipeline.yaml.
EMBEDDER_NAME = os.getenv("TELCORAG_EMBEDDER") or None
QUERY_STRATEGY = os.getenv("TELCORAG_QUERY_STRATEGY") or None
RERANKER_NAME = os.getenv("TELCORAG_RERANKER") or None
CHUNKER_NAME = os.getenv("TELCORAG_CHUNKER") or None


@dataclass(frozen=True)
class ToolSettings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://telcorag:telcorag@localhost:5432/telcorag_feedback",
    )
    backend_url: str = os.getenv(
        "TELCORAG_BACKEND_URL", "http://localhost:8000"
    ).rstrip("/")
    admin_password: str = os.getenv("TELCORAG_ADMIN_PASSWORD", "")
    retrieval_top_k: int = int(os.getenv("TELCORAG_RETRIEVAL_TOP_K", "30"))
    rerank_top_k: int = int(os.getenv("TELCORAG_RERANK_TOP_K", "20"))
    request_timeout_seconds: int = int(os.getenv("TELCORAG_REQUEST_TIMEOUT", "180"))


SETTINGS = ToolSettings()
