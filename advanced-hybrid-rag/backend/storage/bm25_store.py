"""Sparse BM25 index management."""

from __future__ import annotations

import pickle
import re
from pathlib import Path
from threading import RLock

from pydantic import BaseModel

from ..ingestion.models import Chunk


class BM25Result(BaseModel):
	chunk: Chunk
	score: float


class BM25Store:
	"""Thread-safe BM25 index with disk persistence."""

	def __init__(self, index_path: str | Path = "data/bm25_index.pkl") -> None:
		self.index_path = Path(index_path)
		self.lock = RLock()
		self.chunks: list[Chunk] = []
		self.tokens: list[list[str]] = []
		self._bm25 = None
		self._stemmer = self._build_stemmer()
		self._stopwords = self._build_stopwords()
		self._load()

	def search(self, query: str, k: int) -> list[BM25Result]:
		with self.lock:
			if not self.chunks:
				return []
			query_tokens = self._tokenize(query)
			if not query_tokens:
				return []

			if self._bm25 is not None:
				scores = self._bm25.get_scores(query_tokens)
			else:
				scores = [self._fallback_score(query_tokens, token_list) for token_list in self.tokens]

			ranked = sorted(enumerate(scores), key=lambda x: float(x[1]), reverse=True)[:k]
			return [BM25Result(chunk=self.chunks[idx], score=float(score)) for idx, score in ranked]

	def add_chunks(self, chunks: list[Chunk]) -> None:
		with self.lock:
			by_id = {c.metadata.chunk_id: c for c in self.chunks}
			for chunk in chunks:
				by_id[chunk.metadata.chunk_id] = chunk
			self.chunks = list(by_id.values())
			self.rebuild_index()

	def remove_document(self, doc_id: str) -> None:
		with self.lock:
			self.chunks = [c for c in self.chunks if c.metadata.doc_id != doc_id]
			self.rebuild_index()

	def rebuild_index(self) -> None:
		with self.lock:
			self.tokens = [self._tokenize(chunk.text) for chunk in self.chunks]
			try:
				from rank_bm25 import BM25Okapi

				self._bm25 = BM25Okapi(self.tokens)
			except Exception:
				self._bm25 = None
			self._save()

	def _tokenize(self, text: str) -> list[str]:
		words = re.findall(r"\b[a-z0-9]+\b", text.lower())
		filtered = [w for w in words if w not in self._stopwords]
		if self._stemmer is None:
			return filtered
		return [self._stemmer.stem(w) for w in filtered]

	def _fallback_score(self, query_tokens: list[str], doc_tokens: list[str]) -> float:
		if not doc_tokens:
			return 0.0
		doc_set = set(doc_tokens)
		overlap = sum(1 for t in query_tokens if t in doc_set)
		return overlap / max(1, len(query_tokens))

	def _build_stemmer(self):
		try:
			from nltk.stem import PorterStemmer

			return PorterStemmer()
		except Exception:
			return None

	def _build_stopwords(self) -> set[str]:
		return {
			"a",
			"an",
			"the",
			"and",
			"or",
			"to",
			"of",
			"in",
			"for",
			"on",
			"is",
			"are",
			"was",
			"were",
			"be",
			"with",
			"as",
			"by",
			"at",
		}

	def _save(self) -> None:
		self.index_path.parent.mkdir(parents=True, exist_ok=True)
		payload = {"chunks": [c.model_dump() for c in self.chunks]}
		with self.index_path.open("wb") as f:
			pickle.dump(payload, f)

	def _load(self) -> None:
		if not self.index_path.exists():
			return
		try:
			with self.index_path.open("rb") as f:
				payload = pickle.load(f)
			self.chunks = [Chunk.model_validate(c) for c in payload.get("chunks", [])]
			self.rebuild_index()
		except Exception:
			self.chunks = []
			self.tokens = []
			self._bm25 = None


__all__ = ["BM25Store", "BM25Result"]
