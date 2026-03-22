"""Monitoring endpoints for arXiv tracking and digests."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/monitor", tags=["monitor"])


class MonitorConfigRequest(BaseModel):
    categories: list[str] = Field(default_factory=lambda: ["cs.AI", "cs.CL"])
    keywords: list[str] = Field(default_factory=list)


@router.post("/arxiv/config")
async def configure_arxiv_monitor(request: Request, payload: MonitorConfigRequest) -> dict:
    monitor = request.app.state.arxiv_monitor
    return await monitor.configure(categories=payload.categories, keywords=payload.keywords)


@router.post("/arxiv/poll")
async def poll_arxiv(request: Request) -> dict:
    monitor = request.app.state.arxiv_monitor
    items = await monitor.poll()
    return {"items": items, "count": len(items)}


@router.get("/arxiv/digest")
async def arxiv_digest(request: Request) -> dict:
    monitor = request.app.state.arxiv_monitor
    return await monitor.digest()


__all__ = ["router"]
