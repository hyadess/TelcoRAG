"""
Hybrid retriever — fuses dense (vector) and sparse (BM25) results via
Reciprocal Rank Fusion (RRF).

Why RRF: the two retrievers produce scores on different scales (cosine
similarity vs BM25), so directly comparing them is unprincipled. RRF only
uses the *rank* a document achieves in each retriever's output, which is
parameter-free (just `k`) and well-behaved across mismatched scoring schemes.

Reference: Cormack, Clarke, Buettcher (2009), "Reciprocal rank fusion
outperforms condorcet and individual rank learning methods."
"""

import logging
from typing import Any, Dict, List, Optional

from config.settings import SETTINGS
from core.registry import RETRIEVERS

from .base import BaseRetriever
from .bm25 import BM25Retriever
from .vector import VectorRetriever

logger = logging.getLogger("HybridRetriever")


def reciprocal_rank_fusion(
    rankings: List[List[Dict[str, Any]]],
    k: int = 60,
    id_field: str = "id",
) -> List[Dict[str, Any]]:
    """
    Combine multiple ranked lists into one via RRF.

    Args:
        rankings: a list of ranked lists. Each inner list is one retriever's
            top-k output, where index 0 is rank 1.
        k: the RRF constant. Higher = flatter rank influence.
        id_field: which field uniquely identifies a chunk. Defaults to the
            stable chunk ID shared by Pinecone and the local BM25 index.

    Returns: a single list of dicts, ordered by RRF score descending. Each
    output dict carries the original metadata plus a new `score` field
    (the RRF score) and an `rrf_score` field (same value, kept for clarity).
    """
    score_table: Dict[str, float] = {}
    doc_table: Dict[str, Dict[str, Any]] = {}

    for ranking in rankings:
        for rank, doc in enumerate(ranking):
            key = doc.get(id_field, "")
            if not key:
                continue
            score_table[key] = score_table.get(key, 0.0) + 1.0 / (k + rank + 1)
            # Keep the first-seen full doc so we don't lose metadata
            if key not in doc_table:
                doc_table[key] = doc

    # Sort by fused score descending
    sorted_keys = sorted(score_table, key=lambda k_: score_table[k_], reverse=True)
    out = []
    for key in sorted_keys:
        entry = dict(doc_table[key])
        entry["score"] = score_table[key]
        entry["rrf_score"] = score_table[key]
        out.append(entry)
    return out


@RETRIEVERS.register("hybrid")
class HybridRetriever(BaseRetriever):
    """Vector + BM25 fused via RRF."""

    def __init__(
        self,
        embedder_name: Optional[str] = None,
        rrf_k: Optional[int] = None,
        chunker: Optional[str] = None,
    ):
        # Pull the RRF k from pipeline.yaml if not given
        cfg = SETTINGS.pipeline.get("hybrid", {})
        self.rrf_k = rrf_k if rrf_k is not None else cfg.get("rrf_k", 60)

        self.vector = VectorRetriever(embedder_name=embedder_name)
        # BM25 sub-retriever reads the chunker-specific index so the sparse
        # half reads the matching BM25 corpus for this chunker.
        self.bm25 = BM25Retriever(chunker=chunker)

    def set_embedder(self, embedder) -> None:
        """Forward to the vector sub-retriever."""
        self.vector.set_embedder(embedder)

    def search(self, query: str, top_k: int = 30) -> List[Dict[str, Any]]:
        # Get a generous candidate pool from each, then fuse
        # (we ask for top_k from each so the fused output has ≤ 2*top_k unique docs)
        vector_results = self.vector.search(query, top_k=top_k)
        try:
            bm25_results = self.bm25.search(query, top_k=top_k)
        except FileNotFoundError as e:
            logger.warning(f"BM25 unavailable: {e}. Falling back to vector-only.")
            return vector_results

        fused = reciprocal_rank_fusion(
            [vector_results, bm25_results],
            k=self.rrf_k,
        )
        # Cap output at top_k so downstream reranking has bounded work
        return fused[:top_k]
