"""Debug endpoints for inspecting retrieved chunk quality."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Request

router = APIRouter(prefix="/api/debug", tags=["debug"])


@router.get("/chunk-sample")
async def chunk_sample(
    request: Request,
    doc_id: str = Query(..., min_length=1),
    limit: int = Query(default=5, ge=1, le=50),
) -> dict:
    store = request.app.state.relational_store
    db_path = Path(getattr(store, "db_path", ""))
    if not db_path.exists():
        raise HTTPException(status_code=404, detail="Metadata database not found.")

    rows = _read_chunk_rows(db_path, doc_id, limit)
    chunks = []
    for row in rows:
        text = row["text"] or ""
        chars = max(1, len(text))
        chunks.append(
            {
                "chunk_id": row["chunk_id"],
                "section": row["section"],
                "page": row["page_start"],
                "text_preview": text[:300],
                "text_has_spaces": (len(text.split()) / chars) > 0.1,
                "looks_like_reference": _looks_like_reference(text),
            }
        )

    return {"chunks": chunks}


def _read_chunk_rows(db_path: Path, doc_id: str, limit: int) -> list[sqlite3.Row]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT chunk_id, section, page_start, text
            FROM chunks
            WHERE doc_id = ?
            ORDER BY chunk_index ASC
            LIMIT ?
            """,
            (doc_id, limit),
        ).fetchall()
        return list(rows)
    finally:
        conn.close()


def _looks_like_reference(text: str) -> bool:
    return bool(
        re.search(r"\[\d+\]\s+[A-Z][a-z]+", text)
        or re.search(r"(?m)^\s*\d+\.\s+[A-Z][a-z]+.+\(\d{4}\)", text)
    )


__all__ = ["router"]
