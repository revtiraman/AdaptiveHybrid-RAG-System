import { useRAGStore } from "../store/ragStore";

export default function ReasoningTrace() {
	const { messages, planningSteps } = useRAGStore();
	const last = [...messages].reverse().find((m) => m.role === "assistant");
	return (
		<section style={{ background: "white", borderRadius: 12, padding: 14 }}>
			<h3>Reasoning Trace</h3>
			{last?.reasoningTrace && last.reasoningTrace.length > 0 ? (
				<ul>
					{last.reasoningTrace.slice(0, 8).map((t, i) => (
						<li key={`${t}-${i}`}>{t}</li>
					))}
				</ul>
			) : planningSteps.length > 0 ? (
				<ul>
					{planningSteps.slice(0, 8).map((s, i) => (
						<li key={`${s.action}-${i}`}>{s.action}</li>
					))}
				</ul>
			) : (
				<p>Ask a question or run planning to view reasoning traces.</p>
			)}
		</section>
	);
}

