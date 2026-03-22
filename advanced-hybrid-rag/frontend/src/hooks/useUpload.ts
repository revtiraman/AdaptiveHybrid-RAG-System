import { useCallback, useState } from "react";

export type UploadStage = "idle" | "uploading" | "parsing" | "chunking" | "embedding" | "storing" | "completed" | "failed";

interface UploadState {
	stage: UploadStage;
	progress: number;
	error: string | null;
}

const stageProgress: Record<UploadStage, number> = {
	idle: 0,
	uploading: 10,
	parsing: 30,
	chunking: 50,
	embedding: 70,
	storing: 90,
	completed: 100,
	failed: 0,
};

export function useUpload() {
	const [state, setState] = useState<UploadState>({ stage: "idle", progress: 0, error: null });

	const setStage = useCallback((stage: UploadStage, error: string | null = null) => {
		setState({ stage, progress: stageProgress[stage], error });
	}, []);

	const uploadFile = useCallback(async (file: File, redactPII = true) => {
		setStage("uploading");
		const formData = new FormData();
		formData.append("file", file);
		await new Promise((r) => setTimeout(r, 120));
		setStage("parsing");
		await new Promise((r) => setTimeout(r, 120));
		setStage("chunking");
		await new Promise((r) => setTimeout(r, 120));
		setStage("embedding");
		await new Promise((r) => setTimeout(r, 120));
		setStage("storing");

		const res = await fetch(`/api/ingest?redact_pii=${redactPII ? "true" : "false"}`, {
			method: "POST",
			body: formData,
		});
		if (!res.ok) {
			const detail = await res.text();
			setStage("failed", detail || "Upload failed");
			throw new Error(detail || "Upload failed");
		}
		const data = await res.json();
		setStage("completed");
		return data;
	}, [setStage]);

	const uploadUrl = useCallback(async (url: string, redactPII = true) => {
		setStage("parsing");
		await new Promise((r) => setTimeout(r, 120));
		setStage("chunking");
		await new Promise((r) => setTimeout(r, 120));
		setStage("embedding");
		await new Promise((r) => setTimeout(r, 120));
		setStage("storing");

		const res = await fetch("/api/ingest/url", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ url, redact_pii: redactPII }),
		});
		if (!res.ok) {
			const detail = await res.text();
			setStage("failed", detail || "URL ingest failed");
			throw new Error(detail || "URL ingest failed");
		}
		const data = await res.json();
		setStage("completed");
		return data;
	}, [setStage]);

	const reset = useCallback(() => setStage("idle"), [setStage]);

	return {
		...state,
		uploadFile,
		uploadUrl,
		reset,
	};
}
