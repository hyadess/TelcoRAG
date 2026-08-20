"""
Internal settings — code-level constants that rarely change.

User-facing strategy choices live in `config/pipeline.yaml`.
Domain-specific wording lives in `config/domain.yaml`.

This file holds:
  - default model identifiers and Pinecone index names (overridable from YAML)
  - file paths
  - cache file locations
  - helpers `get_embedding_model()` / `get_reranker_model()` that look up the
    YAML override first and fall back to the defaults here.

Settings are loaded once at import time and exposed as a singleton `SETTINGS`.
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


# =============================================================================
# Project paths
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
PROMPTS_DIR = PROJECT_ROOT / "prompts"
PROMPT_EXAMPLES_DIR = PROJECT_ROOT / "prompt_examples"
CACHE_DIR = (
    Path(tempfile.gettempdir()) / "telcorag-cache"
    if os.getenv("VERCEL")
    else PROJECT_ROOT / ".cache"
)
CACHE_DIR.mkdir(exist_ok=True)


# =============================================================================
# Default model identifiers (overridable from pipeline.yaml -> models.*)
# =============================================================================

# Vertex AI model ID used for extraction, generation, reformulation, and judges.
GEMINI_MODEL = "gemini-3.6-flash"

# Default embedding models + matching Pinecone indexes.
# The `model` here is a fallback when pipeline.yaml's `models.embedding.<name>`
# is unset. The index name is NOT overridable from YAML — it stays here so a
# model swap doesn't accidentally point at the wrong Pinecone index.
EMBEDDING_CONFIGS: Dict[str, Dict[str, str]] = {
    "openai": {
        "model": "text-embedding-3-large",
        "index": "telco-openai-index",
    },
    "gemini": {
        "model": "gemini-embedding-001",
        "index": "telco-gemini-index",
    },
    "cohere": {
        "model": "embed-multilingual-v3.0",
        "index": "telco-cohere-index",
    },
    "voyage": {
        "model": "voyage-law-2",
        "index": "telco-voyage-index",
    },
    "perplexity": {
        "model": "pplx-embed-v1-4b",
        "index": "telco-perplexity-index",
    },
}

# Default reranker models.
RERANKER_CONFIGS: Dict[str, str] = {
    "cohere": "rerank-v3.5",
    "voyage": "rerank-2.5",
}


# =============================================================================
# Provider-specific batch sizes (each vendor has different per-call caps)
# =============================================================================

# These match the per-call limits documented at:
#   OpenAI:     up to 2048 inputs per request; 100 keeps tokens-per-request safe.
#   Cohere:     hard cap of 96 texts per call for embed v3+.
#   Voyage:    1000-text list cap; total tokens vary by model — 64 is safe.
#   Gemini:     64 lowers per-call token pressure; adaptive fallback shrinks it.
#   Perplexity: max 512 texts per call, 120k total tokens.
EMBED_BATCH_SIZE: Dict[str, int] = {
    "openai": 100,
    "cohere": 96,
    "voyage": 64,
    "gemini": 64,
    "perplexity": 100,
}


# =============================================================================
# File paths (relative to project root)
# =============================================================================

QUERIES_FILE = DATA_DIR / "good_queries.csv"
RESPONSES_FILE = DATA_DIR / "responses.csv"
REFERENCE_FILE = DATA_DIR / "reference_answers.csv"
CHUNKS_DUMP_FILE = DATA_DIR / "retrieved_chunks.json"
JUDGE_OUTPUT_FILE = DATA_DIR / "llm_judge_results.csv"
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "knowledge_base" / "documents"
BM25_INDEX_FILE = CACHE_DIR / "bm25_index.pkl"

# Per-run intermediate-trace artifacts (configs, per-query reformulations,
# retrieved/reranked/expanded chunks, two-call gap analysis, final answers).
# These are the JSON files the Streamlit viewer reads.
RUNS_DIR = DATA_DIR / "runs"


def bm25_index_path(chunker: Optional[str] = None) -> Path:
    """Return the BM25 index file for a given chunker variant.

    Each chunker indexes a corpus text; a distinct pickle per chunker keeps
    multiple indexing conventions isolated. The legacy
    ``BM25_INDEX_FILE`` is returned when no chunker is given, so old call
    sites keep working.
    """
    if not chunker:
        return BM25_INDEX_FILE
    safe = str(chunker).strip().lower().replace("/", "_")
    return CACHE_DIR / f"bm25_index__{safe}.pkl"


def chunk_namespace(chunker: Optional[str] = None) -> str:
    """Pinecone namespace used to isolate one chunker's dense vectors.

    A chunker's vectors live in its own namespace so multiple indexing
    conventions can coexist without mixing. Empty string == Pinecone's default
    namespace (used when no chunker is specified).
    """
    if not chunker:
        return ""
    return str(chunker).strip().lower().replace("/", "_")

# Reranker caches
COHERE_CACHE_FILE = CACHE_DIR / "cache_cohere.pkl"
VOYAGE_CACHE_FILE = CACHE_DIR / "cache_voyage.pkl"


# =============================================================================
# Pipeline & domain config — loaded from YAML
# =============================================================================

def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config file missing: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


class Settings:
    """Lazy-loaded singleton wrapping the YAML configs."""

    def __init__(self):
        self._pipeline: Dict[str, Any] = {}
        self._domain: Dict[str, Any] = {}
        self._loaded = False

    def _ensure_loaded(self):
        if not self._loaded:
            self._pipeline = _load_yaml(CONFIG_DIR / "pipeline.yaml")
            self._domain = _load_yaml(CONFIG_DIR / "domain.yaml")
            self._loaded = True

    @property
    def pipeline(self) -> Dict[str, Any]:
        self._ensure_loaded()
        return self._pipeline

    @property
    def domain(self) -> Dict[str, Any]:
        self._ensure_loaded()
        return self._domain

    def reload(self):
        """Force a re-read of the YAML files (useful in notebooks)."""
        self._loaded = False
        self._ensure_loaded()


SETTINGS = Settings()


# =============================================================================
# Public helpers — embedders/rerankers call these instead of reading dicts
# directly, so a YAML override transparently wins over the defaults above.
# =============================================================================

def get_embedding_model(provider: str) -> str:
    """Return the active model name for an embedding provider.

    Resolution order:
      1. pipeline.yaml -> models.embedding.<provider>   (if non-empty)
      2. EMBEDDING_CONFIGS[<provider>]["model"]          (default fallback)
    """
    yaml_models = SETTINGS.pipeline.get("models", {}).get("embedding", {}) or {}
    override = yaml_models.get(provider)
    if override:
        return str(override).strip()
    if provider not in EMBEDDING_CONFIGS:
        raise KeyError(f"Unknown embedding provider: {provider!r}")
    return EMBEDDING_CONFIGS[provider]["model"]


def get_chunker_name() -> str:
    """Active chunker from pipeline.yaml -> chunker (default: baseline)."""
    return str(SETTINGS.pipeline.get("chunker", "baseline")).strip().lower()


def get_reranker_model(provider: str) -> str:
    """Same idea as get_embedding_model() but for rerankers."""
    yaml_models = SETTINGS.pipeline.get("models", {}).get("reranking", {}) or {}
    override = yaml_models.get(provider)
    if override:
        return str(override).strip()
    if provider not in RERANKER_CONFIGS:
        raise KeyError(f"Unknown reranker provider: {provider!r}")
    return RERANKER_CONFIGS[provider]


def get_embedding_dimensions() -> Optional[int]:
    """User-configured MRL output_dimensionality override (or None for default)."""
    val = SETTINGS.pipeline.get("embedding_dimensions")
    if val in (None, "", "null"):
        return None
    return int(val)


def get_embedding_request_delay(provider: str) -> float:
    """Minimum pause, in seconds, between embedding API calls.

    Providers enforce different quotas, so this is configured per provider in
    ``pipeline.yaml``. A missing provider entry means no artificial delay.
    """
    delays = SETTINGS.pipeline.get("embedding_request_delay_seconds", {}) or {}
    val = delays.get(provider, 0) if isinstance(delays, dict) else delays
    delay = float(val or 0)
    if delay < 0:
        raise ValueError("embedding_request_delay_seconds cannot be negative")
    return delay


def get_embedding_index(provider: str) -> str:
    """Pinecone index name for a provider — not YAML-overridable on purpose."""
    if provider not in EMBEDDING_CONFIGS:
        raise KeyError(f"Unknown embedding provider: {provider!r}")
    return EMBEDDING_CONFIGS[provider]["index"]
