from __future__ import annotations

import hashlib
import json
import math
import re
import urllib.error
import urllib.request
from typing import Protocol, Sequence


class EmbeddingProvider(Protocol):
    provider_name: str

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        ...


def _normalize(vector: list[float]) -> list[float]:
    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude == 0:
        return vector
    return [value / magnitude for value in vector]


class HashingEmbeddingProvider:
    provider_name = "hash"

    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed_single(text) for text in texts]

    def _embed_single(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        for token in re.findall(r"[a-zA-Z0-9]+", text.lower()):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:2], "big") % self.dimension
            sign = 1.0 if digest[2] % 2 == 0 else -1.0
            weight = 1.0 + (digest[3] / 255.0)
            vector[index] += sign * weight
        return _normalize(vector)


class OpenAIEmbeddingProvider:
    provider_name = "openai"

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://api.openai.com/v1",
        timeout_seconds: float = 45.0,
        batch_size: int = 32,
    ) -> None:
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.batch_size = batch_size
        self.provider_name = f"openai:{model}"

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        embeddings: list[list[float]] = []
        for start in range(0, len(texts), self.batch_size):
            batch = list(texts[start : start + self.batch_size])
            if not batch:
                continue
            embeddings.extend(self._request_embeddings(batch))
        return embeddings

    def _request_embeddings(self, batch: list[str]) -> list[list[float]]:
        payload = json.dumps({"input": batch, "model": self.model}).encode("utf-8")
        request = urllib.request.Request(
            url=f"{self.base_url}/embeddings",
            data=payload,
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
            raise RuntimeError(f"OpenAI embeddings request failed: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"OpenAI embeddings request could not be completed: {exc}") from exc

        items = sorted(body.get("data", []), key=lambda item: item.get("index", 0))
        if not items:
            raise RuntimeError("OpenAI embeddings request succeeded but returned no embeddings.")
        return [item["embedding"] for item in items]
