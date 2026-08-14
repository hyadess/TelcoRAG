"""Pinecone serverless vector DB client."""

import logging
import os
import time
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

logger = logging.getLogger("PineconeDB")

class PineconeDB:
    """Thin wrapper over the Pinecone Python SDK."""

    def __init__(self, index_name: str = "default-index"):
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "PINECONE_API_KEY is not set. Add it to .env before using Pinecone."
            )
        if not index_name or not index_name.strip():
            raise ValueError("Pinecone index_name must not be empty")
        self.pc = Pinecone(api_key=api_key)
        self.index_name = index_name
        self.index = None

    def create_index(
        self,
        dimension: int = 1536,
        metric: str = "cosine",
        wait_timeout: float = 300.0,
    ):
        """Create the index if it doesn't exist, then connect to it."""
        if dimension < 1:
            raise ValueError("dimension must be at least 1")
        if wait_timeout <= 0:
            raise ValueError("wait_timeout must be greater than 0")
        if not self.pc.has_index(self.index_name):
            logger.info(f"Creating index '{self.index_name}'...")
            self.pc.create_index(
                name=self.index_name,
                dimension=dimension,
                metric=metric,
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
            deadline = time.monotonic() + wait_timeout
            while not self._index_is_ready():
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        f"Pinecone index '{self.index_name}' was not ready within "
                        f"{wait_timeout:g} seconds"
                    )
                time.sleep(1)
            logger.info(f"Index '{self.index_name}' is ready.")
        else:
            logger.info(f"Index '{self.index_name}' already exists.")
        self.index = self.pc.Index(self.index_name)

    def _index_is_ready(self) -> bool:
        """Handle both mapping- and attribute-style Pinecone SDK responses."""
        description = self.pc.describe_index(self.index_name)
        status = getattr(description, "status", None)
        if status is None and isinstance(description, dict):
            status = description.get("status", {})
        ready = getattr(status, "ready", None)
        if ready is None and isinstance(status, dict):
            ready = status.get("ready", False)
        return bool(ready)

    def upsert_vectors(self, vectors: List[Dict[str, Any]], batch_size: int = 100, namespace: str = ""):
        """Batch-upsert vectors. Format: [{'id', 'values', 'metadata'}, ...]

        `namespace` isolates vectors within an index — used to keep different
        chunker conventions from mixing.
        """
        if self.index is None:
            raise ValueError("Index not initialized. Call create_index() first.")
        if batch_size < 1:
            raise ValueError("batch_size must be at least 1")

        total = len(vectors)
        logger.info(f"Upserting {total} vectors (namespace={namespace or 'default'})...")
        for i in range(0, total, batch_size):
            batch = vectors[i : i + batch_size]
            self.index.upsert(vectors=batch, namespace=namespace)
        logger.info("Upsert complete.")

    def query_similarity(
        self,
        vector: List[float],
        top_k: int = 5,
        filter_meta: Optional[Dict] = None,
        namespace: str = "",
    ):
        """Search for the most similar vectors. Returns the raw Pinecone response."""
        if self.index is None:
            raise ValueError("Index not connected.")
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        return self.index.query(
            vector=vector,
            top_k=top_k,
            include_metadata=True,
            filter=filter_meta,
            namespace=namespace,
        )

    def fetch_by_ids(self, ids: List[str], namespace: str = "") -> Dict[str, Dict[str, Any]]:
        """Fetch vectors (values + metadata) by id.

        Returns a mapping ``{id: {"values": [...], "metadata": {...}}}``. Used by
        neighbour expansion to score a hit's reading-order neighbours without a
        fresh similarity search. Missing ids are simply absent from the result.
        """
        if self.index is None:
            raise ValueError("Index not connected.")
        if not ids:
            return {}
        resp = self.index.fetch(ids=list(ids), namespace=namespace)
        vectors = getattr(resp, "vectors", None)
        if vectors is None and isinstance(resp, dict):
            vectors = resp.get("vectors", {})
        out: Dict[str, Dict[str, Any]] = {}
        for vid, rec in (vectors or {}).items():
            values = getattr(rec, "values", None)
            metadata = getattr(rec, "metadata", None)
            if values is None and isinstance(rec, dict):
                values = rec.get("values")
                metadata = rec.get("metadata")
            out[vid] = {"values": list(values or []), "metadata": dict(metadata or {})}
        return out
