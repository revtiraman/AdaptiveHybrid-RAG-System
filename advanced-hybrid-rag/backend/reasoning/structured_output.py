"""Pydantic response schemas for reasoning outputs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Citation(BaseModel):
	doc_id: str
	doc_title: str
	authors: list[str] = Field(default_factory=list)
	year: int | None = None
	venue: str | None = None
	doi: str | None = None
	chunk_id: str
	page_numbers: list[int] = Field(default_factory=list)
	relevant_excerpt: str
	support_score: float


class SubQuestion(BaseModel):
	question: str
	answer: str
	sources: list[Citation] = Field(default_factory=list)
	confidence: float


class QueryResponse(BaseModel):
	query_id: str
	query: str
	answer: str
	answer_summary: str
	answer_type: str
	citations: list[Citation] = Field(default_factory=list)
	sub_questions: list[SubQuestion] | None = None
	reasoning_trace: list[str] | None = None
	confidence: Literal["HIGH", "MEDIUM", "LOW"] = "MEDIUM"
	grounding_score: float = 0.0
	retrieval_quality: float = 0.0
	warnings: list[str] = Field(default_factory=list)
	latency_ms: float = 0.0
	token_usage: dict[str, int] = Field(default_factory=dict)
	model_used: str = ""
	corrective_iterations: int = 0
	cached: bool = False


class AnnotatedAnswer(BaseModel):
	text_with_inline_cites: str
	bibliography: list[Citation] = Field(default_factory=list)
	uncited_sentences: list[str] = Field(default_factory=list)


class VerificationIssue(BaseModel):
	issue_type: str
	detail: str
	severity: Literal["low", "medium", "high"] = "medium"


class VerificationResult(BaseModel):
	passed: bool
	issues: list[VerificationIssue] = Field(default_factory=list)
	corrective_action: Literal["none", "re_retrieve", "regenerate", "expand_context", "return_with_warning"] = "none"
	grounding_score: float
	citation_accuracy: float


__all__ = [
	"Citation",
	"SubQuestion",
	"QueryResponse",
	"AnnotatedAnswer",
	"VerificationIssue",
	"VerificationResult",
]
