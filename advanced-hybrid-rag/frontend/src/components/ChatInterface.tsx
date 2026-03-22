import { FormEvent, useEffect, useState } from "react";

import { useStream } from "../hooks/useStream";
import { useRAGStore } from "../store/ragStore";

export default function ChatInterface() {
	const { messages, settings, isStreaming, rateMessage, startStreamQuery, appendStreamChunk, finalizeStreamQuery, failStreamQuery } = useRAGStore();
	const [query, setQuery] = useState("");
	const { events, connect, close, connected } = useStream();

	useEffect(() => {
		if (events.length === 0) return;
		const evt = events[events.length - 1];
		if (evt.type === "chunk") {
			appendStreamChunk(evt.text || "");
		}
		if (evt.type === "complete") {
			finalizeStreamQuery(evt.response || {});
			close();
		}
		if (evt.type === "error") {
			failStreamQuery("Streaming failed. Please retry the query.");
			close();
		}
	}, [events, appendStreamChunk, close, failStreamQuery, finalizeStreamQuery]);

	const streamEndpointFor = (value: string) => {
		const params = new URLSearchParams({
			query: value,
			mode: "auto",
			max_sources: String(settings.max_sources || 5),
			use_hyde: String(Boolean(settings.use_hyde)),
			use_graph: String(Boolean(settings.use_graph)),
			use_colbert: String(Boolean(settings.use_colbert)),
			enable_planning: String(Boolean(settings.enable_planning)),
			enable_verification: String(Boolean(settings.enable_verification)),
			enable_adaptive: String(Boolean(settings.enable_adaptive)),
			citation_style: String(settings.citation_style || "inline"),
			model: String(settings.model || ""),
		});
		return `/api/query/stream?${params.toString()}`;
	};

	const onSubmit = async (e: FormEvent) => {
		e.preventDefault();
		const q = query.trim();
		if (!q) return;
		startStreamQuery(q);
		connect(streamEndpointFor(q));
		setQuery("");
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
								<button onClick={() => void navigator.clipboard.writeText(m.content)}>Copy</button>
								<button onClick={() => void rateMessage(m.id, "up")}>+</button>
								<button onClick={() => void rateMessage(m.id, "down")} style={{ marginLeft: 4 }}>
									-
								</button>
							</span>
						)}
					</div>
				))}
			</div>
			{isStreaming && <p style={{ fontSize: 12, color: connected ? "#1a6f2b" : "#8a6d00" }}>{connected ? "Streaming response..." : "Connecting stream..."}</p>}
			<form onSubmit={onSubmit} style={{ display: "flex", gap: 8 }}>
				<input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Ask a research question" style={{ flex: 1 }} />
				<button type="submit" disabled={isStreaming}>
					{isStreaming ? "Generating..." : "Send"}
				</button>
			</form>
		</section>
	);
}

