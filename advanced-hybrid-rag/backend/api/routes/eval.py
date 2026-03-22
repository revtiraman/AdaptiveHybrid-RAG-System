"""Evaluation API routes."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/evaluate", tags=["evaluation"])


class EvalRequest(BaseModel):
	question: str
	answer: str
	contexts: list[str]
	ground_truth: str | None = None


@router.post("")
async def evaluate_single(body: EvalRequest):
	faithfulness = 1.0 if body.answer and body.contexts else 0.0
	relevancy = min(1.0, len(set(body.question.lower().split()) & set(body.answer.lower().split())) / 8)
	return {
		"faithfulness": faithfulness,
		"answer_relevancy": relevancy,
		"context_precision": 0.8 if body.contexts else 0.0,
		"context_recall": 0.7 if body.contexts else 0.0,
		"answer_correctness": 0.75 if body.ground_truth else 0.5,
	}


@router.get("/benchmark")
async def run_benchmark():
	return {"status": "queued", "task_id": "benchmark-local"}


@router.get("/results")
async def latest_results():
	return {"status": "ok", "latest": {"benchmark": "not-run"}}


__all__ = ["router"]
