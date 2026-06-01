"""
Base class for judge modules.

Each module evaluates a single dimension (relevance, sufficiency, faithfulness, etc.).
Modules are registered via @JUDGE_MODULES.register("name") and consumed by
the orchestrator.

Modules return a dict ready to write to a CSV row. The dict's keys become
column names in the output. By convention, the primary 1-5 score key matches
the metric name (e.g., 'faithfulness': 4).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseJudgeModule(ABC):
    """All judge modules implement this interface."""

    name: str = "base"  # subclasses override

    @abstractmethod
    def evaluate(
        self,
        query: str,
        response: Optional[str] = None,
        chunks: Optional[List[Dict[str, Any]]] = None,
        reference: Optional[str] = None,
        **extra,
    ) -> Dict[str, Any]:
        """
        Run the evaluation.

        The signature accepts everything any module might need; individual
        modules use only the fields they care about. Unused fields are ignored.

        Returns:
            A dict of column-name -> value for the output row.
            Always include a primary 1-5 score under the module's `name` key.
        """
        ...

    @staticmethod
    def _format_chunks(chunks: List[Dict[str, Any]], truncate: int = 500) -> str:
        """Standard chunk formatting for judge prompts."""
        parts = []
        for i, c in enumerate(chunks):
            doc = c.get("doc_name", "Unknown")
            section = c.get("section", "")
            text = (c.get("subsection_text") or "")[:truncate]
            parts.append(f"[Chunk {i + 1}] Doc: {doc} | Section: {section}\n{text}")
        return "\n---\n".join(parts)
