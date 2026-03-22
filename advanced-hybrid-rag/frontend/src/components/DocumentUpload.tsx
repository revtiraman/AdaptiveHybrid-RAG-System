import { ChangeEvent } from "react";

import { useRAGStore } from "../store/ragStore";

export default function DocumentUpload() {
	const { documents, uploadDocument, deleteDocument } = useRAGStore();

	const onChange = async (e: ChangeEvent<HTMLInputElement>) => {
		const file = e.target.files?.[0];
		if (!file) return;
		await uploadDocument(file);
	};

	return (
		<section style={{ background: "white", borderRadius: 12, padding: 14 }}>
			<h3>Upload Documents</h3>
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

