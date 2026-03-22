"""Literature review generation endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ...reasoning.literature_review_generator import LiteratureReviewGenerator

router = APIRouter(prefix="/api/literature", tags=["literature"])
_generator = LiteratureReviewGenerator()


class LiteratureRequest(BaseModel):
    topic: str
    papers: list[dict]
    sections: list[str] | None = None


@router.post("/review")
async def generate_review(payload: LiteratureRequest) -> dict:
    review = _generator.generate(payload.topic, payload.papers, payload.sections)
    return {"review": review}
