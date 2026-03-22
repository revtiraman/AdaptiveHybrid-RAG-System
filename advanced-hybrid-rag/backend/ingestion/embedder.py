"""Embedding interfaces and provider implementations."""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod

import numpy as np


class BaseEmbedder(ABC):
	"""Abstract embedding interface used by the ingestion pipeline."""

	@abstractmethod
	def embed_documents(self, texts: list[str]) -> np.ndarray:
		"""Embed document texts."""

	@abstractmethod
	def embed_query(self, text: str) -> np.ndarray:
		"""Embed a query string."""


class BGEEmbedder(BaseEmbedder):
	"""BGE-based embedder with deterministic fallback when model is unavailable."""

	def __init__(self, model_name: str = "BAAI/bge-large-en-v1.5", device: str = "cpu", batch_size: int = 32) -> None:
		self.model_name = model_name
		self.device = device
		self.batch_size = batch_size
		self._model = None

	def _get_model(self):
		if self._model is not None:
			return self._model
		try:
			from sentence_transformers import SentenceTransformer

			self._model = SentenceTransformer(self.model_name, device=self.device)
		except Exception:
			self._model = None
		return self._model

	def embed_documents(self, texts: list[str]) -> np.ndarray:
		model = self._get_model()
		if model is not None:
			emb = model.encode(texts, batch_size=self.batch_size, normalize_embeddings=True)
			return np.asarray(emb, dtype=np.float32)
		return np.vstack([_stable_hash_embedding(t) for t in texts]) if texts else np.zeros((0, 384), dtype=np.float32)

	def embed_query(self, text: str) -> np.ndarray:
		model = self._get_model()
		query_text = f"Represent this sentence for searching: {text}"
		if model is not None:
			emb = model.encode([query_text], batch_size=1, normalize_embeddings=True)[0]
			return np.asarray(emb, dtype=np.float32)
		return _stable_hash_embedding(query_text)


class OpenAIEmbedder(BaseEmbedder):
	"""OpenAI embedding implementation with chunked API calls."""

	def __init__(self, model: str = "text-embedding-3-large") -> None:
		self.model = model

	def embed_documents(self, texts: list[str]) -> np.ndarray:
		try:
			from openai import OpenAI
			from tenacity import retry, stop_after_attempt, wait_exponential

			client = OpenAI()

			@retry(wait=wait_exponential(multiplier=1, min=1, max=20), stop=stop_after_attempt(5))
			def _call(batch: list[str]):
				return client.embeddings.create(model=self.model, input=batch)

			vectors: list[list[float]] = []
			for i in range(0, len(texts), 100):
				batch = texts[i : i + 100]
				response = _call(batch)
				vectors.extend(item.embedding for item in response.data)
			return _normalize(np.asarray(vectors, dtype=np.float32))
		except Exception:
			return np.vstack([_stable_hash_embedding(t) for t in texts]) if texts else np.zeros((0, 384), dtype=np.float32)

	def embed_query(self, text: str) -> np.ndarray:
		return self.embed_documents([text])[0]


class CohereEmbedder(BaseEmbedder):
	"""Cohere embedding implementation with search_document/search_query modes."""

	def __init__(self, model: str = "embed-english-v3.0") -> None:
		self.model = model

	def embed_documents(self, texts: list[str]) -> np.ndarray:
		try:
			import cohere  # type: ignore

			client = cohere.Client()
			response = client.embed(texts=texts, model=self.model, input_type="search_document")
			return _normalize(np.asarray(response.embeddings, dtype=np.float32))
		except Exception:
			return np.vstack([_stable_hash_embedding(t) for t in texts]) if texts else np.zeros((0, 384), dtype=np.float32)

	def embed_query(self, text: str) -> np.ndarray:
		try:
			import cohere  # type: ignore

			client = cohere.Client()
			response = client.embed(texts=[text], model=self.model, input_type="search_query")
			return _normalize(np.asarray(response.embeddings, dtype=np.float32))[0]
		except Exception:
			return _stable_hash_embedding(text)


class EmbedderFactory:
	"""Factory for selecting embedding backends."""

	@staticmethod
	def create(provider: str, **kwargs) -> BaseEmbedder:
		provider_norm = provider.strip().lower()
		if provider_norm in {"bge", "sentence-transformers", "local"}:
			return BGEEmbedder(**kwargs)
		if provider_norm == "openai":
			return OpenAIEmbedder(**kwargs)
		if provider_norm == "cohere":
			return CohereEmbedder(**kwargs)
		raise ValueError(f"Unsupported embedder provider: {provider}")


def _normalize(arr: np.ndarray) -> np.ndarray:
	norms = np.linalg.norm(arr, axis=1, keepdims=True)
	norms[norms == 0] = 1.0
	return arr / norms


def _stable_hash_embedding(text: str, dim: int = 384) -> np.ndarray:
	digest = hashlib.sha256(text.encode("utf-8")).digest()
	seed = int.from_bytes(digest[:8], "big", signed=False)
	rng = np.random.default_rng(seed)
	vec = rng.standard_normal(dim).astype(np.float32)
	norm = np.linalg.norm(vec) or 1.0
	return vec / norm


__all__ = ["BaseEmbedder", "BGEEmbedder", "OpenAIEmbedder", "CohereEmbedder", "EmbedderFactory"]
