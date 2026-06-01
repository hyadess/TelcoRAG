"""Perplexity AI embedder.

Spec: https://docs.perplexity.ai/docs/embeddings/standard-embeddings

Two model options:
  - pplx-embed-v1-0.6b → 1024 dims, MRL down to 128
  - pplx-embed-v1-4b   → 2560 dims, MRL down to 128

Quirk to be aware of: Perplexity returns embeddings as **base64-encoded
signed int8 arrays** (their `encoding_format` default is `base64_int8`).
We decode them back to float32 lists so they're compatible with Pinecone's
cosine metric and the rest of the pipeline. Doing the decode here keeps the
weirdness contained to one file.

Perplexity has no reranker — pair this embedder with voyage/cohere/rrf/llm/none
(see pipeline.yaml's compatibility table).
"""

import base64
import os
from typing import List, Optional

import numpy as np
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
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")


# Native (non-MRL) output dimensions per Perplexity embedding model.
_NATIVE_DIMS = {
    "pplx-embed-v1-0.6b": 1024,
    "pplx-embed-v1-4b": 2560,
}


def _decode_int8_b64(b64_string: str) -> List[float]:
    """Decode Perplexity's base64-encoded signed-int8 embedding to float32 list."""
    raw = base64.b64decode(b64_string)
    vec = np.frombuffer(raw, dtype=np.int8).astype(np.float32)
    return vec.tolist()


@EMBEDDERS.register("perplexity")
class PerplexityEmbedder(BaseEmbedder):
    batch_size = EMBED_BATCH_SIZE["perplexity"]

    def __init__(self):
        super().__init__(
            model=get_embedding_model("perplexity"),
            api_key=PERPLEXITY_API_KEY,
            index_name=get_embedding_index("perplexity"),
        )
        self._user_dims: Optional[int] = get_embedding_dimensions()

    def _initialize_client(self):
        from perplexity import Perplexity
        return Perplexity(api_key=self.api_key)

    @property
    def dimension(self) -> int:
        if self._user_dims is not None:
            return self._user_dims
        return _NATIVE_DIMS.get(self.model, 2560)

    # ------------------------------------------------------------------

    def _embed_kwargs(self) -> dict:
        kwargs = {"model": self.model}
        if self._user_dims is not None:
            kwargs["dimensions"] = self._user_dims
        return kwargs

    def _embed_documents_batch(self, texts: List[str]) -> List[List[float]]:
        # Perplexity rejects empty strings — catch up-front for a clear error.
        for t in texts:
            if not t or not t.strip():
                raise ValueError("Empty text passed to Perplexity embedder")

        response = self.client.embeddings.create(input=texts, **self._embed_kwargs())
        # Response.data preserves input order; each entry has a base64 string.
        return [_decode_int8_b64(e.embedding) for e in response.data]

    def _get_query_embedding(self, text: str) -> List[float]:
        return self._embed_documents_batch([text])[0]
