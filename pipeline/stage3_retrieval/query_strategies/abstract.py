"""
Abstraction-based reformulation (operator family 3).

Transforms a highly specific query into a more general conceptual form to
recover the broader governing rule. Targets the *overly specific query* failure
mode, common in legal/regulatory corpora where evidence sits at a higher
conceptual level than the surface wording.

    "Can ICX operators transfer spectrum rights?"
      -> "What rules govern ICX operator permissions and limitations?"

Searches both the abstract form (to find the governing rule) and the original
(to catch direct hits).
"""

import logging

from clients.gemini import structured_response
from config.settings import SETTINGS
from core.prompt_loader import get_loader
from core.registry import QUERY_STRATEGIES
from core.schemas import ReformulatedQueries

from .base import BaseQueryStrategy

logger = logging.getLogger("AbstractStrategy")


@QUERY_STRATEGIES.register("abstract")
class AbstractStrategy(BaseQueryStrategy):
    def __init__(self):
        self.prompts = get_loader()
        self.domain = SETTINGS.domain

    def reformulate(self, query: str) -> ReformulatedQueries:
        prompt = self.prompts.render(
            "query/abstract.j2",
            examples_file="abstract",
            query=query,
            domain=self.domain.get("domain", "legal"),
        )
        result = structured_response(prompt, ReformulatedQueries)
        if result is None or not result.queries:
            logger.warning("Abstraction failed; falling back to original.")
            return ReformulatedQueries(queries=[query])

        queries = list(result.queries)
        if query not in queries:
            queries.append(query)
        logger.info(f"Abstract: produced {len(queries)} queries")
        return ReformulatedQueries(queries=queries)
