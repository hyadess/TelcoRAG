"""
Plugin registry — the heart of the plugin system.

Every embedder, retriever, query strategy, reranker, and judge module registers
itself here via a decorator. Adding a new component is a 3-step process:

    1. Drop a file in the right folder, e.g. pipeline/stage3_retrieval/rerankers/my.py
    2. Decorate the class with @RERANKERS.register("my_name")
    3. Add the import to that folder's __init__.py (or it's auto-discovered)

The factory functions at the bottom turn a string from pipeline.yaml into a
ready-to-use instance, so the rest of the codebase never has to know about
specific implementations.
"""

from typing import Any, Callable, Dict, List


class Registry:
    """
    A dict-with-a-decorator. Holds {name -> class} for one component family.
    """

    def __init__(self, family: str):
        self.family = family
        self._items: Dict[str, type] = {}

    def register(self, name: str) -> Callable:
        """Decorator. Use as @REGISTRY.register("foo")."""
        name = name.lower().strip()

        def _wrap(cls):
            if name in self._items:
                # warn rather than crash — re-import is fine, double-register is suspicious
                # but we don't want to die during a notebook reload
                pass
            self._items[name] = cls
            return cls

        return _wrap

    def get(self, name: str) -> type:
        name = name.lower().strip()
        if name not in self._items:
            available = ", ".join(sorted(self._items.keys())) or "(none registered)"
            raise KeyError(
                f"'{name}' is not a registered {self.family}. Available: {available}"
            )
        return self._items[name]

    def list(self) -> List[str]:
        return sorted(self._items.keys())

    def build(self, name: str, **kwargs) -> Any:
        """Look up the class by name and instantiate it with kwargs."""
        return self.get(name)(**kwargs)


# =============================================================================
# THE REGISTRIES
# =============================================================================

EMBEDDERS = Registry("embedder")
CHUNKERS = Registry("chunker")
QUERY_STRATEGIES = Registry("query_strategy")
RETRIEVERS = Registry("retriever")
RERANKERS = Registry("reranker")
JUDGE_MODULES = Registry("judge_module")


# =============================================================================
# DISCOVERY — call this once at startup to trigger all @register decorators
# =============================================================================

def discover_plugins(*, include_judges: bool = True) -> None:
    """
    Import every plugin folder so the @register decorators run.

    This is idempotent — Python caches imported modules, so calling it more than
    once is cheap. Call it from any entry script before reading pipeline.yaml.
    Runtime-only deployments can set ``include_judges=False`` when the offline
    evaluation package is not shipped.
    """
    # Each of these imports has the side effect of populating its registry.
    # Order doesn't matter; the registries are independent.
    import pipeline.stage2_indexing.embedders        # noqa: F401
    import pipeline.stage2_indexing.chunkers          # noqa: F401
    import pipeline.stage3_retrieval.query_strategies  # noqa: F401
    import pipeline.stage3_retrieval.retrievers      # noqa: F401
    import pipeline.stage3_retrieval.rerankers       # noqa: F401
    # Judge modules are only needed by the offline evaluation workflow.  The
    # deployed chat backend intentionally omits ``evaluation/`` to keep its
    # serverless bundle small, so runtime callers must be able to skip them.
    if include_judges:
        import evaluation.judge.modules              # noqa: F401
