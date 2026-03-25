export interface Paper {
  paper_id: string;
  title: string;
  source_path: string;
  page_count: number;
  chunk_count: number;
  updated_at: string;
}

export interface Citation {
  chunk_id: string;
  paper_id: string;
  page_number: number;
  section: string;
  text?: string;
}

export interface Claim {
  claim: string;
  confidence: number;
  citations: Citation[];
}

export interface Verification {
  supported: boolean;
  confidence: number;
  unsupported_claims: string[];
  issues: Array<{ type: string; detail: string }>;
  stage_scores: Record<string, number>;
}

export interface RetrievedChunk {
  chunk_id: string;
  paper_id: string;
  page_number: number;
  section: string;
  rrf_score: number;
  rerank_score: number;
}

export interface Diagnostic {
  retrieved_chunks: RetrievedChunk[];
  verification: Verification;
  llm_error: string | null;
  k_final: number;
  citation_augmented_count: number;
}

export interface QueryResult {
  question: string;
  query_type: 'simple' | 'multi_hop';
  hops: string[];
  answer: string;
  claims: Claim[];
  citations: Citation[];
  retrieval_quality: number;
  retries: number;
  latency_ms: number;
  diagnostic: Diagnostic;
}

export interface SystemStats {
  papers: number;
  chunks: number;
  embedding_provider: string;
  reranker_provider: string;
  llm_provider: string;
}

export interface UploadResult {
  paper: {
    paper_id: string;
    title: string;
    page_count: number;
    chunk_count: number;
    claims_extracted: number;
  };
}

export type MessageRole = 'user' | 'assistant';

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  result?: QueryResult;
  error?: string;
  isLoading?: boolean;
  timestamp: Date;
}

export interface QueryHistoryEntry {
  id: string;
  timestamp: string;
  question: string;
  paperIds: string[];
  answer: string;
  latencyMs: number;
  retrievalQuality: number;
  verified: boolean;
}
