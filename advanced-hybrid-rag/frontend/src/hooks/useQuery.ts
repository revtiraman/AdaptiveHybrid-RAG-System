import { useMutation } from "@tanstack/react-query";

export function useQueryMutation() {
	return useMutation({
		mutationFn: async (query: string) => {
			const res = await fetch("/api/query", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ query, mode: "auto", filters: {}, options: {} }),
			});
			if (!res.ok) throw new Error("Query failed");
			return res.json();
		},
	});
}
