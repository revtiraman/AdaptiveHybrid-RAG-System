"""Automated literature review synthesis."""

from __future__ import annotations

from collections import defaultdict


class LiteratureReviewGenerator:
    """Generate structured review text from paper snippets."""

    def generate(self, topic: str, papers: list[dict], sections: list[str] | None = None) -> str:
        sections = sections or ["background", "methods", "results", "gaps"]
        grouped = defaultdict(list)
        for paper in papers:
            grouped[paper.get("cluster", "general")].append(paper)

        out = [f"# Literature Review: {topic}"]
        for sec in sections:
            out.append(f"\n## {sec.title()}")
            for cluster, items in grouped.items():
                out.append(f"\n### {cluster.title()}")
                for item in items[:5]:
                    out.append(f"- {item.get('title', 'Untitled')}: {item.get('summary', 'No summary available.')}")
        return "\n".join(out)


__all__ = ["LiteratureReviewGenerator"]
