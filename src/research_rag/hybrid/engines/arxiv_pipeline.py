from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
from typing import Any
from urllib.parse import quote_plus
from urllib.request import urlopen
import xml.etree.ElementTree as ET


ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


@dataclass(slots=True)
class ArxivEntry:
    arxiv_id: str
    title: str
    summary: str
    updated: datetime
    pdf_url: str
    categories: list[str]


class ArxivAutoPipeline:
    def __init__(self, system, documents_dir: Path) -> None:
        self.system = system
        self.documents_dir = documents_dir

    def run(
        self,
        query: str,
        max_results: int = 10,
        days_back: int = 30,
        categories: list[str] | None = None,
        relevance_terms: list[str] | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        fetched = self.fetch(query=query, max_results=max_results)
        filtered = self.filter_entries(
            fetched,
            query=query,
            days_back=days_back,
            categories=categories or [],
            relevance_terms=relevance_terms or [],
        )

        ingested: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        failed: list[dict[str, Any]] = []

        for entry in filtered:
            paper_id = f"arxiv-{entry.arxiv_id.replace('/', '-') }"
            if self.system.metadata_store.get_paper(paper_id) is not None:
                skipped.append({"arxiv_id": entry.arxiv_id, "reason": "already-indexed", "paper_id": paper_id})
                continue

            if dry_run:
                skipped.append({"arxiv_id": entry.arxiv_id, "reason": "dry-run", "paper_id": paper_id})
                continue

            target = self.documents_dir / f"arxiv-{entry.arxiv_id.replace('/', '-')}.pdf"
            try:
                self._download_pdf(entry.pdf_url, target)
                report = self.system.ingest_pdf(pdf_path=str(target), title=entry.title, paper_id=paper_id)
                ingested.append(
                    {
                        "arxiv_id": entry.arxiv_id,
                        "paper_id": paper_id,
                        "title": entry.title,
                        "chunk_count": report.get("chunk_count", 0),
                    }
                )
            except Exception as exc:
                failed.append({"arxiv_id": entry.arxiv_id, "paper_id": paper_id, "error": str(exc)})

        return {
            "query": query,
            "fetched": len(fetched),
            "matched": len(filtered),
            "ingested": ingested,
            "skipped": skipped,
            "failed": failed,
            "dry_run": dry_run,
        }

    def fetch(self, query: str, max_results: int = 10) -> list[ArxivEntry]:
        encoded = quote_plus(query.strip())
        api_url = (
            "https://export.arxiv.org/api/query"
            f"?search_query=all:{encoded}&start=0&max_results={max(1, int(max_results))}"
            "&sortBy=submittedDate&sortOrder=descending"
        )
        with urlopen(api_url, timeout=30) as response:
            payload = response.read()
        return self._parse_feed(payload)

    def filter_entries(
        self,
        entries: list[ArxivEntry],
        query: str,
        days_back: int,
        categories: list[str],
        relevance_terms: list[str],
    ) -> list[ArxivEntry]:
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=max(1, int(days_back)))
        category_set = {c.strip().lower() for c in categories if c.strip()}
        relevance = [t.strip().lower() for t in relevance_terms if t.strip()]
        query_terms = [t for t in re.findall(r"[a-zA-Z0-9]+", query.lower()) if len(t) >= 4]

        kept: list[ArxivEntry] = []
        for entry in entries:
            if entry.updated < cutoff:
                continue

            entry_categories = [cat.lower() for cat in entry.categories]
            if category_set and not any(
                (cat in category_set)
                or any(cat.startswith(f"{wanted}.") for wanted in category_set)
                for cat in entry_categories
            ):
                continue

            bag = f"{entry.title} {entry.summary}".lower()
            if relevance and any(term in bag for term in relevance):
                kept.append(entry)
                continue

            # Fallback relevance: accept entries with solid overlap to query intent.
            if query_terms:
                overlap = sum(1 for term in query_terms if term in bag)
                if overlap >= max(1, min(3, len(set(query_terms)) // 3)):
                    kept.append(entry)
                    continue

            # If no explicit relevance terms and no query terms, keep by recency/category only.
            if not relevance and not query_terms:
                kept.append(entry)
                continue
        return kept

    @staticmethod
    def _download_pdf(url: str, target: Path) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        with urlopen(url, timeout=60) as response:
            content = response.read()
        if not content:
            raise ValueError("empty PDF payload from arXiv")
        target.write_bytes(content)

    @staticmethod
    def _parse_feed(payload: bytes) -> list[ArxivEntry]:
        root = ET.fromstring(payload)
        entries: list[ArxivEntry] = []
        for item in root.findall("atom:entry", ATOM_NS):
            id_text = (item.findtext("atom:id", default="", namespaces=ATOM_NS) or "").strip()
            arxiv_id = id_text.rsplit("/", maxsplit=1)[-1]
            arxiv_id = re.sub(r"v\d+$", "", arxiv_id)
            title = " ".join((item.findtext("atom:title", default="", namespaces=ATOM_NS) or "").split())
            summary = " ".join((item.findtext("atom:summary", default="", namespaces=ATOM_NS) or "").split())

            updated_raw = (item.findtext("atom:updated", default="", namespaces=ATOM_NS) or "").strip()
            updated = datetime.fromisoformat(updated_raw.replace("Z", "+00:00")) if updated_raw else datetime.now(timezone.utc)

            pdf_url = ""
            for link in item.findall("atom:link", ATOM_NS):
                title_attr = (link.attrib.get("title") or "").strip().lower()
                href = (link.attrib.get("href") or "").strip()
                if title_attr == "pdf" and href:
                    pdf_url = href
                    break
            if not pdf_url and arxiv_id:
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

            categories = [str(node.attrib.get("term", "")).strip() for node in item.findall("atom:category", ATOM_NS)]
            categories = [cat for cat in categories if cat]

            if arxiv_id and title and pdf_url:
                entries.append(
                    ArxivEntry(
                        arxiv_id=arxiv_id,
                        title=title,
                        summary=summary,
                        updated=updated,
                        pdf_url=pdf_url,
                        categories=categories,
                    )
                )
        return entries
