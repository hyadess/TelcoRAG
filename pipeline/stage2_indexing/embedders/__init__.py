"""
Embedder plugin folder.

Importing this package triggers all @EMBEDDERS.register("...") decorators.
Add a new embedder by dropping a file here and adding its import below.
"""

from . import base       # noqa: F401  (base class — not registered, but exported)
from . import gemini     # noqa: F401
from . import openai     # noqa: F401
from . import voyage     # noqa: F401
from . import cohere     # noqa: F401
from . import perplexity # noqa: F401

from .base import BaseEmbedder

__all__ = ["BaseEmbedder"]
