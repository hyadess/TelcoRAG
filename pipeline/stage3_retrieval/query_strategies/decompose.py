"""
Decomposition-based reformulation (operator family 1).

Splits a complex, multi-aspect query into smaller, independent sub-queries so a
retriever that struggles to jointly cover all aspects can retrieve each one
precisely. Targets the *multi-aspect query* failure mode.

    "What are the licensing fees and renewal conditions for ICX operators?"
      -> "What are the licensing fees for ICX operators?"
      -> "What are the renewal conditions for ICX operators?"
"""

import logging

from clients.gemini import structured_response
from config.settings import SETTINGS
from core.prompt_loader import get_loader
from core.registry import QUERY_STRATEGIES
from core.schemas import ReformulatedQueries

from .base import BaseQueryStrategy

logger = logging.getLogger("DecomposeStrategy")


@QUERY_STRATEGIES.register("decompose")
class DecomposeStrategy(BaseQueryStrategy):
    def __init__(self):
        self.prompts = get_loader()
        self.domain = SETTINGS.domain

    def reformulate(self, query: str) -> ReformulatedQueries:
        prompt = self.prompts.render(
            "query/decompose.j2",
            examples_file="decompose",
            query=query,
            domain=self.domain.get("domain", "legal"),
            terminology_hints=self.domain.get("terminology_hints", []),
        )
        result = structured_response(prompt, ReformulatedQueries)
        if result is None or not result.queries:
            logger.warning("Decomposition failed; falling back to original query.")
            return ReformulatedQueries(queries=[query])
        logger.info(f"Decompose: produced {len(result.queries)} sub-queries")
        return result
