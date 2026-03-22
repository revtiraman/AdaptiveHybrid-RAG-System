"""Web ingestion utilities with article-first extraction and arXiv support."""

from __future__ import annotations

import asyncio
import re
import tempfile
import time
import urllib.parse
import urllib.robotparser
from pathlib import Path

import httpx

from .models import DocumentMetadata, ProcessedDocument, Section
from .pdf_processor import PDFProcessor


class WebScraper:
	"""Scrape web pages and arXiv resources into ProcessedDocument objects."""

	def __init__(self, pdf_processor: PDFProcessor | None = None) -> None:
		self.pdf_processor = pdf_processor or PDFProcessor()
		self._last_domain_request: dict[str, float] = {}

	async def scrape_url(self, url: str) -> ProcessedDocument:
		"""Fetch and parse a URL with fallbacks for dynamic pages."""
		await self._wait_for_rate_limit(url)
		if not self._is_allowed_by_robots(url):
			raise PermissionError(f"robots.txt disallows scraping: {url}")

		if "arxiv.org/abs/" in url:
			arxiv_id = url.rstrip("/").split("/")[-1]
			return await self.scrape_arxiv(arxiv_id)

		text = await self._extract_with_trafilatura(url)
		html = ""
		if len(text) < 500:
			html = await self._fetch_html(url)
			text = self._extract_main_text_from_html(html)
		if len(text) < 500:
			html = await self._extract_with_playwright(url)
			text = self._extract_main_text_from_html(html)

		title = self._extract_title(html) if html else url
		metadata = DocumentMetadata(
			doc_id=f"web-{abs(hash(url))}",
			source=url,
			title=title,
		)
		return ProcessedDocument(
			raw_text=text,
			sections=[Section(name="Web Content", text=text, page_start=1, page_end=1)],
			metadata=metadata,
		)

	async def scrape_arxiv(self, arxiv_id: str) -> ProcessedDocument:
		"""Download and process arXiv paper PDF with metadata enrichment."""
		pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
		abs_url = f"https://arxiv.org/abs/{arxiv_id}"

		async with httpx.AsyncClient(timeout=60) as client:
			pdf_response = await client.get(pdf_url)
			pdf_response.raise_for_status()
			abs_response = await client.get(abs_url)
			abs_html = abs_response.text if abs_response.status_code == 200 else ""

		with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
			tmp.write(pdf_response.content)
			tmp_path = Path(tmp.name)

		processed = self.pdf_processor.process(tmp_path)
		title = self._extract_title(abs_html) or processed.metadata.title
		categories = re.findall(r"(?i)subjects?:\s*([^<\n]+)", abs_html)
		processed.metadata.title = title
		processed.metadata.categories = [c.strip() for c in categories]
		processed.metadata.source = abs_url
		return processed

	async def _extract_with_trafilatura(self, url: str) -> str:
		"""Prefer trafilatura for article-friendly extraction quality."""
		try:
			import trafilatura  # type: ignore

			downloaded = await asyncio.to_thread(trafilatura.fetch_url, url)
			if not downloaded:
				return ""
			extracted = await asyncio.to_thread(trafilatura.extract, downloaded)
			return extracted or ""
		except Exception:
			return ""

	async def _extract_with_playwright(self, url: str) -> str:
		"""Fallback for JS-heavy pages using Playwright."""
		try:
			from playwright.async_api import async_playwright  # type: ignore

			async with async_playwright() as p:
				browser = await p.chromium.launch(headless=True)
				page = await browser.new_page()
				await page.goto(url, wait_until="networkidle", timeout=45000)
				html = await page.content()
				await browser.close()
				return html
		except Exception:
			return ""

	async def _fetch_html(self, url: str) -> str:
		async with httpx.AsyncClient(timeout=30) as client:
			resp = await client.get(url)
			if resp.status_code >= 400:
				return ""
			return resp.text

	def _extract_main_text_from_html(self, html: str) -> str:
		"""Extract likely main content from HTML via broad selectors."""
		if not html:
			return ""
		try:
			from bs4 import BeautifulSoup  # type: ignore

			soup = BeautifulSoup(html, "html.parser")
			for selector in ["article", "main", ".content", "#content", "body"]:
				nodes = soup.select(selector)
				if nodes:
					text = "\n".join(node.get_text(" ", strip=True) for node in nodes)
					if len(text) > 200:
						return text
			return soup.get_text(" ", strip=True)
		except Exception:
			return re.sub(r"\s+", " ", html)

	def _extract_title(self, html: str) -> str:
		match = re.search(r"<title>(.*?)</title>", html, flags=re.I | re.S)
		if not match:
			return ""
		return re.sub(r"\s+", " ", match.group(1)).strip()

	async def _wait_for_rate_limit(self, url: str) -> None:
		parsed = urllib.parse.urlparse(url)
		domain = parsed.netloc
		now = time.monotonic()
		last = self._last_domain_request.get(domain, 0.0)
		delta = now - last
		if delta < 1.0:
			await asyncio.sleep(1.0 - delta)
		self._last_domain_request[domain] = time.monotonic()

	def _is_allowed_by_robots(self, url: str) -> bool:
		parsed = urllib.parse.urlparse(url)
		robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
		rp = urllib.robotparser.RobotFileParser()
		try:
			rp.set_url(robots_url)
			rp.read()
			return rp.can_fetch("*", url)
		except Exception:
			return True


__all__ = ["WebScraper"]
