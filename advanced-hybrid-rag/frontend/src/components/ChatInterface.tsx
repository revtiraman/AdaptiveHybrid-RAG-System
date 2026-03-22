import { FormEvent, useEffect, useState } from "react";

import { useStream } from "../hooks/useStream";
import { useRAGStore } from "../store/ragStore";

export default function ChatInterface() {
	const { messages, settings, isStreaming, rateMessage, startStreamQuery, appendStreamChunk, finalizeStreamQuery, failStreamQuery } = useRAGStore();
	const [query, setQuery] = useState("");
	const { events, connect, close, connected } = useStream();

	const formatScore = (value?: number) => (typeof value === "number" ? value.toFixed(2) : null);

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
						{m.role === "assistant" && (
							<div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 6 }}>
								{typeof m.correctiveIterations === "number" && (
									<span style={{ padding: "2px 8px", borderRadius: 999, background: "#fef3c7", color: "#92400e", fontSize: 12 }}>
										retries {m.correctiveIterations}
									</span>
								)}
								{formatScore(m.retrievalQuality) && (
									<span style={{ padding: "2px 8px", borderRadius: 999, background: "#dbeafe", color: "#1e3a8a", fontSize: 12 }}>
										quality {formatScore(m.retrievalQuality)}
									</span>
								)}
								{formatScore(m.groundingScore) && (
									<span style={{ padding: "2px 8px", borderRadius: 999, background: "#dcfce7", color: "#166534", fontSize: 12 }}>
										grounding {formatScore(m.groundingScore)}
									</span>
								)}
							</div>
						)}
						{m.warnings && m.warnings.length > 0 && (
							<div style={{ color: "#9c3f00", marginTop: 6, fontSize: 12 }}>
								Warnings:
								<ul style={{ margin: "4px 0 0 18px", padding: 0 }}>
									{m.warnings.slice(0, 4).map((w, idx) => (
										<li key={`${m.id}-w-${idx}`}>{w}</li>
									))}
								</ul>
								{m.warnings.length > 4 && <div>+{m.warnings.length - 4} more warnings</div>}
							</div>
						)}
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

