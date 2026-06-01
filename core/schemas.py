"""
All Pydantic schemas in one place.

Reasons for one file: there are not many of them, they're tightly related, and
having them together makes it obvious what data flows through the pipeline.
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# =============================================================================
# DOCUMENT EXTRACTION (stage 1)
# =============================================================================

class PageItemType(str, Enum):
    CHAPTER_HEADER = "chapter_header"
    SECTION_HEADER = "section_header"
    NEW_SUBSECTION = "new_subsection"
    CONTINUATION = "continuation"


class DocumentMetadata(BaseModel):
    document_name: str = Field(..., description="The official title of the document")
    document_summary: str = Field(..., description="A concise 1-2 sentence summary")


class RawPageItem(BaseModel):
    type: PageItemType
    content: str = Field(..., description="The text content or header title")
    id: Optional[str] = Field(None, description="The subsection ID (e.g., '1.01') if applicable")


class PageAnalysisResponse(BaseModel):
    items: List[RawPageItem]


class FinalSubsection(BaseModel):
    """A structured subsection ready for indexing."""
    document_name: str
    document_summary: str
    chapter: str
    section: str
    subsection_id: str
    subsection_text: str
    page_numbers: List[int]


# =============================================================================
# QUERY REFORMULATION (stage 3)
# =============================================================================

class ReformulatedQueries(BaseModel):
    """Output of any query strategy — a list of search-ready queries."""
    queries: List[str]


# =============================================================================
# TWO-CALL / CORRECTIVE RETRIEVAL (stage 3)
# =============================================================================

class GapAnalysis(BaseModel):
    """
    Output of the gap-analysis LLM call in the two-call retriever.

    After the first retrieval round, the LLM inspects the *main* query against
    the chunks retrieved so far and decides whether anything is still missing.
    If so, it proposes one or more focused follow-up queries for a second round.
    """
    reasoning: str = Field(
        ...,
        description="Brief chain-of-thought: what the query asks vs. what the chunks cover.",
    )
    sufficient: bool = Field(
        ...,
        description="True if the retrieved chunks already cover everything the main query needs.",
    )
    missing_info: str = Field(
        default="",
        description="Plain-language description of what is still missing (empty if sufficient).",
    )
    followup_queries: List[str] = Field(
        default_factory=list,
        description="1-3 focused search queries targeting only the missing information. Empty if sufficient.",
    )


# =============================================================================
# JUDGE OUTPUTS (evaluation)
# =============================================================================

class ContextRelevanceScore(BaseModel):
    reasoning: str = Field(..., description="Step-by-step reasoning before scoring (chain-of-thought).")
    relevant_chunk_count: int = Field(..., ge=0)
    total_chunk_count: int = Field(..., ge=0)
    precision_score: int = Field(..., ge=1, le=5)
    noise_analysis: str


class ContextSufficiencyScore(BaseModel):
    reasoning: str = Field(..., description="Step-by-step reasoning before scoring.")
    sufficiency: int = Field(..., ge=1, le=5)
    missing_info: str


class FaithfulnessScore(BaseModel):
    reasoning: str = Field(..., description="Step-by-step verification of each claim.")
    faithfulness: int = Field(..., ge=1, le=5)
    hallucinated_claims: str


class AnswerCorrectnessScore(BaseModel):
    reasoning: str = Field(..., description="Step-by-step comparison with the reference.")
    correctness: int = Field(..., ge=1, le=5)
    completeness: int = Field(..., ge=1, le=5)
    relevance: int = Field(..., ge=1, le=5)
    factual_errors: str
    missing_points: str


class AnswerRelevanceScore(BaseModel):
    """
    RAGAS-style reference-free metric. Asks: does the answer actually address
    the question (regardless of whether it's correct)?
    """
    reasoning: str
    relevance: int = Field(..., ge=1, le=5)
    off_topic_content: str


class PairwiseVerdict(BaseModel):
    """Output of pairwise comparison between two responses."""
    reasoning: str
    winner: str = Field(..., description="One of: 'A', 'B', 'tie'")
    confidence: int = Field(..., ge=1, le=5)
