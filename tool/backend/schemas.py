"""Validated HTTP request and response contracts."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=5000)
    session_id: str = Field(min_length=1, max_length=64)

    @field_validator("question")
    @classmethod
    def non_blank_question(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Question cannot be blank")
        return value


class RetrievedSubsection(BaseModel):
    rank: int
    document: str
    chapter: str = ""
    section: str = ""
    subsection_id: str = ""
    page_numbers: Any = None
    text: str
    score: float | None = None


class ChatResult(BaseModel):
    response_id: UUID
    question: str
    answer: str
    retriever: str
    retrieved_subsections: list[RetrievedSubsection]
    latency_ms: int
    created_at: datetime


class RatingRequest(BaseModel):
    rater_id: str = Field(min_length=1, max_length=64)
    retrieval_relevance: int = Field(ge=1, le=5)
    completeness: int = Field(ge=1, le=5)
    correctness: int = Field(ge=1, le=5)
    comment: str = Field(default="", max_length=5000)


class RatingResult(BaseModel):
    rating_id: UUID
    response_id: UUID
    updated: bool


class CriterionStats(BaseModel):
    average: float
    count: int
    distribution: dict[str, int]


class AdminStats(BaseModel):
    total_responses: int
    rated_responses: int
    total_ratings: int
    rating_coverage_percent: float
    criteria: dict[str, CriterionStats]
    retriever_breakdown: list[dict[str, Any]]
    recent_feedback: list[dict[str, Any]]
