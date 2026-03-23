import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

export type Citation = {
  paper_id: string;
  chunk_id: string;
  page_number: number;
  section: string;
};

export type Claim = {
  claim: string;
  citations: Citation[];
};

export type EvidenceItem = {
  id: string;
  type: 'CLAIM' | 'CONTEXT' | 'TABLE' | 'FIGURE';
  text: string;
  section: string;
  pageNumber: number;
  chunkId: string;
};

export type VerificationResult = {
  supported: boolean;
  confidence: number;
  unsupported_claims: string[];
  issues?: Array<{ type: string; detail: string }>;
  stage_scores?: Record<string, number>;
};

export type ReasoningStep = {
  step: string;
  latencyMs?: number;
};

export type SubQuestion = {
  text: string;
  status: 'pending' | 'running' | 'done';
};

export type Paper = {
  id: string;
  title: string;
  authors: string[];
  year: number;
  venue: string;
  chunks: number;
  tables: number;
  claims: number;
  indexingProgress: number;
  status: 'ready' | 'indexing' | 'error' | 'queued';
  extractionQuality: number;
  columnsDetected: number;
  parser: 'docling' | 'marker' | 'pymupdf';
};

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  streamText?: string;
  stage?: string;
  status?: 'streaming' | 'complete' | 'error' | 'cancelled';
  citations?: Citation[];
  claims?: Claim[];
  evidence?: EvidenceItem[];
  verification?: VerificationResult;
  reasoningSteps?: ReasoningStep[];
  subQuestions?: SubQuestion[];
  confidence?: 'HIGH' | 'MEDIUM' | 'LOW';
  groundingScore?: number;
  latencyMs?: number;
  model?: string;
  corrective_iterations?: number;
  cached?: boolean;
  rating?: 1 | -1;
  timestamp: Date;
  error?: string;
}

export interface Session {
  id: string;
  name: string;
  messages: Message[];
  paperScope: string[];
  createdAt: Date;
  updatedAt: Date;
}

export interface RAGSettings {
  kVector: number;
  kBM25: number;
  kFinal: number;
  qualityThreshold: number;
  maxRetries: number;
  rerankThreshold: number;
  useHyDE: boolean;
  useGraph: boolean;
  useClaims: boolean;
  useCitationChain: boolean;
  enableAdaptive: boolean;
  enableVerification: boolean;
  enableCRAG: boolean;
  primaryModel: string;
  fallbackModel: string;
  citationStyle: 'inline' | 'apa' | 'ieee' | 'mla';
  streamingEnabled: boolean;
  autoScrollEnabled: boolean;
  showReasoningTrace: boolean;
  compactMode: boolean;
}

type GraphData = { nodes: Array<Record<string, unknown>>; edges: Array<Record<string, unknown>> };
type EvalResults = Record<string, unknown>;

type RagStore = {
  sessions: Session[];
  activeSessionId: string | null;
  createSession: () => string;
  deleteSession: (id: string) => void;
  clearSessionMessages: (id: string) => void;
  renameSession: (id: string, name: string) => void;
  setActiveSession: (id: string) => void;
  addMessage: (sessionId: string, msg: Omit<Message, 'id'>) => string;
  updateMessage: (msgId: string, update: Partial<Message> | ((prev: Message) => Partial<Message>)) => void;
  deleteMessage: (msgId: string) => void;
  rateMessage: (msgId: string, rating: 1 | -1) => void;
  papers: Paper[];
  setPapers: (papers: Paper[]) => void;
  activePaperIds: string[];
  addPaper: (paper: Paper) => void;
  removePaper: (id: string) => void;
  setPaperScope: (ids: string[]) => void;
  updatePaperProgress: (id: string, progress: number, status: string) => void;
  settings: RAGSettings;
  updateSettings: (update: Partial<RAGSettings>) => void;
  resetSettings: () => void;
  graphData: GraphData | null;
  setGraphData: (data: GraphData) => void;
  evalResults: EvalResults | null;
  setEvalResults: (r: EvalResults) => void;
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
  activeView: string;
  setActiveView: (view: string) => void;
  commandPaletteOpen: boolean;
  toggleCommandPalette: () => void;
};

const defaultSettings: RAGSettings = {
  kVector: 30,
  kBM25: 20,
  kFinal: 5,
  qualityThreshold: 0.65,
  maxRetries: 3,
  rerankThreshold: 0.3,
  useHyDE: false,
  useGraph: true,
  useClaims: true,
  useCitationChain: true,
  enableAdaptive: true,
  enableVerification: true,
  enableCRAG: true,
  primaryModel: 'gpt-4o',
  fallbackModel: 'gpt-4o-mini',
  citationStyle: 'inline',
  streamingEnabled: true,
  autoScrollEnabled: true,
  showReasoningTrace: true,
  compactMode: false,
};

