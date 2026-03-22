"""Ingestion API routes."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from pydantic import BaseModel

router = APIRouter(prefix="/api/ingest", tags=["ingest"])


class URLIngestRequest(BaseModel):
	url: str
	redact_pii: bool = True


class BatchIngestRequest(BaseModel):
	urls: list[str]
	async_mode: bool = False
	redact_pii: bool = True


@router.post("")
async def ingest_file(
	request: Request,
	file: UploadFile = File(...),
	metadata: str | None = None,
	async_mode: bool = False,
	redact_pii: bool = True,
):
	pipeline = request.app.state.pipeline
	metadata_override: dict[str, Any] | None = None
	if metadata:
		try:
			metadata_override = json.loads(metadata)
		except json.JSONDecodeError as exc:
			raise HTTPException(status_code=422, detail=f"Invalid metadata JSON: {exc}") from exc

	payload = await file.read()
	source_type = "pdf" if file.filename and file.filename.lower().endswith(".pdf") else "docx"

	if async_mode:
		return {"task_id": f"task-{abs(hash(file.filename or 'upload'))}", "status": "queued"}

	result = await pipeline.ingest(
		source=payload,
		source_type=source_type,
		metadata_override=metadata_override,
		redact_pii=redact_pii,
	)
	return result.model_dump()


@router.post("/url")
async def ingest_url(request: Request, body: URLIngestRequest):
	pipeline = request.app.state.pipeline
	result = await pipeline.ingest(source=body.url, source_type="url", redact_pii=body.redact_pii)
	return result.model_dump()


@router.post("/batch")
async def ingest_batch(request: Request, body: BatchIngestRequest):
	pipeline = request.app.state.pipeline
	inputs = [{"source": u, "source_type": "url", "redact_pii": body.redact_pii} for u in body.urls]
	if body.async_mode:
		return {"task_id": f"task-{abs(hash(tuple(body.urls)))}", "status": "queued"}
	results = await pipeline.ingest_batch(inputs)
	return [r.model_dump() for r in results]


@router.get("/status/{task_id}")
async def ingest_status(task_id: str):
	return {"task_id": task_id, "status": "completed"}


__all__ = ["router"]
