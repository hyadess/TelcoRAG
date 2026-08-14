"""
Answer relevance — does the answer actually address the question?

This is a RAGAS-style reference-free metric. It works without ground truth,
which makes it useful for sanity-checking the system on queries you don't have
expert answers for.

This module ignores correctness entirely and asks only whether the response is
*on-topic*. A response that is completely wrong but on-topic can still score 5.
"""

from typing import Any, Dict, List, Optional

from clients.gemini import structured_response
from core.prompt_loader import get_loader
from core.registry import JUDGE_MODULES
from core.schemas import AnswerRelevanceScore

from .base import BaseJudgeModule


@JUDGE_MODULES.register("answer_relevance")
class AnswerRelevanceJudge(BaseJudgeModule):
    name = "answer_relevance"

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
        prompt = self.prompts.render(
            "judge/answer_relevance.j2",
            query=query,
            response=response or "",
        )
        result = structured_response(prompt, AnswerRelevanceScore)
        if result is None:
            return {
                "answer_relevance": 0,
                "off_topic_content": "JUDGE_ERROR",
                "answer_relevance_reasoning": "",
            }
        return {
            "answer_relevance": result.relevance,
            "off_topic_content": result.off_topic_content,
            "answer_relevance_reasoning": result.reasoning,
        }
