"""Answer correctness — compares response against a ground-truth reference."""

from typing import Any, Dict, List, Optional

from clients.gemini import structured_response
from config.settings import SETTINGS
from core.prompt_loader import get_loader
from core.registry import JUDGE_MODULES
from core.schemas import AnswerCorrectnessScore

from .base import BaseJudgeModule


@JUDGE_MODULES.register("answer_correctness")
class AnswerCorrectnessJudge(BaseJudgeModule):
    name = "answer_correctness"

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
        if not reference:
            # Reference-required module — skip cleanly if missing
            return {
                "correctness": 0,
                "completeness": 0,
                "relevance": 0,
                "factual_errors": "NO_REFERENCE",
                "missing_points": "NO_REFERENCE",
                "correctness_reasoning": "",
            }

        prompt = self.prompts.render(
            "judge/answer_correctness.j2",
            query=query,
            reference=reference,
            response=response or "",
            document_type=SETTINGS.domain.get("document_type", "legal documents"),
        )
        result = structured_response(prompt, AnswerCorrectnessScore)
        if result is None:
            return {
                "correctness": 0,
                "completeness": 0,
                "relevance": 0,
                "factual_errors": "JUDGE_ERROR",
                "missing_points": "JUDGE_ERROR",
                "correctness_reasoning": "",
            }
        return {
            "correctness": result.correctness,
            "completeness": result.completeness,
            "relevance": result.relevance,
            "factual_errors": result.factual_errors,
            "missing_points": result.missing_points,
            "correctness_reasoning": result.reasoning,
        }
