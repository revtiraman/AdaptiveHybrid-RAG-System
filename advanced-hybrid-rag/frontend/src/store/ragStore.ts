import { create } from "zustand";

import type {
	DocumentItem,
	EvalResults,
	FeedbackStats,
	GraphData,
	Message,
	PlannerStep,
	RAGSettings,
} from "../types";

interface RAGState {
	messages: Message[];
	documents: DocumentItem[];
	settings: RAGSettings;
	isStreaming: boolean;
	currentQuery: string;
	evaluationResults: EvalResults | null;
	graphData: GraphData | null;
	planningSteps: PlannerStep[];
	literatureReview: string | null;
	feedbackStats: FeedbackStats | null;
	arxivItems: Array<{ title: string; category: string; fetched_at: string }>;
	annotationsByDoc: Record<string, Array<{ chunk_id: string; label: string; note: string; user_id: string; public: boolean }>>;
	sendQuery: (query: string) => Promise<void>;
	startStreamQuery: (query: string) => void;
	appendStreamChunk: (chunk: string) => void;
	finalizeStreamQuery: (response: any) => void;
	failStreamQuery: (message: string) => void;
	uploadDocument: (file: File, redactPII?: boolean) => Promise<void>;
	ingestUrl: (url: string, redactPII?: boolean) => Promise<void>;
	deleteDocument: (docId: string) => Promise<void>;
	updateSettings: (partial: Partial<RAGSettings>) => void;
	rateMessage: (messageId: string, rating: "up" | "down") => Promise<void>;
	runPlanning: (query: string) => Promise<void>;
	generateLiteratureReview: (topic: string) => Promise<void>;
	refreshFeedbackStats: () => Promise<void>;
	pollArxiv: () => Promise<void>;
	configureArxiv: (categories: string[], keywords: string[]) => Promise<void>;
	createAnnotation: (documentId: string, chunkId: string, note: string, label?: string) => Promise<void>;
	loadAnnotations: (documentId: string) => Promise<void>;
}

