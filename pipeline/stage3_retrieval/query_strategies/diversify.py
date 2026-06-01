"""
Diversification-based reformulation (operator family 2).

Generates multiple semantically equivalent variants of the query to overcome
*vocabulary mismatch* between the user's wording and the corpus. Preserves the
single information need; only widens lexical coverage (helps BM25 especially).

    "license fee" -> "licensing cost", "application fee", "regulatory charge"
"""

import logging

from clients.gemini import structured_response
from config.settings import SETTINGS
from core.prompt_loader import get_loader
from core.registry import QUERY_STRATEGIES
from core.schemas import ReformulatedQueries

from .base import BaseQueryStrategy

logger = logging.getLogger("DiversifyStrategy")


@QUERY_STRATEGIES.register("diversify")
class DiversifyStrategy(BaseQueryStrategy):
    def __init__(self, n_variants: int = 4):
        self.n_variants = n_variants
        self.prompts = get_loader()
        self.domain = SETTINGS.domain

    def reformulate(self, query: str) -> ReformulatedQueries:
        prompt = self.prompts.render(
            "query/diversify.j2",
            examples_file="diversify",
            query=query,
            domain=self.domain.get("domain", "legal"),
            n_variants=self.n_variants,
        )
        result = structured_response(prompt, ReformulatedQueries)
        if result is None or not result.queries:
            logger.warning("Diversification failed; falling back to original.")
            return ReformulatedQueries(queries=[query])

        queries = list(result.queries)
        if query not in queries:
            queries.append(query)
        logger.info(f"Diversify: produced {len(queries)} variants")
        return ReformulatedQueries(queries=queries)
