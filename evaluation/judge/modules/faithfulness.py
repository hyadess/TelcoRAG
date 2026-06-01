"""Faithfulness — does the response stay grounded in the retrieved chunks?"""

from typing import Any, Dict, List, Optional

from clients.gemini import structured_response
from core.prompt_loader import get_loader
from core.registry import JUDGE_MODULES
from core.schemas import FaithfulnessScore

from .base import BaseJudgeModule


@JUDGE_MODULES.register("faithfulness")
class FaithfulnessJudge(BaseJudgeModule):
    name = "faithfulness"

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
        chunks_str = self._format_chunks(chunks, truncate=800)

        prompt = self.prompts.render(
            "judge/faithfulness.j2",
            query=query,
            chunks_str=chunks_str,
            response=response or "",
        )
        result = structured_response(prompt, FaithfulnessScore)
        if result is None:
            return {
                "faithfulness": 0,
                "hallucinated_claims": "JUDGE_ERROR",
                "faithfulness_reasoning": "",
            }
        return {
            "faithfulness": result.faithfulness,
            "hallucinated_claims": result.hallucinated_claims,
            "faithfulness_reasoning": result.reasoning,
        }