const defaultSettings: RAGSettings = {
	use_hyde: false,
	use_graph: true,
	use_colbert: false,
	enable_planning: false,
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
	planningSteps: [],
	literatureReview: null,
	feedbackStats: null,
	arxivItems: [],
	annotationsByDoc: {},

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
			queryId: data.query_id,
			reasoningTrace: data.reasoning_trace,
			warnings: data.warnings,
		};
		set({
			messages: [...get().messages, assistantMessage],
			planningSteps: data.reasoning_trace
				? data.reasoning_trace.map((entry: string) => ({ thought: "", action: entry, observation: "" }))
				: get().planningSteps,
			isStreaming: false,
		});
	},

	startStreamQuery: (query: string) => {
		const userMessage: Message = { id: crypto.randomUUID(), role: "user", content: query };
		const assistantMessage: Message = { id: crypto.randomUUID(), role: "assistant", content: "" };
		set({
			messages: [...get().messages, userMessage, assistantMessage],
			isStreaming: true,
			currentQuery: query,
		});
	},

	appendStreamChunk: (chunk: string) => {
		const items = [...get().messages];
		const idx = [...items].reverse().findIndex((m) => m.role === "assistant");
		if (idx === -1) return;
		const realIdx = items.length - 1 - idx;
		items[realIdx] = { ...items[realIdx], content: `${items[realIdx].content}${chunk}` };
		set({ messages: items });
	},

	finalizeStreamQuery: (response: any) => {
		const items = [...get().messages];
		const idx = [...items].reverse().findIndex((m) => m.role === "assistant");
		if (idx === -1) {
			set({ isStreaming: false });
			return;
		}
		const realIdx = items.length - 1 - idx;
		items[realIdx] = {
			...items[realIdx],
			content: response?.answer ?? items[realIdx].content,
			citations: response?.citations,
			queryId: response?.query_id,
			reasoningTrace: response?.reasoning_trace,
			warnings: response?.warnings,
		};
		set({
			messages: items,
			planningSteps: response?.reasoning_trace
				? response.reasoning_trace.map((entry: string) => ({ thought: "", action: entry, observation: "" }))
				: get().planningSteps,
			isStreaming: false,
		});
	},

	failStreamQuery: (message: string) => {
		set({
			messages: [
				...get().messages,
				{ id: crypto.randomUUID(), role: "assistant", content: message, warnings: ["stream_error"] },
			],
			isStreaming: false,
		});
	},

	uploadDocument: async (file: File, redactPII = true) => {
		const formData = new FormData();
		formData.append("file", file);
		const ingestPath = `/api/ingest?redact_pii=${redactPII ? "true" : "false"}`;
		const res = await fetch(ingestPath, { method: "POST", body: formData });
		const data = await res.json();
		set({ documents: [{ doc_id: data.doc_id, title: file.name }, ...get().documents] });
	},

	ingestUrl: async (url: string, redactPII = true) => {
		const res = await fetch("/api/ingest/url", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ url, redact_pii: redactPII }),
		});
		const data = await res.json();
		set({
			documents: [
				{ doc_id: data.doc_id, title: data.doc_id, source: url },
				...get().documents,
			],
		});
	},

	deleteDocument: async (docId: string) => {
		await fetch(`/api/papers/${docId}`, { method: "DELETE" });
		set({ documents: get().documents.filter((d) => d.doc_id !== docId) });
	},

	updateSettings: (partial: Partial<RAGSettings>) => {
		set({ settings: { ...get().settings, ...partial } });
	},

	rateMessage: async (messageId: string, rating: "up" | "down") => {
		const target = get().messages.find((m) => m.id === messageId && m.role === "assistant");
		set({
			messages: get().messages.map((m) => (m.id === messageId ? { ...m, rating } : m)),
		});

		if (!target?.queryId) {
			return;
		}

		await fetch("/api/feedback/", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({
				query_id: target.queryId,
				answer: target.content,
				rating: rating === "up" ? 5 : 1,
				helpful: rating === "up",
				bad_citation_ids: [],
			}),
		});
		await get().refreshFeedbackStats();
	},

	runPlanning: async (query: string) => {
		const res = await fetch("/api/planning/react", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ query }),
		});
		const data = await res.json();
		set({ planningSteps: data.steps ?? [] });
	},

	generateLiteratureReview: async (topic: string) => {
		const papers = get().documents.slice(0, 5).map((d) => ({
			title: d.title || d.doc_id,
			summary: `Indexed source: ${d.doc_id}`,
			cluster: "general",
		}));
		const res = await fetch("/api/literature/review", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ topic, papers }),
		});
		const data = await res.json();
		set({ literatureReview: data.review ?? null });
	},

	refreshFeedbackStats: async () => {
		const res = await fetch("/api/feedback/stats");
		if (!res.ok) return;
		const data = await res.json();
		set({ feedbackStats: data });
	},

	pollArxiv: async () => {
		const res = await fetch("/api/monitor/arxiv/poll", { method: "POST" });
		if (!res.ok) return;
		const data = await res.json();
		set({ arxivItems: data.items ?? [] });
	},

	configureArxiv: async (categories: string[], keywords: string[]) => {
		await fetch("/api/monitor/arxiv/config", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ categories, keywords }),
		});
	},

	createAnnotation: async (documentId: string, chunkId: string, note: string, label = "general") => {
		await fetch("/api/annotations", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ document_id: documentId, chunk_id: chunkId, note, label }),
		});
		await get().loadAnnotations(documentId);
	},

	loadAnnotations: async (documentId: string) => {
		const res = await fetch(`/api/annotations/${documentId}`);
		if (!res.ok) return;
		const data = await res.json();
		set({
			annotationsByDoc: {
				...get().annotationsByDoc,
				[documentId]: data.annotations ?? [],
			},
		});
	},
}));
