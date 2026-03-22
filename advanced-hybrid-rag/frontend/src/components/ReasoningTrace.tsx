import { useMemo } from "react";

import { useRAGStore } from "../store/ragStore";

export default function ReasoningTrace() {
	const { messages, planningSteps } = useRAGStore();
	const last = [...messages].reverse().find((m) => m.role === "assistant");
	const entries = useMemo(() => {
		if (last?.reasoningTrace && last.reasoningTrace.length > 0) {
			return last.reasoningTrace.map((v, i) => ({
				title: `Step ${i + 1}`,
				action: v,
				detail: `Trace signal from backend: ${v}`,
			}));
		}
		return planningSteps.map((s, i) => ({
			title: `Plan ${i + 1}`,
			action: s.action,
			detail: `${s.thought || "Thought unavailable"}. ${s.observation || "Observation unavailable"}`,
		}));
	}, [last?.reasoningTrace, planningSteps]);

	return (
		<section style={{ background: "white", borderRadius: 12, padding: 14 }}>
			<h3>Reasoning Trace</h3>
			{entries.length > 0 ? (
				<div style={{ display: "grid", gap: 8 }}>
					{entries.slice(0, 10).map((entry, i) => (
						<details key={`${entry.action}-${i}`} open={i === 0} style={{ border: "1px solid #e5e7eb", borderRadius: 8, padding: 8 }}>
							<summary style={{ cursor: "pointer" }}>
								<strong>{entry.title}</strong>: {entry.action}
							</summary>
							<p style={{ margin: "8px 0 0 0", color: "#4b5563" }}>{entry.detail}</p>
						</details>
					))}
				</div>
			) : (
				<p>Ask a question or run planning to view reasoning traces.</p>
			)}
		</section>
	);
}

