import { FormEvent, useEffect, useState } from "react";

import { useStream } from "../hooks/useStream";
import { useRAGStore } from "../store/ragStore";

export default function ChatInterface() {
	const { messages, settings, isStreaming, rateMessage, startStreamQuery, appendStreamChunk, finalizeStreamQuery, failStreamQuery } = useRAGStore();
	const [query, setQuery] = useState("");
	const [filterMode, setFilterMode] = useState<"all" | "issues" | "retried">("all");
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

	const assistantMessages = messages.filter((m) => m.role === "assistant");
	const issueCount = assistantMessages.filter((m) => (m.warnings?.length ?? 0) > 0).length;
	const retryCount = assistantMessages.filter((m) => (m.correctiveIterations ?? 0) > 0).length;
	const visibleMessages = messages.filter((m) => {
		if (m.role !== "assistant") return filterMode === "all";
		if (filterMode === "issues") return (m.warnings?.length ?? 0) > 0;
		if (filterMode === "retried") return (m.correctiveIterations ?? 0) > 0;
		return true;
	});

	const severityColor = (m: (typeof messages)[number]) => {
		if (m.role !== "assistant") return "transparent";
		if ((m.warnings?.length ?? 0) > 0) return "#f59e0b";
		if (typeof m.groundingScore === "number" && m.groundingScore < 0.5) return "#dc2626";
		return "#e5e7eb";
	};

	const copyDiagnostics = async (m: (typeof messages)[number]) => {
		const payload = {
			id: m.id,
			queryId: m.queryId,
			correctiveIterations: m.correctiveIterations,
			retrievalQuality: m.retrievalQuality,
			groundingScore: m.groundingScore,
			warnings: m.warnings ?? [],
			reasoningTrace: m.reasoningTrace ?? [],
			citations: m.citations ?? [],
		};
		await navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
	};

	return (
		<section style={{ background: "white", borderRadius: 12, padding: 14 }}>
			<h3>Chat</h3>
			<div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 8, alignItems: "center" }}>
				<button onClick={() => setFilterMode("all")} style={{ background: filterMode === "all" ? "#dbeafe" : "#f3f4f6" }}>
					All
				</button>
				<button onClick={() => setFilterMode("issues")} style={{ background: filterMode === "issues" ? "#fde68a" : "#f3f4f6" }}>
					With issues
				</button>
				<button onClick={() => setFilterMode("retried")} style={{ background: filterMode === "retried" ? "#dcfce7" : "#f3f4f6" }}>
					Retried
				</button>
				<span style={{ fontSize: 12, color: "#374151" }}>assistant: {assistantMessages.length}</span>
				<span style={{ fontSize: 12, color: "#92400e" }}>issues: {issueCount}</span>
				<span style={{ fontSize: 12, color: "#166534" }}>retried: {retryCount}</span>
			</div>
			<div style={{ maxHeight: 280, overflow: "auto", marginBottom: 8 }}>
				{visibleMessages.map((m) => (
					<div key={m.id} style={{ marginBottom: 10, padding: 8, border: `1px solid ${severityColor(m)}`, borderRadius: 8 }}>
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
						{m.role === "assistant" && m.confidence === "LOW" && (
							<div
								style={{
									marginTop: 6,
									background: "#fef3c7",
									border: "1px solid #f59e0b",
									color: "#7c2d12",
									borderRadius: 8,
									padding: "8px 10px",
									fontSize: 12,
								}}
							>
								Low confidence answer — retrieved context quality was poor.
							</div>
						)}
						{m.role === "assistant" && (
							<details style={{ marginTop: 6, fontSize: 12, color: "#374151" }}>
								<summary style={{ cursor: "pointer" }}>Details</summary>
								<div style={{ marginTop: 6, border: "1px solid #e5e7eb", borderRadius: 8, padding: 8, background: "#f9fafb" }}>
									{m.queryId && (
										<div>
											<strong>Query ID:</strong> {m.queryId}
										</div>
									)}
									{m.reasoningTrace && m.reasoningTrace.length > 0 && (
										<div style={{ marginTop: 4 }}>
											<strong>Reasoning Trace</strong>
											<ul style={{ margin: "4px 0 0 18px", padding: 0 }}>
												{m.reasoningTrace.slice(0, 12).map((step, idx) => (
													<li key={`${m.id}-trace-${idx}`}>{step}</li>
												))}
											</ul>
										</div>
									)}
									{m.citations && m.citations.length > 0 && (
										<div style={{ marginTop: 4 }}>
											<strong>Citations</strong>
											<ul style={{ margin: "4px 0 0 18px", padding: 0 }}>
												{m.citations.slice(0, 8).map((c, idx) => (
													<li key={`${m.id}-cite-${idx}`}>
														{c.doc_id} / {c.chunk_id}
													</li>
												))}
											</ul>
										</div>
									)}
									<div style={{ marginTop: 8 }}>
										<button onClick={() => void copyDiagnostics(m)}>Copy diagnostics JSON</button>
									</div>
								</div>
							</details>
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

