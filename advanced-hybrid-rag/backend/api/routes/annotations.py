"""Annotation APIs for collaborative review."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from ...storage.annotation_store import Annotation

router = APIRouter(prefix="/api/annotations", tags=["annotations"])


class AnnotationRequest(BaseModel):
    document_id: str
    chunk_id: str
    note: str
    label: str = "general"
    user_id: str = "anonymous"
    public: bool = False


@router.post("")
async def create_annotation(request: Request, payload: AnnotationRequest) -> dict:
    store = request.app.state.annotation_store
    store.add(
        Annotation(
            doc_id=payload.document_id,
            chunk_id=payload.chunk_id,
            text=payload.note,
            annotation=payload.label,
            user_id=payload.user_id,
            public=payload.public,
        )
    )
    return {
        "status": "created",
        "document_id": payload.document_id,
        "chunk_id": payload.chunk_id,
        "label": payload.label,
    }


@router.get("/{document_id}")
async def list_annotations(request: Request, document_id: str) -> dict:
    store = request.app.state.annotation_store
    anns = store.by_doc(document_id)
    return {
        "document_id": document_id,
        "annotations": [
            {
                "chunk_id": a.chunk_id,
                "label": a.annotation,
                "note": a.text,
                "user_id": a.user_id,
                "public": a.public,
            }
            for a in anns
        ],
    }
