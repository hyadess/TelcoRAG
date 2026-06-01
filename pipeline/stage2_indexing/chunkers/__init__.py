"""
Chunker plugin folder.

Importing this package triggers the @CHUNKERS.register("...") decorators.

There is a single indexing convention, ``baseline``:
  - dense embed text = document summary + headers + subsection text
  - BM25 corpus text = subsection text only

Add a new convention by dropping a file here, decorating with
@CHUNKERS.register("name"), and adding its import below.
"""

from . import base      # noqa: F401  (base class — not registered)
from . import baseline  # noqa: F401

from .base import BaseChunker

__all__ = ["BaseChunker"]
