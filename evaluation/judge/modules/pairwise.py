"""
Pairwise comparison — judge two candidate responses head-to-head.

Position bias is real (Zheng et al., MT-Bench): LLM judges systematically
prefer the answer in position 1. We mitigate by running the comparison twice
with the candidates swapped, then merging the two verdicts.

Output keys:
  - pairwise_winner: 'A', 'B', or 'tie'
  - pairwise_confidence: 1..5 average across the two passes
  - pairwise_position_bias: True if the two passes disagreed (signals bias)

This module is a bit different from the others — it's not run as part of
`evaluate_full`, it's invoked separately when comparing two experiment runs.
"""

from typing import Any, Dict, Optional

from clients.gemini import structured_response
from config.settings import SETTINGS
from core.prompt_loader import get_loader
from core.schemas import PairwiseVerdict


class PairwiseJudge:
    """Not registered with @JUDGE_MODULES because it has a different signature."""

    def __init__(self):
        self.prompts = get_loader()

    def _judge_once(
        self,
        query: str,
        response_a: str,
        response_b: str,
        reference: Optional[str] = None,
    ) -> Optional[PairwiseVerdict]:
        prompt = self.prompts.render(
            "judge/pairwise.j2",
            query=query,
            response_a=response_a,
            response_b=response_b,
            reference=reference,
            document_type=SETTINGS.domain.get("document_type", "legal documents"),
        )
        return structured_response(prompt, PairwiseVerdict)

    def compare(
        self,
        query: str,
        response_a: str,
        response_b: str,
        reference: Optional[str] = None,
    ) -> Dict[str, Any]:
        # Pass 1: A=A, B=B
        v1 = self._judge_once(query, response_a, response_b, reference)
        # Pass 2: positions swapped
        v2 = self._judge_once(query, response_b, response_a, reference)

        if v1 is None or v2 is None:
            return {
                "pairwise_winner": "JUDGE_ERROR",
                "pairwise_confidence": 0,
                "pairwise_position_bias": False,
                "pairwise_reasoning_1": (v1.reasoning if v1 else ""),
                "pairwise_reasoning_2": (v2.reasoning if v2 else ""),
            }

        # In pass 2 the labels are flipped — translate back
        translated_v2_winner = {"A": "B", "B": "A", "tie": "tie"}.get(v2.winner, v2.winner)

        # If both passes agree -> use that verdict.
        # If they disagree -> position bias detected; downgrade to "tie" with
        # confidence = 1 (i.e. low) so the user knows.
        if v1.winner == translated_v2_winner:
            winner = v1.winner
            confidence = (v1.confidence + v2.confidence) / 2
            bias = False
        else:
            winner = "tie"
            confidence = 1
            bias = True

        return {
            "pairwise_winner": winner,
            "pairwise_confidence": round(confidence, 2),
            "pairwise_position_bias": bias,
            "pairwise_reasoning_1": v1.reasoning,
            "pairwise_reasoning_2": v2.reasoning,
        }
