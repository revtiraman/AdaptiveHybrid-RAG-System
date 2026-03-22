"""Knowledge graph API routes."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api/graph", tags=["graph"])


class CypherRequest(BaseModel):
	cypher: str


@router.get("/entities")
async def entities(request: Request):
	graph = request.app.state.graph_store
	neighbors = await graph.find_entity_neighbors("BERT")
	return {"entities": neighbors}


@router.get("/entity/{name}")
async def entity(request: Request, name: str):
	graph = request.app.state.graph_store
	return {"entity": name, "neighbors": await graph.find_entity_neighbors(name)}


@router.get("/citation-network")
async def citation_network(request: Request, doc_id: str | None = None):
	graph = request.app.state.graph_store
	if doc_id is None:
		docs = request.app.state.relational_store.list_documents()
		doc_id = docs[0]["doc_id"] if docs else ""
	return await graph.get_citation_network(doc_id)


@router.post("/query")
async def graph_query(request: Request, body: CypherRequest):
	graph = request.app.state.graph_store
	return await graph.cypher_query(body.cypher)


__all__ = ["router"]
