"""Base class for all query strategies."""

from abc import ABC, abstractmethod

from core.schemas import ReformulatedQueries


class BaseQueryStrategy(ABC):
    """
    A query strategy takes the user's question and returns a list of search-ready
    queries. The retriever runs all of them and merges results downstream.
    """

    @abstractmethod
    def reformulate(self, query: str) -> ReformulatedQueries:
        ...
