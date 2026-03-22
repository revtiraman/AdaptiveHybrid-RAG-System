"""Citation graph analytics helpers."""

from __future__ import annotations

import networkx as nx


class CitationAnalysis:
    """Compute influence metrics over citation networks."""

    def build_graph(self, edges: list[tuple[str, str]]) -> nx.DiGraph:
        g = nx.DiGraph()
        g.add_edges_from(edges)
        return g

    def metrics(self, graph: nx.DiGraph) -> dict:
        return {
            "pagerank": nx.pagerank(graph) if graph.number_of_nodes() else {},
            "betweenness": nx.betweenness_centrality(graph) if graph.number_of_nodes() else {},
            "in_degree": dict(graph.in_degree()),
            "out_degree": dict(graph.out_degree()),
        }


__all__ = ["CitationAnalysis"]
