import { useRAGStore } from "../store/ragStore";

export default function ReasoningTrace() {
	const { messages } = useRAGStore();
	const last = [...messages].reverse().find((m) => m.role === "assistant");
	return (
		<section style={{ background: "white", borderRadius: 12, padding: 14 }}>
			<h3>Reasoning Trace</h3>
			<p>{last ? "Trace available in backend response payload." : "Ask a question to view reasoning."}</p>
		</section>
	);
}

