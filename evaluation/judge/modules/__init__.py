"""
Judge module plugins. Importing this package registers them all.

Note: `pairwise` is not registered with @JUDGE_MODULES because it has a
different evaluate() signature (takes two responses). It's used separately by
the comparison harness.
"""

from . import base                # noqa: F401
from . import context_relevance   # noqa: F401
from . import context_sufficiency # noqa: F401
from . import faithfulness        # noqa: F401
from . import answer_correctness  # noqa: F401
from . import answer_relevance    # noqa: F401

from .base import BaseJudgeModule
from .pairwise import PairwiseJudge

__all__ = ["BaseJudgeModule", "PairwiseJudge"]
