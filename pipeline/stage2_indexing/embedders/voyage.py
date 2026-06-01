"""Voyage AI embedder.

Spec: https://docs.voyageai.com/docs/embeddings

- `Client.embed(texts, model, input_type, output_dimension=None)` accepts up
  to 1,000 texts per call (with a total-token budget per model). The previous
  implementation looped one text at a time, which both slow and rate-limit
  prone — fixed via base-class batching.
- Voyage 3.x and 4.x models support MRL truncation via `output_dimension`.
  Older legal/finance models (`voyage-law-2`, `voyage-finance-2`) are fixed
  at 1024 — we only forward `output_dimension` when the model supports it.
"""

import os
from typing import List, Optional

from dotenv import load_dotenv

from config.settings import (
    EMBED_BATCH_SIZE,
    get_embedding_dimensions,
    get_embedding_index,
    get_embedding_model,
)
from core.registry import EMBEDDERS

from .base import BaseEmbedder

load_dotenv()
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")


# Native (non-MRL) dimensions per Voyage model.
_NATIVE_DIMS = {
    "voyage-4-large": 1024,
    "voyage-4": 1024,
    "voyage-4-lite": 1024,
    "voyage-3-large": 1024,
    "voyage-3.5": 1024,
    "voyage-3.5-lite": 1024,
    "voyage-3": 1024,
    "voyage-3-lite": 512,
    "voyage-code-3": 1024,
    "voyage-finance-2": 1024,
    "voyage-law-2": 1024,
    "voyage-multilingual-2": 1024,
    "voyage-large-2": 1536,
    "voyage-2": 1024,
}

# Models that accept the `output_dimension` MRL knob.
_MRL_MODELS = {
    "voyage-4-large", "voyage-4", "voyage-4-lite",
    "voyage-3-large", "voyage-3.5", "voyage-3.5-lite",
    "voyage-code-3",
}


@EMBEDDERS.register("voyage")
class VoyageEmbedder(BaseEmbedder):
    batch_size = EMBED_BATCH_SIZE["voyage"]

    def __init__(self):
        super().__init__(
            model=get_embedding_model("voyage"),
            api_key=VOYAGE_API_KEY,
            index_name=get_embedding_index("voyage"),
        )
        self._user_dims: Optional[int] = get_embedding_dimensions()

    def _initialize_client(self):
        import voyageai
        return voyageai.Client(api_key=self.api_key)

    @property
    def dimension(self) -> int:
        if self._user_dims is not None and self.model in _MRL_MODELS:
            return self._user_dims
        # Fall back to the native dim; default to 1024 if we don't recognize
        # the model (Voyage's modern defaults all land there).
        return _NATIVE_DIMS.get(self.model, 1024)

    # ------------------------------------------------------------------

    def _embed_kwargs(self) -> dict:
        kwargs = {"model": self.model}
        if self._user_dims is not None and self.model in _MRL_MODELS:
            kwargs["output_dimension"] = self._user_dims
        return kwargs

    def _embed_documents_batch(self, texts: List[str]) -> List[List[float]]:
        res = self.client.embed(texts, input_type="document", **self._embed_kwargs())
        return res.embeddings

    def _get_query_embedding(self, text: str) -> List[float]:
        res = self.client.embed([text], input_type="query", **self._embed_kwargs())
        return res.embeddings[0]
