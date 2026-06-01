"""Context relevance — are the retrieved chunks relevant to the query?"""

from typing import Any, Dict, List, Optional

from clients.gemini import structured_response
from config.settings import SETTINGS
from core.prompt_loader import get_loader
from core.registry import JUDGE_MODULES
from core.schemas import ContextRelevanceScore

from .base import BaseJudgeModule


@JUDGE_MODULES.register("context_relevance")
class ContextRelevanceJudge(BaseJudgeModule):
    name = "context_relevance"

    def __init__(self):
        self.prompts = get_loader()

    def evaluate(
        self,
        query: str,
        response: Optional[str] = None,
        chunks: Optional[List[Dict[str, Any]]] = None,
        reference: Optional[str] = None,
        **extra,
    ) -> Dict[str, Any]:
        chunks = chunks or []
        chunks_str = self._format_chunks(chunks)

        prompt = self.prompts.render(
            "judge/context_relevance.j2",
            query=query,
            chunks_str=chunks_str,
            n_chunks=len(chunks),
            document_type=SETTINGS.domain.get("document_type", "legal documents"),
        )
        result = structured_response(prompt, ContextRelevanceScore)
        if result is None:
            return {
                "ctx_precision": 0,
                "ctx_relevant_chunks": 0,
                "ctx_total_chunks": len(chunks),
                "ctx_noise_analysis": "JUDGE_ERROR",
                "ctx_relevance_reasoning": "",
            }
        return {
            "ctx_precision": result.precision_score,
            "ctx_relevant_chunks": result.relevant_chunk_count,
            "ctx_total_chunks": result.total_chunk_count,
            "ctx_noise_analysis": result.noise_analysis,
            "ctx_relevance_reasoning": result.reasoning,
        }
