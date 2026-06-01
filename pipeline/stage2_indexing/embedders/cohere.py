"""Cohere embedder — uses cohere.ClientV2.

Spec: https://docs.cohere.com/reference/embed

- Cohere v3+ caps each call at 96 texts. The base class auto-chunks because
  we set `batch_size = 96`.
- `input_type` is required for v3+ ("search_document" for indexed chunks,
  "search_query" for retrieval-time queries).
- `embedding_types=["float"]` is set explicitly so we always get raw floats
  (the response object also exposes int8, uint8, etc. for the same call).
"""

import os
from typing import List

from dotenv import load_dotenv

from config.settings import (
    EMBED_BATCH_SIZE,
    get_embedding_index,
    get_embedding_model,
)
from core.registry import EMBEDDERS

from .base import BaseEmbedder

load_dotenv()
COHERE_API_KEY = os.getenv("COHERE_API_KEY")


# Output dimensions per Cohere embedding model.
# (Cohere v3 has no MRL; v4 is fixed at 1536 unless you request quantization.)
_MODEL_DIMS = {
    "embed-multilingual-v3.0": 1024,
    "embed-english-v3.0": 1024,
    "embed-multilingual-light-v3.0": 384,
    "embed-english-light-v3.0": 384,
    "embed-v4.0": 1536,
}


@EMBEDDERS.register("cohere")
class CohereEmbedder(BaseEmbedder):
    batch_size = EMBED_BATCH_SIZE["cohere"]

    def __init__(self):
        super().__init__(
            model=get_embedding_model("cohere"),
            api_key=COHERE_API_KEY,
            index_name=get_embedding_index("cohere"),
        )

    def _initialize_client(self):
        import cohere
        return cohere.ClientV2(self.api_key)

    @property
    def dimension(self) -> int:
        return _MODEL_DIMS.get(self.model, 1024)

    # ------------------------------------------------------------------

    def _embed_documents_batch(self, texts: List[str]) -> List[List[float]]:
        response = self.client.embed(
            model=self.model,
            texts=texts,
            input_type="search_document",
            embedding_types=["float"],
        )
        return response.embeddings.float

    def _get_query_embedding(self, text: str) -> List[float]:
        response = self.client.embed(
            model=self.model,
            texts=[text],
            input_type="search_query",
            embedding_types=["float"],
        )
        return response.embeddings.float[0]
