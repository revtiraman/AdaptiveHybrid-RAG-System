"""Document management routes."""

from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/papers", tags=["papers"])


@router.get("")
async def list_papers(request: Request):
	store = request.app.state.relational_store
	return store.list_documents()


@router.get("/{doc_id}")
async def get_paper(request: Request, doc_id: str):
	rows = request.app.state.relational_store.list_documents()
	for row in rows:
		if row.get("doc_id") == doc_id:
			return row
	return {"detail": "not found"}


@router.delete("/{doc_id}")
async def delete_paper(request: Request, doc_id: str):
	ok = await request.app.state.pipeline.delete_document(doc_id)
	return {"deleted": ok, "doc_id": doc_id}


@router.get("/{doc_id}/chunks")
async def list_chunks(request: Request, doc_id: str):
	conn = __import__("sqlite3").connect(request.app.state.relational_store.db_path)
	conn.row_factory = __import__("sqlite3").Row
	try:
		rows = conn.execute("SELECT * FROM chunks WHERE doc_id = ? ORDER BY chunk_index", (doc_id,)).fetchall()
		return [dict(r) for r in rows]
	finally:
		conn.close()


@router.get("/search")
async def search_papers(request: Request, q: str):
	rows = request.app.state.relational_store.list_documents()
	ql = q.lower()
	return [r for r in rows if ql in str(r.get("title", "")).lower()]


__all__ = ["router"]
