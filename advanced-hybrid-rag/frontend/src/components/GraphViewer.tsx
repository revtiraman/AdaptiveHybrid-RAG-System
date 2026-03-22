import { useRAGStore } from "../store/ragStore";

export default function GraphViewer() {
	const { graphData } = useRAGStore();
	return (
		<section style={{ background: "white", borderRadius: 12, padding: 14 }}>
			<h3>Knowledge Graph</h3>
			<p>Nodes: {graphData?.nodes.length ?? 0}</p>
			<p>Edges: {graphData?.edges.length ?? 0}</p>
			<p>D3 visualization wiring is prepared for the next phase.</p>
		</section>
	);
}

