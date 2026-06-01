"""Simple passthrough — return the original query unchanged."""

from core.registry import QUERY_STRATEGIES
from core.schemas import ReformulatedQueries

from .base import BaseQueryStrategy


@QUERY_STRATEGIES.register("simple")
class SimpleStrategy(BaseQueryStrategy):
    def reformulate(self, query: str) -> ReformulatedQueries:
        return ReformulatedQueries(queries=[query])
