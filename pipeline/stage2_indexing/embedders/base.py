"""Base class for all embedders. Subclass and decorate with @EMBEDDERS.register("name")."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from clients.pinecone_client import PineconeDB
from pipeline.stage2_indexing.vector_metadata import pinecone_metadata
from utils.adaptive_batch import AdaptiveBatchPolicy, run_adaptive_batches

logger = logging.getLogger("Embedder")


class BaseEmbedder(ABC):
    """
    Embeds documents and queries, and stores/searches them in a vector DB.

    Subclasses must implement:
      - _initialize_client()
      - dimension property
      - _embed_documents_batch(texts) -> list of vectors
        (called with at most `batch_size` texts at once)
      - _get_query_embedding(text) -> vector

    `batch_size` defaults to 32 — set it on the subclass to the provider's
    documented per-call cap (e.g. 96 for Cohere, 100 for OpenAI).
    """

    # Subclasses override this to match each provider's per-call limit.
    batch_size: int = 32

    def __init__(self, model: str, api_key: str, index_name: str = "default-index"):
        self.api_key = api_key
        self.model = model
        # Pinecone namespace isolating one chunker variant's vectors. Set via
        # `set_namespace()` by the ingestion/retrieval orchestrators. Empty
        # string == Pinecone's default namespace.
        self.namespace = ""
        self.vector_db = PineconeDB(index_name=index_name)
        self.client = self._initialize_client()

    def set_namespace(self, namespace: str) -> None:
        """Point this embedder at a specific Pinecone namespace."""
        self.namespace = namespace or ""

    @abstractmethod
    def _initialize_client(self):
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        ...

    @abstractmethod
    def _embed_documents_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a single batch of at most `self.batch_size` texts."""
        ...

    @abstractmethod
    def _get_query_embedding(self, text: str) -> List[float]:
        ...

    # ------------------------------------------------------------------
    # Generic adaptive batching wrapper. Most providers cap requests by text
    # count, tokens, or throughput. Capacity failures reduce the batch size for
    # the remainder of this run and retry the same inputs in order.
    # ------------------------------------------------------------------
    def _get_document_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        processed = 0

        def embed_batch(chunk):
            nonlocal processed
            logger.debug(
                "Embedding batch %d-%d / %d",
                processed,
                processed + len(chunk),
                len(texts),
            )
            result = self._embed_documents_batch(list(chunk))
            processed += len(chunk)
            return result

        batch_results = run_adaptive_batches(
            texts,
            embed_batch,
            policy=AdaptiveBatchPolicy(initial_batch_size=self.batch_size),
            operation=f"{self.model} embedding",
            logger=logger,
        )
        out = [vector for batch in batch_results for vector in batch]
        if len(out) != len(texts):
            raise RuntimeError(
                f"Embedding count mismatch: got {len(out)} for {len(texts)} inputs"
            )
        return out

    # ------------------------------------------------------------------
    # Public API used by the rest of the pipeline
    # ------------------------------------------------------------------
    def initialize_db(self):
        """Ensure the vector DB index exists; return True if it was created."""
        return self.vector_db.create_index(dimension=self.dimension, metric="cosine")

    def store_documents(self, chunks: List[Dict[str, Any]]):
        """Embed and store a list of chunks. Each chunk must have 'id', 'text', 'metadata'."""
        # Validate and compact metadata before paying to generate embeddings.
        metadatas = [pinecone_metadata(chunk) for chunk in chunks]
        texts = [c["text"] for c in chunks]
        logger.info(f"Generating embeddings for {len(texts)} documents...")
        embeddings = self._get_document_embeddings(texts)

        vectors = [
            {"id": chunk["id"], "values": embeddings[i], "metadata": metadatas[i]}
            for i, chunk in enumerate(chunks)
        ]
        self.vector_db.upsert_vectors(vectors, namespace=self.namespace)
        logger.info("Documents stored successfully.")

    def delete_documents(self, chunks: List[Dict[str, Any]]) -> None:
        """Remove this document's chunk IDs before retrying an incomplete ingest."""
        ids = [chunk["id"] for chunk in chunks]
        self.vector_db.delete_vectors(ids, namespace=self.namespace)

    def embed_query(self, query: str) -> List[float]:
        """Public query-embedding entry point (used by hierarchical retrieval
        to embed once and run several filtered Pinecone queries)."""
        return self._get_query_embedding(query)

    def search_by_vector(self, vector: List[float], top_k: int = 5, filters: Dict = None):
        """Run similarity search from a precomputed query vector."""
        return self.vector_db.query_similarity(
            vector=vector, top_k=top_k, filter_meta=filters, namespace=self.namespace
        )

    def fetch_vectors(self, ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Fetch stored vectors (values + metadata) by id from this namespace.

        Used by neighbour expansion to score a hit's prev/next chunks. Returns
        ``{id: {"values": [...], "metadata": {...}}}``.
        """
        return self.vector_db.fetch_by_ids(ids, namespace=self.namespace)

    def search(self, query: str, top_k: int = 5, filters: Dict = None):
        """Embed the query and run cosine similarity search."""
        logger.info(f"Embedding query: '{query[:80]}...'")
        query_vector = self._get_query_embedding(query)
        return self.vector_db.query_similarity(
            vector=query_vector, top_k=top_k, filter_meta=filters, namespace=self.namespace
        )
