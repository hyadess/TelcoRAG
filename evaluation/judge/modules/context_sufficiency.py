"""Context sufficiency — do the chunks contain enough info to answer fully?"""

from typing import Any, Dict, List, Optional

from clients.gemini import structured_response
from core.prompt_loader import get_loader
from core.registry import JUDGE_MODULES
from core.schemas import ContextSufficiencyScore

from .base import BaseJudgeModule


@JUDGE_MODULES.register("context_sufficiency")
class ContextSufficiencyJudge(BaseJudgeModule):
    name = "context_sufficiency"

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
        # For sufficiency the LLM needs a bit more text per chunk
        chunks_str = self._format_chunks(chunks, truncate=800)

        prompt = self.prompts.render(
            "judge/context_sufficiency.j2",
            query=query,
            chunks_str=chunks_str,
        )
        result = structured_response(prompt, ContextSufficiencyScore)
        if result is None:
            return {
                "ctx_sufficiency": 0,
                "ctx_missing_info": "JUDGE_ERROR",
                "ctx_sufficiency_reasoning": "",
            }
        return {
            "ctx_sufficiency": result.sufficiency,
            "ctx_missing_info": result.missing_info,
            "ctx_sufficiency_reasoning": result.reasoning,
        }
