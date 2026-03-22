from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Protocol, Sequence

from research_rag.domain import AnswerPayload, SearchResult

_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
}
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


class AnswerGenerator(Protocol):
    provider_name: str

    def generate(self, question: str, results: Sequence[SearchResult]) -> AnswerPayload:
        ...


def _terms(text: str) -> set[str]:
    tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {token for token in tokens if len(token) > 2 and token not in _STOPWORDS}


def _default_citations(results: Sequence[SearchResult], limit: int = 3) -> list[dict[str, object]]:
    citations: list[dict[str, object]] = []
    seen: set[str] = set()
    for result in results:
        if result.chunk.chunk_id in seen:
            continue
        seen.add(result.chunk.chunk_id)
        citations.append(
            {
                "document_id": result.chunk.document_id,
                "chunk_id": result.chunk.chunk_id,
                "page_number": result.chunk.page_number,
                "score": round(result.score, 4),
            }
        )
        if len(citations) == limit:
            break
    return citations


class ExtractiveAnswerGenerator:
    provider_name = "extractive"

    def generate(self, question: str, results: Sequence[SearchResult]) -> AnswerPayload:
        if not results:
            return AnswerPayload(
                answer="I could not find any indexed context that answers this question yet.",
                citations=[],
                provider=self.provider_name,
            )

        question_terms = _terms(question)
        ranked_sentences: list[tuple[float, str, SearchResult]] = []
        for result in results:
            sentences = [part.strip() for part in _SENTENCE_SPLIT.split(result.chunk.text) if part.strip()]
            if not sentences:
                sentences = [result.chunk.text]
            for sentence in sentences:
                overlap = len(question_terms & _terms(sentence))
                score = (result.score * 0.75) + (overlap * 0.25)
                ranked_sentences.append((score, sentence, result))

        ranked_sentences.sort(key=lambda item: item[0], reverse=True)
        selected: list[tuple[str, SearchResult]] = []
        seen_sentences: set[str] = set()
        for _, sentence, result in ranked_sentences:
            normalized = sentence.lower()
            if normalized in seen_sentences:
                continue
            seen_sentences.add(normalized)
            selected.append((sentence, result))
            if len(selected) == 3:
                break

        if not selected:
            top = results[0]
            selected = [(top.chunk.text, top)]

        answer = " ".join(sentence for sentence, _ in selected).strip()
        citations = _default_citations([result for _, result in selected], limit=3)
        return AnswerPayload(answer=answer, citations=citations, provider=self.provider_name)


class OpenAIResponsesGenerator:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://api.openai.com/v1",
        timeout_seconds: float = 45.0,
        max_output_tokens: int = 400,
    ) -> None:
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required when GENERATION_PROVIDER=openai")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_output_tokens = max_output_tokens
        self.provider_name = f"openai:{model}"

    def generate(self, question: str, results: Sequence[SearchResult]) -> AnswerPayload:
        if not results:
            return AnswerPayload(
                answer="I could not find any indexed context that answers this question yet.",
                citations=[],
                provider=self.provider_name,
            )

        context_blocks = []
        for result in results:
            context_blocks.append(
                f"[page {result.chunk.page_number} | score {result.score:.3f}]\n{result.chunk.text}"
            )

        payload = {
            "model": self.model,
            "instructions": (
                "You are a careful research assistant. Answer only from the supplied context. "
                "If the context is insufficient, say so clearly. Cite pages inline like [p. 3]."
            ),
            "input": (
                f"Question:\n{question}\n\n"
                f"Context:\n{chr(10).join(context_blocks)}"
            ),
            "temperature": 0.1,
            "max_output_tokens": self.max_output_tokens,
        }
        request = urllib.request.Request(
            url=f"{self.base_url}/responses",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI generation request failed: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"OpenAI generation request could not be completed: {exc}") from exc

        answer_text = self._extract_text(body)
        if not answer_text:
            answer_text = "The model did not return any text for this request."

        return AnswerPayload(
            answer=answer_text.strip(),
            citations=_default_citations(results, limit=3),
            provider=self.provider_name,
        )

    @staticmethod
    def _extract_text(body: dict[str, object]) -> str:
        output_text = body.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text

        parts: list[str] = []
        output_items = body.get("output")
        if not isinstance(output_items, list):
            output_items = []
        for item in output_items:
            if not isinstance(item, dict):
                continue
            content_items = item.get("content")
            if not isinstance(content_items, list):
                content_items = []
            for content in content_items:
                if not isinstance(content, dict):
                    continue
                text = content.get("text")
                if isinstance(text, str):
                    parts.append(text)
                elif isinstance(text, dict):
                    value = text.get("value")
                    if isinstance(value, str):
                        parts.append(value)
        return "\n".join(part.strip() for part in parts if part and part.strip())
