"""Pinecone serverless vector DB client."""

import logging
import os
import time
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

logger = logging.getLogger("PineconeDB")

API_KEY = os.getenv("PINECONE_API_KEY")


class PineconeDB:
    """Thin wrapper over the Pinecone Python SDK."""

    def __init__(self, index_name: str = "default-index"):
        self.pc = Pinecone(api_key=API_KEY)
        self.index_name = index_name
        self.index = None

    def create_index(self, dimension: int = 1536, metric: str = "cosine"):
        """Create the index if it doesn't exist, then connect to it."""
        if not self.pc.has_index(self.index_name):
            logger.info(f"Creating index '{self.index_name}'...")
            self.pc.create_index(
                name=self.index_name,
                dimension=dimension,
                metric=metric,
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
            while not self.pc.describe_index(self.index_name).status.ready:
                time.sleep(1)
            logger.info(f"Index '{self.index_name}' is ready.")
        else:
            logger.info(f"Index '{self.index_name}' already exists.")
        self.index = self.pc.Index(self.index_name)

    def upsert_vectors(self, vectors: List[Dict[str, Any]], batch_size: int = 100, namespace: str = ""):
        """Batch-upsert vectors. Format: [{'id', 'values', 'metadata'}, ...]

        `namespace` isolates vectors within an index — used to keep different
        chunker conventions from mixing.
        """
        if not self.index:
            raise ValueError("Index not initialized. Call create_index() first.")

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
        if not self.index:
            raise ValueError("Index not connected.")
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
        if not self.index:
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
