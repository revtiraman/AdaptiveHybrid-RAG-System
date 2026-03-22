"""Query-planning and agentic execution endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api/planning", tags=["planning"])


class PlanningRequest(BaseModel):
    query: str


@router.post("/react")
async def run_planner(request: Request, payload: PlanningRequest) -> dict:
    planner = request.app.state.query_planning_agent
    result = await planner.run(payload.query)
    return {
        "final_answer": result.final_answer,
        "steps": [
            {
                "thought": step.thought,
                "action": step.action,
                "observation": step.observation,
            }
            for step in result.steps
        ],
    }


__all__ = ["router"]
