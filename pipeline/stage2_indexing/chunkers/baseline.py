"""
``baseline`` — the single, enrichment-free chunker.

Dense embed text = document summary + chapter/section headers + subsection text.
BM25 corpus text = subsection text only.

This is the only indexing convention in the system. All splitting, context
summaries, and metadata assembly are inherited from ``BaseChunker``; this class
exists so the chunker is discoverable through the plugin registry (and so a new
indexing convention can be added later by dropping a sibling file).
"""

from core.registry import CHUNKERS

from .base import BaseChunker


@CHUNKERS.register("baseline")
class BaselineChunker(BaseChunker):
    # Embedding = headers + summary + subsection text; BM25 = subsection text.
    # Both behaviours are implemented in BaseChunker.process_subsection.
    pass
