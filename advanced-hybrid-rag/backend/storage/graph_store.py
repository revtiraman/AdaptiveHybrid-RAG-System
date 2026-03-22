"""Knowledge graph storage with Neo4j and in-memory fallback."""

from __future__ import annotations

from typing import Any

import networkx as nx

from ..ingestion.models import Chunk, ChunkMetadata, ProcessedDocument


class Neo4jGraphStore:
	"""Store document/entity graph in Neo4j, with networkx fallback for local runs."""

	def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "password") -> None:
		self.uri = uri
		self.user = user
		self.password = password
		self._driver = None
		self._graph = nx.MultiDiGraph()

	async def add_document_graph(self, doc: ProcessedDocument) -> None:
		driver = await self._get_driver()
		if driver is None:
			self._add_doc_memory(doc)
			return
		async with driver.session() as session:
			await session.run(
				"MERGE (d:Document {doc_id:$doc_id}) SET d.title=$title, d.year=$year, d.venue=$venue, d.doi=$doi",
				doc_id=doc.metadata.doc_id,
				title=doc.metadata.title,
				year=doc.metadata.year,
				venue=doc.metadata.venue,
				doi=doc.metadata.doi,
			)

	async def add_entities(self, doc_id: str, entities: list[str]) -> None:
		driver = await self._get_driver()
		if driver is None:
			for entity in entities:
				self._graph.add_node(entity, type="Entity")
				self._graph.add_edge(doc_id, entity, rel="USES")
			return
		async with driver.session() as session:
			for entity in entities:
				await session.run(
					"""
					MERGE (d:Document {doc_id:$doc_id})
					MERGE (e:Entity {name:$name})
					MERGE (d)-[:USES]->(e)
					""",
					doc_id=doc_id,
					name=entity,
				)

	async def search_related(self, query: str, depth: int = 2) -> list[Chunk]:
		neighbors = await self.find_entity_neighbors(query)
		chunks: list[Chunk] = []
		for idx, node in enumerate(neighbors):
			text = f"Related entity: {node.get('name', 'unknown')}"
			chunks.append(
				Chunk(
					text=text,
					metadata=ChunkMetadata(
						doc_id=node.get("doc_id", "graph"),
						chunk_id=f"graph-{idx}",
						source_file="graph",
						section="Knowledge Graph",
						page_start=1,
						page_end=1,
						char_start=0,
						char_end=len(text),
						chunk_index=idx,
						total_chunks=len(neighbors),
					),
				)
			)
		return chunks

	async def find_entity_neighbors(self, entity: str) -> list[dict[str, Any]]:
		driver = await self._get_driver()
		if driver is None:
			if entity not in self._graph:
				return []
			return [{"name": n} for n in self._graph.neighbors(entity)]
		async with driver.session() as session:
			result = await session.run(
				"MATCH (e:Entity {name:$name})--(n) RETURN n LIMIT 20",
				name=entity,
			)
			rows = await result.data()
			return [r.get("n", {}) for r in rows]

	async def get_citation_network(self, doc_id: str) -> dict[str, Any]:
		if doc_id in self._graph:
			nodes = [{"id": n} for n in self._graph.nodes]
			edges = [{"source": s, "target": t} for s, t in self._graph.edges]
			return {"nodes": nodes, "edges": edges}
		driver = await self._get_driver()
		if driver is None:
			return {"nodes": [], "edges": []}
		async with driver.session() as session:
			result = await session.run(
				"""
				MATCH (d:Document {doc_id:$doc_id})-[:CITES]->(c:Document)
				RETURN d.doc_id AS source, c.doc_id AS target
				""",
				doc_id=doc_id,
			)
			rows = await result.data()
			nodes = sorted({r["source"] for r in rows} | {r["target"] for r in rows})
			return {
				"nodes": [{"id": n} for n in nodes],
				"edges": [{"source": r["source"], "target": r["target"]} for r in rows],
			}

	async def cypher_query(self, cypher: str) -> list[dict]:
		driver = await self._get_driver()
		if driver is None:
			return []
		async with driver.session() as session:
			result = await session.run(cypher)
			return await result.data()

	async def delete_document(self, doc_id: str) -> None:
		if doc_id in self._graph:
			self._graph.remove_node(doc_id)
		driver = await self._get_driver()
		if driver is None:
			return
		async with driver.session() as session:
			await session.run("MATCH (d:Document {doc_id:$doc_id}) DETACH DELETE d", doc_id=doc_id)

	async def _get_driver(self):
		if self._driver is not None:
			return self._driver
		try:
			from neo4j import AsyncGraphDatabase

			self._driver = AsyncGraphDatabase.driver(self.uri, auth=(self.user, self.password))
			return self._driver
		except Exception:
			return None

	def _add_doc_memory(self, doc: ProcessedDocument) -> None:
		doc_id = doc.metadata.doc_id
		self._graph.add_node(doc_id, type="Document", title=doc.metadata.title)
		for author in doc.metadata.authors:
			self._graph.add_node(author, type="Author")
			self._graph.add_edge(doc_id, author, rel="WRITTEN_BY")


__all__ = ["Neo4jGraphStore"]
