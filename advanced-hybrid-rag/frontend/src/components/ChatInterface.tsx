import { FormEvent, useState } from "react";

import { useRAGStore } from "../store/ragStore";

export default function ChatInterface() {
	const { messages, sendQuery, isStreaming, rateMessage } = useRAGStore();
	const [query, setQuery] = useState("");

	const onSubmit = async (e: FormEvent) => {
		e.preventDefault();
		const q = query.trim();
		if (!q) return;
		setQuery("");
		await sendQuery(q);
	};

	return (
		<section style={{ background: "white", borderRadius: 12, padding: 14 }}>
			<h3>Chat</h3>
			<div style={{ maxHeight: 280, overflow: "auto", marginBottom: 8 }}>
				{messages.map((m) => (
					<div key={m.id} style={{ marginBottom: 10 }}>
						<strong>{m.role === "user" ? "You" : "Assistant"}:</strong> {m.content}
						{m.warnings && m.warnings.length > 0 && <div style={{ color: "#9c3f00", marginTop: 4 }}>Warnings: {m.warnings.join(" | ")}</div>}
						{m.role === "assistant" && (
							<span style={{ marginLeft: 8 }}>
								<button onClick={() => void rateMessage(m.id, "up")}>+</button>
								<button onClick={() => void rateMessage(m.id, "down")} style={{ marginLeft: 4 }}>
									-
								</button>
							</span>
						)}
					</div>
				))}
			</div>
			<form onSubmit={onSubmit} style={{ display: "flex", gap: 8 }}>
				<input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Ask a research question" style={{ flex: 1 }} />
				<button type="submit" disabled={isStreaming}>
					{isStreaming ? "Generating..." : "Send"}
				</button>
			</form>
		</section>
	);
}