const uid = () => Math.random().toString(36).slice(2, 10);

const firstSession = (): Session => ({
  id: uid(),
  name: 'Default Session',
  messages: [],
  paperScope: [],
  createdAt: new Date(),
  updatedAt: new Date(),
});

export const useRagStore = create<RagStore>()(
  devtools(
    persist(
      immer((set, get) => ({
        sessions: [firstSession()],
        activeSessionId: null,
        createSession: () => {
          const next: Session = {
            id: uid(),
            name: `Session ${get().sessions.length + 1}`,
            messages: [],
            paperScope: get().activePaperIds,
            createdAt: new Date(),
            updatedAt: new Date(),
          };
          set((state) => {
            state.sessions.unshift(next);
            state.activeSessionId = next.id;
          });
          return next.id;
        },
        deleteSession: (id) =>
          set((state) => {
            state.sessions = state.sessions.filter((s) => s.id !== id);
            if (state.activeSessionId === id) state.activeSessionId = state.sessions[0]?.id ?? null;
          }),
        clearSessionMessages: (id) =>
          set((state) => {
            const session = state.sessions.find((s) => s.id === id);
            if (!session) return;
            session.messages = [];
            session.updatedAt = new Date();
          }),
        renameSession: (id, name) =>
          set((state) => {
            const session = state.sessions.find((s) => s.id === id);
            if (session) session.name = name;
          }),
        setActiveSession: (id) => set((state) => void (state.activeSessionId = id)),
        addMessage: (sessionId, msg) => {
          const id = uid();
          set((state) => {
            const session = state.sessions.find((s) => s.id === sessionId);
            if (!session) return;
            session.messages.push({ ...msg, id });
            session.updatedAt = new Date();
          });
          return id;
        },
        updateMessage: (msgId, update) =>
          set((state) => {
            for (const session of state.sessions) {
              const msg = session.messages.find((m) => m.id === msgId);
              if (msg) {
                const delta = typeof update === 'function' ? update(msg) : update;
                Object.assign(msg, delta);
                break;
              }
            }
          }),
        deleteMessage: (msgId) =>
          set((state) => {
            for (const session of state.sessions) {
              session.messages = session.messages.filter((m) => m.id !== msgId);
            }
          }),
        rateMessage: (msgId, rating) =>
          set((state) => {
            for (const session of state.sessions) {
              const msg = session.messages.find((m) => m.id === msgId);
              if (msg) msg.rating = rating;
            }
          }),
        papers: [],
        setPapers: (papers) =>
          set((state) => {
            state.papers = papers;
            const valid = new Set(papers.map((paper) => paper.id));
            state.activePaperIds = state.activePaperIds.filter((id) => valid.has(id));
          }),
        activePaperIds: [],
        addPaper: (paper) => set((state) => void state.papers.unshift(paper)),
        removePaper: (id) =>
          set((state) => {
            state.papers = state.papers.filter((p) => p.id !== id);
            state.activePaperIds = state.activePaperIds.filter((pId) => pId !== id);
          }),
        setPaperScope: (ids) => set((state) => void (state.activePaperIds = ids)),
        updatePaperProgress: (id, progress, status) =>
          set((state) => {
            const paper = state.papers.find((p) => p.id === id);
            if (!paper) return;
            paper.indexingProgress = progress;
            paper.status = status as Paper['status'];
          }),
        settings: defaultSettings,
        updateSettings: (update) => set((state) => void Object.assign(state.settings, update)),
        resetSettings: () => set((state) => void (state.settings = { ...defaultSettings })),
        graphData: null,
        setGraphData: (data) => set((state) => void (state.graphData = data)),
        evalResults: null,
        setEvalResults: (r) => set((state) => void (state.evalResults = r)),
        sidebarCollapsed: false,
        toggleSidebar: () => set((state) => void (state.sidebarCollapsed = !state.sidebarCollapsed)),
        activeView: 'chat',
        setActiveView: (view) => set((state) => void (state.activeView = view)),
        commandPaletteOpen: false,
        toggleCommandPalette: () => set((state) => void (state.commandPaletteOpen = !state.commandPaletteOpen)),
      })),
      {
        name: 'rag-store',
        partialize: (state) => ({
          sessions: state.sessions,
          settings: state.settings,
          papers: state.papers,
          activePaperIds: state.activePaperIds,
        }),
      },
    ),
  ),
);

export const useActiveSession = () => {
  return useRagStore((state) => {
    const activeId = state.activeSessionId ?? state.sessions[0]?.id;
    return state.sessions.find((s) => s.id === activeId) ?? state.sessions[0] ?? null;
  });
};
