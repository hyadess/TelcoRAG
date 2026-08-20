"""FastAPI entry point for chat, feedback collection, and admin analytics."""

import time
from contextlib import asynccontextmanager
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException, status
from sqlalchemy import distinct, func, select, text
from sqlalchemy.orm import Session

from tool.settings import RETRIEVER_NAME, SETTINGS

from .database import Base, engine, get_db
from .models import ChatResponse, Rating
from .rag_service import answer_question
from .schemas import (
    AdminStats,
    ChatRequest,
    ChatResult,
    CriterionStats,
    RatingRequest,
    RatingResult,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="TelcoRAG Feedback API", version="1.0.0", lifespan=lifespan)
DbSession = Annotated[Session, Depends(get_db)]


def require_admin(x_admin_password: Annotated[str | None, Header()] = None) -> None:
    configured = SETTINGS.admin_password
    if configured and x_admin_password != configured:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin password")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "retriever": RETRIEVER_NAME}


@app.get("/health/db")
def database_health(db: DbSession) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}


@app.post("/api/chat", response_model=ChatResult, status_code=status.HTTP_201_CREATED)
def chat(payload: ChatRequest, db: DbSession) -> ChatResult:
    started = time.perf_counter()
    try:
        answer, subsections = answer_question(payload.question)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"RAG pipeline failed: {exc}",
        ) from exc

    record = ChatResponse(
        session_id=payload.session_id,
        question=payload.question,
        answer=answer,
        retriever=RETRIEVER_NAME,
        retrieved_subsections=subsections,
        latency_ms=round((time.perf_counter() - started) * 1000),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return ChatResult(
        response_id=record.id,
        question=record.question,
        answer=record.answer,
        retriever=record.retriever,
        retrieved_subsections=record.retrieved_subsections,
        latency_ms=record.latency_ms,
        created_at=record.created_at,
    )


@app.put("/api/responses/{response_id}/rating", response_model=RatingResult)
def rate_response(response_id: UUID, payload: RatingRequest, db: DbSession) -> RatingResult:
    if db.get(ChatResponse, response_id) is None:
        raise HTTPException(status_code=404, detail="Response not found")

    rating = db.scalar(
        select(Rating).where(
            Rating.response_id == response_id,
            Rating.rater_id == payload.rater_id,
        )
    )
    updated = rating is not None
    if rating is None:
        rating = Rating(response_id=response_id, rater_id=payload.rater_id)
        db.add(rating)
    rating.retrieval_relevance = payload.retrieval_relevance
    rating.completeness = payload.completeness
    rating.correctness = payload.correctness
    rating.comment = payload.comment.strip()
    db.commit()
    db.refresh(rating)
    return RatingResult(rating_id=rating.id, response_id=response_id, updated=updated)


def _criterion_stats(db: Session, column) -> CriterionStats:
    average, count = db.execute(select(func.avg(column), func.count(column))).one()
    rows = db.execute(select(column, func.count()).group_by(column)).all()
    distribution = {str(score): 0 for score in range(1, 6)}
    distribution.update({str(score): total for score, total in rows})
    return CriterionStats(
        average=round(float(average or 0), 2),
        count=int(count or 0),
        distribution=distribution,
    )


@app.get(
    "/api/admin/stats",
    response_model=AdminStats,
    dependencies=[Depends(require_admin)],
)
def admin_stats(db: DbSession, recent_limit: int = 50) -> AdminStats:
    recent_limit = max(1, min(recent_limit, 200))
    total_responses = db.scalar(select(func.count(ChatResponse.id))) or 0
    total_ratings = db.scalar(select(func.count(Rating.id))) or 0
    rated_responses = db.scalar(select(func.count(distinct(Rating.response_id)))) or 0

    breakdown_rows = db.execute(
        select(
            ChatResponse.retriever,
            func.count(distinct(ChatResponse.id)),
            func.count(Rating.id),
            func.avg(Rating.retrieval_relevance),
            func.avg(Rating.completeness),
            func.avg(Rating.correctness),
        )
        .outerjoin(Rating, Rating.response_id == ChatResponse.id)
        .group_by(ChatResponse.retriever)
        .order_by(ChatResponse.retriever)
    ).all()
    retriever_breakdown = [
        {
            "retriever": row[0],
            "responses": row[1],
            "ratings": row[2],
            "retrieval_relevance": round(float(row[3] or 0), 2),
            "completeness": round(float(row[4] or 0), 2),
            "correctness": round(float(row[5] or 0), 2),
        }
        for row in breakdown_rows
    ]

    recent_rows = db.execute(
        select(Rating, ChatResponse)
        .join(ChatResponse, ChatResponse.id == Rating.response_id)
        .order_by(Rating.updated_at.desc())
        .limit(recent_limit)
    ).all()
    recent_feedback = [
        {
            "response_id": str(response.id),
            "created_at": rating.updated_at.isoformat(),
            "question": response.question,
            "answer": response.answer,
            "retriever": response.retriever,
            "retrieval_relevance": rating.retrieval_relevance,
            "completeness": rating.completeness,
            "correctness": rating.correctness,
            "comment": rating.comment,
        }
        for rating, response in recent_rows
    ]

    return AdminStats(
        total_responses=total_responses,
        rated_responses=rated_responses,
        total_ratings=total_ratings,
        rating_coverage_percent=round(100 * rated_responses / total_responses, 1)
        if total_responses
        else 0,
        criteria={
            "Retrieval relevance": _criterion_stats(db, Rating.retrieval_relevance),
            "Completeness": _criterion_stats(db, Rating.completeness),
            "Correctness": _criterion_stats(db, Rating.correctness),
        },
        retriever_breakdown=retriever_breakdown,
        recent_feedback=recent_feedback,
    )
