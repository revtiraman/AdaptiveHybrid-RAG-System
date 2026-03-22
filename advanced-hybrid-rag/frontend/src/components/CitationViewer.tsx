import { useMemo } from "react";

import { useRAGStore } from "../store/ragStore";

export default function CitationViewer() {
	const { messages } = useRAGStore();
	const citations = useMemo(() => {
		const latestAssistant = [...messages].reverse().find((m) => m.role === "assistant");
		return latestAssistant?.citations ?? [];
	}, [messages]);

	const exportBibtex = () => {
		const lines = citations.map((c, idx) => {
			const key = `${c.doc_id || "source"}-${idx}`.replace(/[^a-zA-Z0-9-_]/g, "_");
			return `@misc{${key},\n  title={${c.doc_id}},\n  note={Chunk: ${c.chunk_id}},\n}`;
		});
		const content = lines.join("\n\n");
		const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
		const href = URL.createObjectURL(blob);
		const a = document.createElement("a");
		a.href = href;
		a.download = "citations.bib";
		document.body.appendChild(a);
		a.click();
		a.remove();
		URL.revokeObjectURL(href);
	};

	return (
		<section style={{ background: "white", borderRadius: 12, padding: 14 }}>
			<h3>Citations</h3>
			{citations.length > 0 && (
				<button onClick={exportBibtex} style={{ marginBottom: 8 }}>
					Export BibTeX
				</button>
			)}
			{citations.length === 0 ? (
				<p>No citations yet.</p>
			) : (
				<ul>
					{citations.map((c) => (
						<li key={`${c.chunk_id}-${c.doc_id}`}>
							{c.doc_id} / {c.chunk_id}
						</li>
					))}
				</ul>
			)}
		</section>
	);
}

