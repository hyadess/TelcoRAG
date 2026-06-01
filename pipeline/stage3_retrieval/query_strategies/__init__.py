"""
Query reformulation operator plugins.

Importing this package registers every operator. Following the reformulation
operator framework, four operator families address four retrieval failure modes:

  - decompose  : decomposition-based     -> multi-aspect queries
  - diversify  : diversification-based    -> vocabulary mismatch
  - abstract   : abstraction-based        -> overly specific queries
  - hyde       : hypothetical-expansion   -> weak semantic signal

``simple`` is a non-reformulating passthrough kept as an experimental control.

Add a new operator by dropping a file here that decorates its class with
@QUERY_STRATEGIES.register("name"), then add an import below.
"""

from . import base       # noqa: F401
from . import simple     # noqa: F401  (control / passthrough)
from . import decompose  # noqa: F401
from . import diversify  # noqa: F401
from . import abstract   # noqa: F401
from . import hyde       # noqa: F401

from .base import BaseQueryStrategy

__all__ = ["BaseQueryStrategy"]
