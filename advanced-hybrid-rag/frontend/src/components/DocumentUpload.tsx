import { ChangeEvent } from "react";
import { useState } from "react";

import { useRAGStore } from "../store/ragStore";

export default function DocumentUpload() {
	const { documents, uploadDocument, deleteDocument, loadAnnotations } = useRAGStore();
	const [redactPII, setRedactPII] = useState(true);

	const onChange = async (e: ChangeEvent<HTMLInputElement>) => {
		const file = e.target.files?.[0];
		if (!file) return;
		await uploadDocument(file, redactPII);
		const created = useRAGStore.getState().documents[0];
		if (created?.doc_id) {
			await loadAnnotations(created.doc_id);
		}
	};

	return (
		<section style={{ background: "white", borderRadius: 12, padding: 14 }}>
			<h3>Upload Documents</h3>
			<label style={{ display: "block", marginBottom: 8 }}>
				<input type="checkbox" checked={redactPII} onChange={(e) => setRedactPII(e.target.checked)} /> Redact PII during ingest
			</label>
			<input type="file" accept=".pdf,.docx" onChange={onChange} />
			<ul>
				{documents.map((d) => (
					<li key={d.doc_id}>
						{d.title || d.doc_id}
						<button onClick={() => deleteDocument(d.doc_id)} style={{ marginLeft: 8 }}>
							Delete
						</button>
					</li>
				))}
			</ul>
		</section>
	);
}

