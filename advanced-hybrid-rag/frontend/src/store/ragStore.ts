import { create } from "zustand";

import type { DocumentItem, EvalResults, GraphData, Message, RAGSettings } from "../types";

interface RAGState {
	messages: Message[];
	documents: DocumentItem[];
	settings: RAGSettings;
	isStreaming: boolean;
	currentQuery: string;
	evaluationResults: EvalResults | null;
	graphData: GraphData | null;
	sendQuery: (query: string) => Promise<void>;
	uploadDocument: (file: File) => Promise<void>;
	deleteDocument: (docId: string) => Promise<void>;
	updateSettings: (partial: Partial<RAGSettings>) => void;
	rateMessage: (messageId: string, rating: "up" | "down") => void;
}

const defaultSettings: RAGSettings = {
	use_hyde: false,
	use_graph: true,
	use_colbert: false,
	max_sources: 5,
};

export const useRAGStore = create<RAGState>((set, get) => ({
	messages: [],
	documents: [],
	settings: defaultSettings,
	isStreaming: false,
	currentQuery: "",
	evaluationResults: null,
	graphData: null,

	sendQuery: async (query: string) => {
		const userMessage: Message = { id: crypto.randomUUID(), role: "user", content: query };
		set({ messages: [...get().messages, userMessage], isStreaming: true, currentQuery: query });

		const payload = {
			query,
			mode: "auto",
			filters: {},
			options: get().settings,
		};
		const res = await fetch("/api/query", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify(payload),
		});
		const data = await res.json();
		const assistantMessage: Message = {
			id: crypto.randomUUID(),
			role: "assistant",
			content: data.answer ?? "No answer returned.",
			citations: data.citations,
		};
		set({ messages: [...get().messages, assistantMessage], isStreaming: false });
	},

	uploadDocument: async (file: File) => {
		const formData = new FormData();
		formData.append("file", file);
		const res = await fetch("/api/ingest", { method: "POST", body: formData });
		const data = await res.json();
		set({ documents: [{ doc_id: data.doc_id, title: file.name }, ...get().documents] });
	},

	deleteDocument: async (docId: string) => {
		await fetch(`/api/papers/${docId}`, { method: "DELETE" });
		set({ documents: get().documents.filter((d) => d.doc_id !== docId) });
	},

	updateSettings: (partial: Partial<RAGSettings>) => {
		set({ settings: { ...get().settings, ...partial } });
	},

	rateMessage: (messageId: string, rating: "up" | "down") => {
		set({
			messages: get().messages.map((m) => (m.id === messageId ? { ...m, rating } : m)),
		});
	},
}));
