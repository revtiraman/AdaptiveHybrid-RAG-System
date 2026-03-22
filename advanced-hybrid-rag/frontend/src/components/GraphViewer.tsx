import { useEffect, useMemo, useRef } from "react";

import * as d3 from "d3";

import { useRAGStore } from "../store/ragStore";

export default function GraphViewer() {
	const { graphData } = useRAGStore();
	const svgRef = useRef<SVGSVGElement | null>(null);

	const data = useMemo(() => {
		if (graphData && graphData.nodes.length > 0) {
			return graphData;
		}
		return {
			nodes: [
				{ id: "Query" },
				{ id: "Retriever" },
				{ id: "Reasoner" },
				{ id: "Citations" },
			],
			edges: [
				{ source: "Query", target: "Retriever" },
				{ source: "Retriever", target: "Reasoner" },
				{ source: "Reasoner", target: "Citations" },
			],
		};
	}, [graphData]);

	useEffect(() => {
		if (!svgRef.current) return;

		const width = 720;
		const height = 320;
		const svg = d3.select(svgRef.current);
		svg.selectAll("*").remove();

		svg.attr("viewBox", `0 0 ${width} ${height}`);

		const nodes = data.nodes.map((n) => ({ ...n }));
		const links = data.edges.map((l) => ({ ...l }));

		const simulation = d3
			.forceSimulation(nodes as d3.SimulationNodeDatum[])
			.force("link", d3.forceLink(links).id((d: any) => d.id).distance(90))
			.force("charge", d3.forceManyBody().strength(-190))
			.force("center", d3.forceCenter(width / 2, height / 2));

		const link = svg
			.append("g")
			.attr("stroke", "#95a1ad")
			.attr("stroke-opacity", 0.85)
			.selectAll("line")
			.data(links)
			.enter()
			.append("line")
			.attr("stroke-width", 1.6);

		const node = svg
			.append("g")
			.selectAll("circle")
			.data(nodes)
			.enter()
			.append("circle")
			.attr("r", 10)
			.attr("fill", "#2563eb")
			.call(
				d3
					.drag<SVGCircleElement, any>()
					.on("start", (event, d) => {
						if (!event.active) simulation.alphaTarget(0.3).restart();
						d.fx = d.x;
						d.fy = d.y;
					})
					.on("drag", (event, d) => {
						d.fx = event.x;
						d.fy = event.y;
					})
					.on("end", (event, d) => {
						if (!event.active) simulation.alphaTarget(0);
						d.fx = null;
						d.fy = null;
					}),
			);

		const labels = svg
			.append("g")
			.selectAll("text")
			.data(nodes)
			.enter()
			.append("text")
			.text((d: any) => d.id)
			.attr("font-size", 11)
			.attr("fill", "#1f2937")
			.attr("dx", 13)
			.attr("dy", 4);

		simulation.on("tick", () => {
			link
				.attr("x1", (d: any) => d.source.x)
				.attr("y1", (d: any) => d.source.y)
				.attr("x2", (d: any) => d.target.x)
				.attr("y2", (d: any) => d.target.y);

			node.attr("cx", (d: any) => d.x).attr("cy", (d: any) => d.y);
			labels.attr("x", (d: any) => d.x).attr("y", (d: any) => d.y);
		});

		return () => simulation.stop();
	}, [data]);

	return (
		<section style={{ background: "white", borderRadius: 12, padding: 14 }}>
			<h3>Knowledge Graph</h3>
			<p>Nodes: {data.nodes.length}</p>
			<p>Edges: {data.edges.length}</p>
			<svg ref={svgRef} style={{ width: "100%", height: 320, border: "1px solid #e5e7eb", borderRadius: 8 }} />
		</section>
	);
}

