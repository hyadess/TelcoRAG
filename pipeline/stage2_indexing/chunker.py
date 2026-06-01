"""
Backward-compatibility shim.

Chunking lives in the ``chunkers/`` plugin folder. This module re-exports the
``baseline`` chunker as ``Chunker`` so older imports keep working:

    from pipeline.stage2_indexing.chunker import Chunker

Prefer building from the registry instead:

    from core.registry import CHUNKERS, discover_plugins
    discover_plugins()
    chunker = CHUNKERS.build("baseline", max_chunk_size=2048, overlap=204)
"""

from .chunkers.base import BaseChunker  # noqa: F401
from .chunkers.baseline import BaselineChunker as Chunker  # noqa: F401

__all__ = ["Chunker", "BaseChunker"]
