from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

JsonDict = dict[str, Any]


@dataclass(slots=True)
class PaperRecord:
    paper_id: str
    title: str
    source_path: str
    checksum: str
    page_count: int
    chunk_count: int
    created_at: str
    updated_at: str


@dataclass(slots=True)
class SectionChunk:
    chunk_id: str
    paper_id: str
    page_number: int
    section: str
    ordinal: int
    text: str
    char_count: int
    metadata: JsonDict = field(default_factory=dict)


@dataclass(slots=True)
class ClaimRecord:
    claim_id: str
    paper_id: str
    chunk_id: str
    claim: str
    claim_type: Literal["result", "method", "definition", "comparison", "limitation"]
    section: str
    page_number: int
    entities: list[str] = field(default_factory=list)
    confidence: float = 0.0
    metadata: JsonDict = field(default_factory=dict)


@dataclass(slots=True)
class RetrievalCandidate:
    chunk: SectionChunk
    vector_rank: int | None
    bm25_rank: int | None
    vector_score: float
    bm25_score: float
    rrf_score: float
    rerank_score: float = 0.0
    claim_text: str | None = None
    context_type: Literal["chunk", "claim"] = "chunk"


@dataclass(slots=True)
class QueryPlan:
    query_type: Literal["simple", "multi_hop"]
    hops: list[str]


@dataclass(slots=True)
class VerificationResult:
    supported: bool
    confidence: float
    unsupported_claims: list[str]
    issues: list[dict[str, str]] = field(default_factory=list)
    stage_scores: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class AnswerClaim:
    claim: str
    citations: list[dict[str, Any]]


@dataclass(slots=True)
class QueryResult:
    question: str
    query_type: str
    hops: list[str]
    answer: str
    claims: list[AnswerClaim]
    citations: list[dict[str, Any]]
    retrieval_quality: float
    retries: int
    latency_ms: int
    diagnostic: JsonDict

    def to_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "query_type": self.query_type,
            "hops": self.hops,
            "answer": self.answer,
            "claims": [{"claim": c.claim, "citations": c.citations} for c in self.claims],
            "citations": self.citations,
            "retrieval_quality": self.retrieval_quality,
            "retries": self.retries,
            "latency_ms": self.latency_ms,
            "diagnostic": self.diagnostic,
        }
