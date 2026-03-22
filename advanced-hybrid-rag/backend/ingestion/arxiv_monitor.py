"""ArXiv monitoring and digest generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class ArxivMonitorConfig:
    categories: list[str] = field(default_factory=lambda: ["cs.AI", "cs.CL"])
    keywords: list[str] = field(default_factory=list)


class ArxivMonitor:
    """Track configured arXiv categories and create a daily digest."""

    def __init__(self) -> None:
        self.config = ArxivMonitorConfig()
        self.last_digest: dict = {"date": None, "items": []}

    async def configure(self, categories: list[str], keywords: list[str]) -> dict:
        self.config = ArxivMonitorConfig(categories=categories, keywords=keywords)
        return {"status": "configured", "categories": categories, "keywords": keywords}

    async def poll(self) -> list[dict]:
        # Placeholder polling logic for scaffold phase.
        now = datetime.now(UTC).isoformat()
        items = [{"title": "Daily arXiv placeholder", "category": c, "fetched_at": now} for c in self.config.categories]
        self.last_digest = {"date": now, "items": items}
        return items

    async def digest(self) -> dict:
        return self.last_digest


__all__ = ["ArxivMonitor", "ArxivMonitorConfig"]
