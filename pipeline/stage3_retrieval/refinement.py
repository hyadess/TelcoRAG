"""
Gap analysis for the two-call (corrective) retrieval mode.

After the first retrieval round, this module asks the LLM whether the chunks
retrieved so far already cover the *main* query. If not, it returns one or more
focused follow-up queries that the orchestrator runs in a second round, merging
the new chunks with the first round's before a final rerank against the main
query.

This is the only LLM-dependent piece of the two-call flow; the orchestration
(round 1, decide, round 2, merge, rerank) lives in the retrieval orchestrator so
the control flow stays in one readable place.
"""

import logging
from typing import Any, Dict, List

from clients.gemini import structured_response
from config.settings import SETTINGS
from core.prompt_loader import get_loader
from core.schemas import GapAnalysis

logger = logging.getLogger("GapAnalysis")


def _context_window(chunks: List[Dict[str, Any]], max_chunks: int = 12, max_chars: int = 600) -> str:
    """Compact rendering of the current chunks for the gap-analysis prompt."""
    parts = []
    for i, c in enumerate(chunks[:max_chunks]):
        head = f"[{i + 1}] {c.get('doc_name', '')} | {c.get('section', '')} | {c.get('subsection_id', '')}"
        text = (c.get("subsection_text", "") or "")[:max_chars]
        parts.append(f"{head}\n{text}")
    return "\n\n---\n\n".join(parts)


def analyze_gap(main_query: str, chunks: List[Dict[str, Any]]) -> GapAnalysis:
    """Ask the LLM whether `chunks` suffice for `main_query`; propose follow-ups.

    Falls back to a "sufficient" verdict on any LLM/parse failure so the
    pipeline degrades to single-call behaviour instead of erroring.
    """
    prompts = get_loader()
    domain = SETTINGS.domain
    prompt = prompts.render(
        "query/gap_analysis.j2",
        query=main_query,
        context_window=_context_window(chunks),
        domain=domain.get("domain", "the relevant legal area"),
    )
    result = structured_response(prompt, GapAnalysis)
    if result is None:
        logger.warning("Gap analysis failed; treating context as sufficient.")
        return GapAnalysis(reasoning="gap analysis unavailable", sufficient=True)
    # Defensive: if marked insufficient but no follow-ups, treat as sufficient.
    if not result.sufficient and not result.followup_queries:
        result.sufficient = True
    return result
