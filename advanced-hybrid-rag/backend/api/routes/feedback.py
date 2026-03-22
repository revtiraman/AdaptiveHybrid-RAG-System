"""Feedback APIs for adaptive learning."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from ...adaptive.feedback_learner import FeedbackItem

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


class FeedbackRequest(BaseModel):
    query_id: str
    answer: str
    rating: int = Field(ge=1, le=5)
    helpful: bool = True
    corrected_answer: str | None = None
    bad_citation_ids: list[str] = Field(default_factory=list)
    notes: str = ""


@router.post("/")
async def submit_feedback(request: Request, payload: FeedbackRequest) -> dict:
    learner = request.app.state.feedback_learner
    learner.add_feedback(
        FeedbackItem(
            query_id=payload.query_id,
            rating=payload.rating,
            helpful=payload.helpful,
            corrected_answer=payload.corrected_answer,
            bad_citation_ids=payload.bad_citation_ids,
        )
    )
    return {
        "status": "accepted",
        "query_id": payload.query_id,
        "rating": payload.rating,
        "hard_negative_count": len(learner.hard_negatives()),
    }


@router.get("/stats")
async def feedback_stats(request: Request) -> dict:
    learner = request.app.state.feedback_learner
    return {
        "total_feedback": len(learner.feedback),
        "hard_negatives": len(learner.hard_negatives()),
        "high_quality": len(learner.high_quality()),
    }
