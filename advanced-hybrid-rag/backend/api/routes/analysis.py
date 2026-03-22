"""Advanced analysis endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ...analysis.citation_analysis import CitationAnalysis

router = APIRouter(prefix="/api/analysis", tags=["analysis"])
_analysis = CitationAnalysis()


class CitationGraphRequest(BaseModel):
    edges: list[tuple[str, str]]


@router.post("/citations")
async def citation_metrics(payload: CitationGraphRequest) -> dict:
    graph = _analysis.build_graph(payload.edges)
    return {"metrics": _analysis.metrics(graph)}
