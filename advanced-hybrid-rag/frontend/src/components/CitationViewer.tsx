import { useMemo } from "react";

import { useRAGStore } from "../store/ragStore";

export default function CitationViewer() {
	const { messages } = useRAGStore();
	const citations = useMemo(() => {
		const latestAssistant = [...messages].reverse().find((m) => m.role === "assistant");
		return latestAssistant?.citations ?? [];
	}, [messages]);

	return (
		<section style={{ background: "white", borderRadius: 12, padding: 14 }}>
			<h3>Citations</h3>
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

