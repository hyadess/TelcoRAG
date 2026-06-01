"""Gemini embedder — uses google.genai's embed_content endpoint.

Spec: https://ai.google.dev/gemini-api/docs/embeddings

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

import math
import os
from typing import List, Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types

from config.settings import (
    EMBED_BATCH_SIZE,
    get_embedding_dimensions,
    get_embedding_index,
    get_embedding_model,
)
from core.registry import EMBEDDERS

from .base import BaseEmbedder

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# Default output dimensions per Gemini embedding model.
_DEFAULT_DIMS = {
    "gemini-embedding-001": 3072,
    "gemini-embedding-2": 3072,
}


def _l2_normalize(vec: List[float]) -> List[float]:
    """Divide by L2 norm so the vector lies on the unit sphere."""
    n = math.sqrt(sum(x * x for x in vec))
    if n == 0:
        return vec
    return [x / n for x in vec]


@EMBEDDERS.register("gemini")
class GeminiEmbedder(BaseEmbedder):
    batch_size = EMBED_BATCH_SIZE["gemini"]

    def __init__(self):
        super().__init__(
            model=get_embedding_model("gemini"),
            api_key=GEMINI_API_KEY,
            index_name=get_embedding_index("gemini"),
        )
        self._user_dims: Optional[int] = get_embedding_dimensions()

    def _initialize_client(self):
        return genai.Client(api_key=self.api_key)

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

    def _embed_documents_batch(self, texts: List[str]) -> List[List[float]]:
        res = self.client.models.embed_content(
            model=self.model,
            contents=texts,  # list — returns one embedding per input
            config=self._embed_config("RETRIEVAL_DOCUMENT"),
        )
        vectors = [e.values for e in res.embeddings]
        if self._needs_manual_normalization():
            vectors = [_l2_normalize(v) for v in vectors]
        return vectors

    def _get_query_embedding(self, text: str) -> List[float]:
        res = self.client.models.embed_content(
            model=self.model,
            contents=text,
            config=self._embed_config("RETRIEVAL_QUERY"),
        )
        vec = res.embeddings[0].values
        if self._needs_manual_normalization():
            vec = _l2_normalize(vec)
        return vec
