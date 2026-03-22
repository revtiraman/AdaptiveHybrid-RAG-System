import { ChangeEvent } from "react";
import { useState } from "react";

import { useUpload } from "../hooks/useUpload";
import { useRAGStore } from "../store/ragStore";

export default function DocumentUpload() {
	const { documents, uploadDocument, ingestUrl, deleteDocument, loadAnnotations } = useRAGStore();
	const [redactPII, setRedactPII] = useState(true);
	const [tab, setTab] = useState<"file" | "url">("file");
	const [url, setUrl] = useState("");
	const { stage, progress, error, uploadFile, uploadUrl, reset } = useUpload();

	const onChange = async (e: ChangeEvent<HTMLInputElement>) => {
		const file = e.target.files?.[0];
		if (!file) return;
		const result = await uploadFile(file, redactPII);
		await uploadDocument(file, redactPII);
		const created = useRAGStore.getState().documents[0];
		if (created?.doc_id || result?.doc_id) {
			await loadAnnotations(created.doc_id);
		}
	};

	const onUrlSubmit = async () => {
		const value = url.trim();
		if (!value) return;
		const result = await uploadUrl(value, redactPII);
		await ingestUrl(value, redactPII);
		if (result?.doc_id) {
			await loadAnnotations(result.doc_id);
		}
		setUrl("");
	};

	return (
		<section style={{ background: "white", borderRadius: 12, padding: 14 }}>
			<h3>Upload Documents</h3>
			<div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
				<button onClick={() => setTab("file")} style={{ opacity: tab === "file" ? 1 : 0.65 }}>
					File
				</button>
				<button onClick={() => setTab("url")} style={{ opacity: tab === "url" ? 1 : 0.65 }}>
					URL
				</button>
			</div>
			<label style={{ display: "block", marginBottom: 8 }}>
				<input type="checkbox" checked={redactPII} onChange={(e) => setRedactPII(e.target.checked)} /> Redact PII during ingest
			</label>

			{tab === "file" ? (
				<input type="file" accept=".pdf,.docx" onChange={onChange} />
			) : (
				<div style={{ display: "flex", gap: 8 }}>
					<input
						value={url}
						onChange={(e) => setUrl(e.target.value)}
						placeholder="https://arxiv.org/abs/..."
						style={{ flex: 1 }}
					/>
					<button onClick={() => void onUrlSubmit()}>Ingest URL</button>
				</div>
			)}

			<div style={{ marginTop: 10, fontSize: 13 }}>
				<div>Stage: {stage}</div>
				<div style={{ height: 8, background: "#e5e7eb", borderRadius: 999, marginTop: 6 }}>
					<div style={{ width: `${progress}%`, height: 8, background: "#2563eb", borderRadius: 999 }} />
				</div>
				{error && <div style={{ color: "#b91c1c", marginTop: 6 }}>{error}</div>}
				{stage !== "idle" && <button onClick={reset} style={{ marginTop: 6 }}>Reset</button>}
			</div>

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

