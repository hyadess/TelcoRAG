"""Vertex AI Gemini embedder — uses google.genai's embed_content endpoint.

Spec: https://cloud.google.com/vertex-ai/generative-ai/docs/embeddings/get-text-embeddings

Important fixes over the previous implementation:

1. **task_type** — `gemini-embedding-001` accepts `RETRIEVAL_DOCUMENT` (for
   indexed chunks) and `RETRIEVAL_QUERY` (for searches). Specifying these
   meaningfully improves retrieval quality vs. leaving it unset.

2. **Batching** — `embed_content` accepts a list of strings and returns a
   list of embeddings (one per input). The previous code looped one call
   per text, which is both slow and rate-limit-prone.

3. **Manual normalization for truncated outputs** — only `gemini-embedding-2`
   auto-normalizes when `output_dimensionality < 3072`. For
   `gemini-embedding-001`, the docs explicitly say you must normalize yourself
   if you ask for fewer dimensions, otherwise cosine math goes off.
"""

import logging
import math
import threading
import time
from typing import List, Optional

from google.genai import types

from clients.gemini import create_vertex_client
from config.settings import (
    EMBED_BATCH_SIZE,
    get_embedding_dimensions,
    get_embedding_index,
    get_embedding_model,
    get_embedding_request_delay,
)
from core.registry import EMBEDDERS

from .base import BaseEmbedder

# Default output dimensions per Gemini embedding model.
_DEFAULT_DIMS = {
    "gemini-embedding-001": 3072,
    "gemini-embedding-2": 3072,
}

logger = logging.getLogger("GeminiEmbedder")


def _l2_normalize(vec: List[float]) -> List[float]:
    """Divide by L2 norm so the vector lies on the unit sphere."""
    n = math.sqrt(sum(x * x for x in vec))
    if n == 0:
        return vec
    return [x / n for x in vec]


@EMBEDDERS.register("gemini")
class GeminiEmbedder(BaseEmbedder):
    batch_size = EMBED_BATCH_SIZE["gemini"]

    # Shared across instances so consecutive ingestion/experiment runs in the
    # same process cannot independently burst against the same Vertex quota.
    _request_lock = threading.Lock()
    _last_request_finished_at = 0.0

    def __init__(self):
        super().__init__(
            model=get_embedding_model("gemini"),
            # Vertex AI authenticates with Google credentials, not an API key.
            api_key="",
            index_name=get_embedding_index("gemini"),
        )
        self._user_dims: Optional[int] = get_embedding_dimensions()
        self._request_delay_seconds = get_embedding_request_delay("gemini")

    def _initialize_client(self):
        return create_vertex_client()

    @property
    def dimension(self) -> int:
        if self._user_dims is not None:
            return self._user_dims
        return _DEFAULT_DIMS.get(self.model, 3072)

    # ------------------------------------------------------------------

    def _is_v1(self) -> bool:
        """gemini-embedding-001 takes `task_type` and doesn't auto-normalize."""
        return self.model == "gemini-embedding-001"

    def _needs_manual_normalization(self) -> bool:
        """Only v1 with a truncated dim needs us to normalize manually."""
        if not self._is_v1():
            return False
        return self._user_dims is not None and self._user_dims < _DEFAULT_DIMS[self.model]

    def _embed_config(self, task_type: str) -> types.EmbedContentConfig:
        kwargs = {}
        if self._user_dims is not None:
            kwargs["output_dimensionality"] = self._user_dims
        # `task_type` is only valid for gemini-embedding-001. For v2 the task
        # is expressed as a prefix in the prompt (we don't add a prefix here
        # to keep behaviour comparable across models; tweak if you need it).
        if self._is_v1():
            kwargs["task_type"] = task_type
        return types.EmbedContentConfig(**kwargs)

    def _embed_content(self, *, contents, task_type: str):
        """Call Vertex AI while maintaining a minimum gap between requests."""
        cls = type(self)
        with cls._request_lock:
            elapsed = time.monotonic() - cls._last_request_finished_at
            wait_seconds = max(0.0, self._request_delay_seconds - elapsed)
            if wait_seconds:
                logger.info(
                    "Waiting %.1f seconds before the next Gemini embedding request",
                    wait_seconds,
                )
                time.sleep(wait_seconds)

            try:
                return self.client.models.embed_content(
                    model=self.model,
                    contents=contents,
                    config=self._embed_config(task_type),
                )
            finally:
                # Pace from completion rather than request start; this guarantees
                # a real quiet interval even when Vertex responds very quickly.
                cls._last_request_finished_at = time.monotonic()

    def _embed_documents_batch(self, texts: List[str]) -> List[List[float]]:
        res = self._embed_content(
            contents=texts,  # list — returns one embedding per input
            task_type="RETRIEVAL_DOCUMENT",
        )
        vectors = [e.values for e in res.embeddings]
        if self._needs_manual_normalization():
            vectors = [_l2_normalize(v) for v in vectors]
        return vectors

    def _get_query_embedding(self, text: str) -> List[float]:
        res = self._embed_content(
            contents=text,
            task_type="RETRIEVAL_QUERY",
        )
        vec = res.embeddings[0].values
        if self._needs_manual_normalization():
            vec = _l2_normalize(vec)
        return vec
