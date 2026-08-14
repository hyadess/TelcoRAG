"""
LLM-as-reranker — use the LLM itself to score relevance of each candidate.

When it shines: niche legal language where cross-encoders trained on web data
struggle, or when the query is unusual / multi-hop. It reasons over the
full passage text rather than relying on lexical overlap.

When to skip: this is the slowest reranker. Don't use for >50 candidates per
query unless you really need it. For experimentation set `top_k_to_score` to
limit how many candidates actually get scored.

Implementation: we ask the LLM to return a 0–10 score per candidate in batches
of `batch_size`. Failures fall back to the candidate's original score.
"""

import logging
import re
from typing import Any, Dict, List

from clients.gemini import general_response
from core.registry import RERANKERS

from .base import BaseReranker

logger = logging.getLogger("LLMReranker")


# We score a small batch at a time — keeps the prompt focused, easier to parse,
# and avoids the LLM losing track of the indices.
_BATCH_PROMPT = """You are an expert at relevance scoring for a legal document Q&A system.

Score each numbered passage on how relevant it is to the QUESTION below, on a scale of 0 to 10:
- 10 = directly and completely answers the question
- 7-9 = contains key information for the answer
- 4-6 = related but only partially useful
- 1-3 = touches the topic but unlikely to help
- 0 = irrelevant

### QUESTION
{query}

### PASSAGES
{passages}

### OUTPUT FORMAT
Output one line per passage in the form `<id>: <score>` (no other text).
Example output for 3 passages:
1: 8
2: 3
3: 6
"""


@RERANKERS.register("llm")
class LLMReranker(BaseReranker):
    def __init__(self, batch_size: int = 5, top_k_to_score: int = 30):
        self.batch_size = batch_size
        self.top_k_to_score = top_k_to_score

    def _score_batch(self, query: str, batch: List[Dict[str, Any]]) -> List[float]:
        """Returns a 0-10 score per doc in `batch`. On failure, returns 5.0 each."""
        passages = []
        for i, d in enumerate(batch):
            text = self._format_doc_for_rerank(d)[:1500]  # truncate to control prompt size
            passages.append(f"[{i + 1}]\n{text}")
        prompt = _BATCH_PROMPT.format(query=query, passages="\n\n".join(passages))

        raw = general_response(prompt)
        scores = [5.0] * len(batch)  # default fallback

        if not raw:
            return scores

        # Parse "1: 8" / "1 : 8" / "1.8" lines
        for line in raw.splitlines():
            m = re.match(r"\s*(\d+)\s*[:.\-]\s*(\d+(?:\.\d+)?)", line)
            if m:
                idx = int(m.group(1)) - 1
                if 0 <= idx < len(batch):
                    try:
                        scores[idx] = max(0.0, min(10.0, float(m.group(2))))
                    except ValueError:
                        pass
        return scores

    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        if not documents:
            return []

        # Limit the number of candidates the LLM has to score
        head = documents[: self.top_k_to_score]
        all_scores: List[float] = []
        for i in range(0, len(head), self.batch_size):
            batch = head[i : i + self.batch_size]
            all_scores.extend(self._score_batch(query, batch))

        # Pair, sort, normalize to 0-1, take top_k
        scored = list(zip(head, all_scores))
        scored.sort(key=lambda x: x[1], reverse=True)
        out = []
        for i, (d, s) in enumerate(scored[:top_k]):
            out.append(self._carry_fields(d, s / 10.0, i))
        return out
