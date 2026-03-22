import { useMutation } from "@tanstack/react-query";

export function useUploadMutation() {
	return useMutation({
		mutationFn: async (file: File) => {
			const formData = new FormData();
			formData.append("file", file);
			const res = await fetch("/api/ingest", { method: "POST", body: formData });
			if (!res.ok) throw new Error("Upload failed");
			return res.json();
		},
	});
}
