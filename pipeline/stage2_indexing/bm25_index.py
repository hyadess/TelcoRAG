"""
BM25 keyword index — built once at ingestion time, queried at retrieval time.

Why have it: dense embeddings miss exact-token matches like Act names, fee codes,
defined terms ("Licensee", "Tk. 25,000", "ICX"). BM25 catches these. Combining
the two via RRF (see retrievers/hybrid.py) is a major retrieval upgrade for
legal/regulated documents where precise terminology matters.

Storage: a single pickle file containing the BM25 model and its associated
metadata list. The metadata mirrors the chunks stored in Pinecone, so the
retriever can use either index and return a consistent shape.

Tokenization is intentionally simple — lowercased, split on word boundaries,
stop-words removed via a small list. Good enough for English-language legal
documents; can be replaced if a domain tokenizer is needed.
"""

import logging
import pickle
import re
from pathlib import Path
from typing import Any, Dict, List, Union

logger = logging.getLogger("BM25Index")


# Minimal English stop-word list — kept short on purpose so BM25 still scores
# common legal connectors that may matter ("of", "in", "the" excluded; "with"
# kept in case it carries weight in clauses)
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "have", "in", "is", "it", "its", "of", "on", "or", "that",
    "the", "to", "was", "were", "will",
}

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:[.\-][A-Za-z0-9]+)*")


def tokenize(text: str) -> List[str]:
    """
    Tokenize for BM25.

    Keeps things like "1.01", "Tk.25,000-ish" (after normalizing punctuation
    around boundaries) more or less intact via the dot/hyphen-aware regex.
    Lowercases; drops short stop-words.
    """
    if not text:
        return []
    tokens = _TOKEN_RE.findall(text.lower())
    return [t for t in tokens if t not in _STOPWORDS and len(t) > 1]


class BM25Index:
    """Wraps `rank_bm25.BM25Okapi` with persistence and query helpers."""

    def __init__(self):
        self._bm25 = None  # rank_bm25.BM25Okapi instance
        self._metadatas: List[Dict[str, Any]] = []

    # ---------- build ----------

    def build(self, chunks: List[Dict[str, Any]]) -> None:
        """
        Build the index from a list of chunks. Each chunk needs:
          - 'metadata' dict (will be returned at search time)
          - either 'text' (the embed text) or metadata['subsection_text']

        We index the *full subsection_text* from metadata when available, since
        that's the human-relevant content; otherwise fall back to embed text.
        """
        from rank_bm25 import BM25Okapi  # local import keeps the dep optional

        corpus_tokens = []
        self._metadatas = []
        for chunk in chunks:
            md = chunk.get("metadata", {})
            # Prefer the chunker-provided BM25 text (subsection text). Fall
            # back to the raw subsection text, then the embed text, so older
            # caches that predate `bm25_text` still index sensibly.
            text = (
                md.get("bm25_text")
                or md.get("subsection_text")
                or chunk.get("text", "")
            )
            corpus_tokens.append(tokenize(text))
            # Keep a copy that includes the chunk's id and embed text so search
            # results are consistent with the dense path
            entry = dict(md)
            entry["id"] = chunk.get("id", "")
            self._metadatas.append(entry)

        if not corpus_tokens:
            logger.warning("BM25 build: no chunks provided.")
            return

        self._bm25 = BM25Okapi(corpus_tokens)
        logger.info(f"BM25 index built over {len(corpus_tokens)} chunks.")

    # ---------- query ----------

    def search(self, query: str, top_k: int = 30) -> List[Dict[str, Any]]:
        """
        Return the top_k chunks for `query`. Output shape mirrors the dense
        retriever: a list of metadata dicts each with a 'score' field.
        Returns [] if the index hasn't been built.
        """
        if self._bm25 is None:
            logger.warning("BM25 search called before build.")
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scores = self._bm25.get_scores(query_tokens)
        # Argsort descending, take top_k
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        results = []
        for i in top_indices:
            if scores[i] <= 0:
                continue  # skip zero-score entries
            entry = dict(self._metadatas[i])
            entry["score"] = float(scores[i])
            results.append(entry)
        return results

    # ---------- persistence ----------

    def save(self, path: Union[str, Path]) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({"bm25": self._bm25, "metadatas": self._metadatas}, f)
        logger.info(f"BM25 index saved to {path}")

    def load(self, path: Union[str, Path]) -> bool:
        """Load index from disk. Returns True on success, False if file missing."""
        path = Path(path)
        if not path.exists():
            return False
        with open(path, "rb") as f:
            data = pickle.load(f)
        self._bm25 = data["bm25"]
        self._metadatas = data["metadatas"]
        logger.info(f"BM25 index loaded from {path} ({len(self._metadatas)} chunks)")
        return True

    @property
    def n_documents(self) -> int:
        return len(self._metadatas)
