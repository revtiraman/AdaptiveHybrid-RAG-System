export type Role = "user" | "assistant";

export interface Message {
	id: string;
	role: Role;
	content: string;
	citations?: Array<{ chunk_id: string; doc_id: string }>;
	rating?: "up" | "down";
}

export interface DocumentItem {
	doc_id: string;
	title?: string;
	source?: string;
}

export interface RAGSettings {
	use_hyde: boolean;
	use_graph: boolean;
	use_colbert: boolean;
	max_sources: number;
	model?: string;
}

export interface GraphData {
	nodes: Array<{ id: string }>;
	edges: Array<{ source: string; target: string }>;
}

export interface EvalResults {
	faithfulness: number;
	answer_relevancy: number;
	context_precision: number;
	context_recall: number;
}
