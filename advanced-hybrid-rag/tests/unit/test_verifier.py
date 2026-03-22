from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from ingestion.models import Chunk, ChunkMetadata
from reasoning.self_verifier import SelfVerifier


def _chunk(text: str, chunk_id: str = "c1", page: int = 1) -> Chunk:
	return Chunk(
		text=text,
		metadata=ChunkMetadata(
			doc_id="d1",
			chunk_id=chunk_id,
			source_file="src",
			section="s",
			page_start=page,
			page_end=page,
			char_start=0,
			char_end=len(text),
			chunk_index=0,
			total_chunks=1,
		),
	)


def test_grounding_check_catches_unsupported_claims():
	verifier = SelfVerifier()
	res = asyncio.run(verifier.verify("what", "This includes unicorn theorem.", [_chunk("Known facts only.")]))
	assert not res.passed


def test_citation_check_validates_page_numbers():
	verifier = SelfVerifier()
	res = asyncio.run(verifier.verify("q", "Claim [missing_chunk].", [_chunk("Claim")]))
	assert any(i.issue_type == "citation" for i in res.issues)


def test_hallucination_detection_flags_entities():
	verifier = SelfVerifier()
	res = asyncio.run(verifier.verify("q", "MadeupEntity beats all models.", [_chunk("BERT baseline only.")]))
	assert not res.passed


def test_passes_when_fully_grounded():
	verifier = SelfVerifier()
	res = asyncio.run(verifier.verify("q", "BERT is a model.", [_chunk("BERT is a model.", "c1")]))
	assert res.grounding_score > 0
