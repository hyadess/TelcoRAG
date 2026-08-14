"""Base class for rerankers. Subclass and decorate with @RERANKERS.register."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseReranker(ABC):
    """
    A reranker takes a query and a list of candidate chunks (with metadata)
    and returns a re-ordered, possibly trimmed list. Each output dict must
    contain a `relevance_score` field.
    """

    @abstractmethod
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        ...

    @staticmethod
    def _format_doc_for_rerank(doc: Dict[str, Any]) -> str:
        """Standard doc representation: doc summary + subsection text."""
        return f"{doc.get('document_summary', '')}\n{doc.get('subsection_text', '')}".strip()

    @staticmethod
    def _carry_fields(doc: Dict[str, Any], score: float, index: int) -> Dict[str, Any]:
        """Build the standard reranker output dict for one chunk."""
        out = {
            "id": doc.get("id", ""),
            "doc_name": doc.get("doc_name", ""),
            "document_summary": doc.get("document_summary", ""),
            "subsection_id": doc.get("subsection_id", ""),
            "subsection_text": doc.get("subsection_text", ""),
            "chapter": doc.get("chapter", ""),
            "section": doc.get("section", ""),
            "page_numbers": doc.get("page_numbers", ""),
            "relevance_score": float(score),
            "index": index,
        }
        # Carry retrieval-side diagnostics through reranking so the trace/viewer
        # can show how a chunk was produced (raw score, hierarchy ranks, and
        # whether it was sibling/neighbour expanded).
        for k in (
            "score", "base_score", "seq",
            "hier_doc_name_rank", "hier_chapter_rank", "hier_section_rank",
            "sibling_expanded", "neighbor_expanded", "neighbor_decision", "neighbor_added",
        ):
            if k in doc:
                out[k] = doc[k]
        return out
