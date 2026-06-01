"""
Hypothetical-expansion-based reformulation (operator family 4) — HyDE.

Generates a synthetic, answer-like passage and embeds it (concatenated with the
original query). The richer semantic signal helps dense retrieval on vague,
underspecified, or conversational queries. Targets the *weak semantic signal*
failure mode. Risks (hallucinated concepts, semantic drift) are mitigated by
keeping the original query in the embedded text and reranking downstream.
"""

from clients.gemini import general_response
from config.settings import SETTINGS
from core.prompt_loader import get_loader
from core.registry import QUERY_STRATEGIES
from core.schemas import ReformulatedQueries

from .base import BaseQueryStrategy


@QUERY_STRATEGIES.register("hyde")
class HydeStrategy(BaseQueryStrategy):
    def __init__(self):
        self.prompts = get_loader()
        self.domain = SETTINGS.domain

    def reformulate(self, query: str) -> ReformulatedQueries:
        prompt = self.prompts.render(
            "query/hyde.j2",
            examples_file="hyde",
            query=query,
            expert_role=self.domain.get("expert_role", "domain expert"),
        )
        hypothetical = general_response(prompt)
        # Combining the original query with the hypothetical answer gives the
        # embedding both literal terms and elaborated context.
        combined = f"{query}\n\n{hypothetical}" if hypothetical else query
        return ReformulatedQueries(queries=[combined])
