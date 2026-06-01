"""OpenAI embedder — uses the /v1/embeddings endpoint.

Spec: https://developers.openai.com/api/docs/guides/embeddings
- `text-embedding-3-small` is 1536-d by default; `text-embedding-3-large` is 3072-d.
- Both v3 models accept an optional `dimensions` parameter (MRL truncation) to
  shrink the output vector without a big quality loss — useful when your vector
  DB caps you at e.g. 1024 dims.
- The `input` field accepts a list of strings, so we batch in one call.
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
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# OpenAI's stable embedding model dimensions when no MRL override is used.
_DEFAULT_DIMS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
}


@EMBEDDERS.register("openai")
class OpenAIEmbedder(BaseEmbedder):
    batch_size = EMBED_BATCH_SIZE["openai"]

    def __init__(self):
        super().__init__(
            model=get_embedding_model("openai"),
            api_key=OPENAI_API_KEY,
            index_name=get_embedding_index("openai"),
        )
        self._user_dims: Optional[int] = get_embedding_dimensions()

    def _initialize_client(self):
        from openai import OpenAI
        return OpenAI(api_key=self.api_key)

    @property
    def dimension(self) -> int:
        # If the user set an MRL override in pipeline.yaml, honor it.
        if self._user_dims is not None:
            return self._user_dims
        # Otherwise use the model's native dimension. Fall back to 1536 if
        # we encounter an unknown model name (better than crashing).
        return _DEFAULT_DIMS.get(self.model, 1536)

    # ------------------------------------------------------------------

    def _clean(self, text: str) -> str:
        # OpenAI's documented best practice is to strip newlines for stability.
        return text.replace("\n", " ")

    def _embed_documents_batch(self, texts: List[str]) -> List[List[float]]:
        # Validate up-front — OpenAI errors out on empty strings, and the error
        # message is unhelpful ("invalid input"). Catch it here with context.
        cleaned: List[str] = []
        for t in texts:
            c = self._clean(t)
            if not c.strip():
                raise ValueError("Empty text passed to OpenAI embedder")
            cleaned.append(c)

        kwargs = {"input": cleaned, "model": self.model}
        # `dimensions` is only valid on text-embedding-3-* models.
        if self._user_dims is not None and "3-" in self.model:
            kwargs["dimensions"] = self._user_dims

        response = self.client.embeddings.create(**kwargs)
        # The API guarantees response.data is in the same order as the input.
        return [d.embedding for d in response.data]

    def _get_query_embedding(self, text: str) -> List[float]:
        return self._embed_documents_batch([text])[0]
