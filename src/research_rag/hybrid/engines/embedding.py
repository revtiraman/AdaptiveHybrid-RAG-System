from __future__ import annotations

# pyright: reportMissingImports=false

import math
import re
from hashlib import sha256
from typing import Sequence


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vector))
    if norm == 0:
        return vector
    return [v / norm for v in vector]


class BGEEmbedder:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model = None
        self._fallback_dimension = 384

        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(model_name)
        except ModuleNotFoundError:
            self._model = None

    @property
    def provider_name(self) -> str:
        if self._model is None:
            return "hash-fallback"
        return f"sentence-transformers:{self.model_name}"

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        if self._model is None:
            return [self._hash_embed(text) for text in texts]

        vectors = self._model.encode(
            list(texts),
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return [vector.astype(float).tolist() for vector in vectors]

    def _hash_embed(self, text: str) -> list[float]:
        vector = [0.0] * self._fallback_dimension
        for token in re.findall(r"[a-zA-Z0-9]+", text.lower()):
            digest = sha256(token.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:2], "big") % self._fallback_dimension
            sign = 1.0 if digest[3] % 2 == 0 else -1.0
            vector[idx] += sign
        return _normalize(vector)


class CrossEncoderReranker:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model = None
        try:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(model_name)
        except ModuleNotFoundError:
            self._model = None

    @property
    def provider_name(self) -> str:
        if self._model is None:
            return "lexical-rerank-fallback"
        return f"cross-encoder:{self.model_name}"

    def score(self, query: str, passages: list[str]) -> list[float]:
        if not passages:
            return []
        if self._model is None:
            query_terms = set(re.findall(r"[a-zA-Z0-9]+", query.lower()))
            scores: list[float] = []
            for passage in passages:
                passage_terms = set(re.findall(r"[a-zA-Z0-9]+", passage.lower()))
                overlap = len(query_terms & passage_terms)
                scores.append(float(overlap))
            return scores

        pairs = [[query, passage] for passage in passages]
        values = self._model.predict(pairs)
        return [float(v) for v in values]
