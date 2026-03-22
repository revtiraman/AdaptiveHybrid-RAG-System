// @ts-nocheck
import { useMemo, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { FlaskConical, Search, UploadCloud } from 'lucide-react';

type QueryResponse = {
  answer: string;
  claims: Array<{ claim: string; citations: Array<Record<string, unknown>> }>;
  citations: Array<Record<string, unknown>>;
  retrieval_quality: number;
  retries: number;
  latency_ms: number;
  diagnostic: Record<string, unknown>;
};

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000';

function normalizeText(text: string): string {
  return (text || '')
    .replace(/\s+/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .trim();
}

function toParagraphs(text: string): string[] {
  const clean = normalizeText(text);
  if (!clean) return [];
  const sentences = clean.split(/(?<=[.!?])\s+/).filter(Boolean);
  if (sentences.length <= 2) return [clean];
  const out: string[] = [];
  for (let i = 0; i < sentences.length; i += 2) {
    out.push(`${sentences[i]} ${sentences[i + 1] ?? ''}`.trim());
  }
  return out;
}

export default function App() {
  const [paperFile, setPaperFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [activePaperId, setActivePaperId] = useState('');
  const [question, setQuestion] = useState('What are the key contributions and evaluation outcomes?');
  const [section, setSection] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [status, setStatus] = useState('');

  const answerParagraphs = useMemo(() => toParagraphs(response?.answer ?? ''), [response?.answer]);
  const topClaims = useMemo(() => (response?.claims ?? []).slice(0, 6), [response?.claims]);

  const qualityLabel = useMemo(() => {
    if (!response) return 'N/A';
    if (response.retrieval_quality >= 0.75) return 'High';
    if (response.retrieval_quality >= 0.5) return 'Medium';
    return 'Low';
  }, [response]);

  async function readJsonSafe(res: Response): Promise<Record<string, any>> {
    try {
      return await res.json();
    } catch {
      return {};
    }
  }

  async function uploadPaper() {
    if (!paperFile) {
      setStatus('Choose a PDF first.');
      return;
    }

    setLoading(true);
    setStatus('Uploading and indexing...');
    const form = new FormData();
    form.append('file', paperFile);
    if (title.trim()) form.append('title', title.trim());

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 300000);

    try {
      const res = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: form,
        signal: controller.signal,
      });
      const payload = await readJsonSafe(res);
      if (res.ok && payload.paper?.paper_id) {
        setActivePaperId(String(payload.paper.paper_id));
      }
      setStatus(res.ok ? `Indexed: ${payload.paper?.paper_id ?? 'ok'}` : payload.detail ?? 'Upload failed');
    } catch (err: any) {
      const message = err?.name === 'AbortError' ? 'Upload timed out after 5 minutes.' : `Upload failed: ${err?.message ?? 'Network error'}`;
      setStatus(message);
    } finally {
      clearTimeout(timeoutId);
      setLoading(false);
    }
  }

  async function runQuery() {
    if (!activePaperId) {
      setStatus('Upload/index a paper first. Queries are scoped to the latest uploaded paper.');
      return;
    }

    setLoading(true);
    setStatus('Running adaptive hybrid retrieval...');

    const body: Record<string, unknown> = {
      question,
      paper_ids: [activePaperId],
    };
    if (section) body.filters = { section };

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 180000);

    try {
      const res = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      const payload = await readJsonSafe(res);
      if (!res.ok) {
        setStatus(payload.detail ?? 'Query failed');
        return;
      }

      setResponse(payload as QueryResponse);
      setStatus('Query complete.');
    } catch (err: any) {
      const message = err?.name === 'AbortError' ? 'Query timed out after 3 minutes.' : `Query failed: ${err?.message ?? 'Network error'}`;
      setStatus(message);
    } finally {
      clearTimeout(timeoutId);
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-mesh font-body text-ink">
      <div className="mx-auto max-w-6xl px-5 py-8 md:px-8">
        <motion.header
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-3xl border border-black/10 bg-white/75 p-6 shadow-xl backdrop-blur"
        >
          <h1 className="font-display text-3xl font-bold md:text-5xl">Adaptive Hybrid RAG</h1>
          <p className="mt-3 max-w-3xl text-sm md:text-base">
            Vector + BM25 retrieval, cross-encoder reranking, multi-hop reasoning, and self-verification for scientific paper QA.
          </p>
        </motion.header>

        <div className="mt-6 grid gap-6 md:grid-cols-2">
          <motion.section initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="rounded-3xl bg-white p-6 shadow-lg">
            <div className="mb-4 flex items-center gap-2 font-display text-xl font-semibold"><UploadCloud className="h-5 w-5" /> Upload</div>
            <input
              type="file"
              accept=".pdf"
              className="w-full rounded-xl border border-black/20 p-3"
              onChange={(event) => setPaperFile(event.target.files?.[0] ?? null)}
            />
            <input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Optional paper title"
              className="mt-3 w-full rounded-xl border border-black/20 p-3"
            />
            <button
              onClick={uploadPaper}
              disabled={loading}
              className="mt-4 rounded-2xl bg-accent px-5 py-3 font-semibold text-white transition hover:opacity-90 disabled:opacity-50"
            >
              Index Paper
            </button>
          </motion.section>

          <motion.section initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="rounded-3xl bg-white p-6 shadow-lg">
            <div className="mb-4 flex items-center gap-2 font-display text-xl font-semibold"><Search className="h-5 w-5" /> Query</div>
            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              rows={4}
              className="w-full rounded-xl border border-black/20 p-3"
            />
            <select value={section} onChange={(event) => setSection(event.target.value)} className="mt-3 w-full rounded-xl border border-black/20 p-3">
              <option value="">All sections</option>
              <option value="abstract">Abstract</option>
              <option value="introduction">Introduction</option>
              <option value="related_work">Related Work</option>
              <option value="method">Method</option>
              <option value="experiments">Experiments</option>
              <option value="results">Results</option>
              <option value="conclusion">Conclusion</option>
            </select>
            <button
              onClick={runQuery}
              disabled={loading}
              className="mt-4 rounded-2xl bg-signal px-5 py-3 font-semibold text-white transition hover:opacity-90 disabled:opacity-50"
            >
              Run Adaptive Query
            </button>
          </motion.section>
        </div>

        <div className="mt-4 rounded-2xl border border-black/10 bg-white/70 p-4 text-sm">{status}</div>
        {activePaperId && (
          <div className="mt-3 rounded-2xl border border-black/10 bg-white/70 p-4 text-xs">
            Active paper scope: {activePaperId}
          </div>
        )}

        <AnimatePresence>
          {response && (
            <motion.section
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 12 }}
              className="mt-6 rounded-3xl bg-white p-6 shadow-xl"
            >
              <div className="flex flex-wrap items-center gap-4 text-sm">
                <span className="rounded-full bg-black/5 px-3 py-1">Quality: {qualityLabel}</span>
                <span className="rounded-full bg-black/5 px-3 py-1">Retries: {response.retries}</span>
                <span className="rounded-full bg-black/5 px-3 py-1">Latency: {Math.round(response.latency_ms)} ms</span>
              </div>
              <div className="mt-4 flex items-center justify-between gap-3">
                <h2 className="font-display text-2xl font-semibold">Paper Overview</h2>
                <button
                  onClick={() => navigator.clipboard.writeText(normalizeText(response.answer))}
                  className="rounded-xl border border-black/15 px-3 py-1 text-sm hover:bg-black/5"
                >
                  Copy Answer
                </button>
              </div>

              <div className="mt-4 grid gap-4 lg:grid-cols-[1.6fr_1fr]">
                <div className="rounded-2xl border border-black/10 bg-white p-4">
                  <h3 className="font-display text-lg font-semibold">Summary</h3>
                  <div className="mt-3 space-y-3 text-[15px] leading-7 text-slate-800">
                    {answerParagraphs.length > 0 ? (
                      answerParagraphs.slice(0, 6).map((paragraph, idx) => (
                        <p key={idx} className="break-words">
                          {paragraph}
                        </p>
                      ))
                    ) : (
                      <p>No answer generated yet.</p>
                    )}
                  </div>
                </div>

                <div className="rounded-2xl border border-black/10 bg-black/[0.03] p-4">
                  <h3 className="font-display text-lg font-semibold">Key Points</h3>
                  {topClaims.length > 0 ? (
                    <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-slate-800">
                      {topClaims.map((claim, idx) => (
                        <li key={idx} className="break-words">{normalizeText(claim.claim)}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="mt-3 text-sm text-slate-700">No extracted claims were returned for this response.</p>
                  )}
                </div>
              </div>

              <h3 className="mt-6 flex items-center gap-2 font-display text-xl font-semibold"><FlaskConical className="h-5 w-5" /> Claim-level Citations</h3>
              <div className="mt-3 space-y-3">
                {topClaims.map((claim, idx) => (
                  <div key={idx} className="rounded-xl border border-black/10 p-4">
                    <p className="font-medium leading-7 break-words">{normalizeText(claim.claim)}</p>
                    <div className="mt-3 grid gap-2">
                      {(claim.citations ?? []).length > 0 ? (
                        claim.citations.map((citation: any, cIdx: number) => (
                          <div key={cIdx} className="rounded-lg bg-black/5 p-3 text-xs">
                            <div><span className="font-semibold">paper:</span> {String(citation.paper_id ?? 'unknown')}</div>
                            <div><span className="font-semibold">section:</span> {String(citation.section ?? 'n/a')}</div>
                            <div><span className="font-semibold">page:</span> {String(citation.page_number ?? 'n/a')}</div>
                            <div className="break-all"><span className="font-semibold">chunk:</span> {String(citation.chunk_id ?? 'n/a')}</div>
                          </div>
                        ))
                      ) : (
                        <div className="rounded-lg bg-black/5 p-3 text-xs">No citation metadata for this claim.</div>
                      )}
                    </div>
                  </div>
                ))}
                {topClaims.length === 0 && (
                  <div className="rounded-xl border border-black/10 p-4 text-sm text-slate-700">No claim-level citations returned.</div>
                )}
              </div>
            </motion.section>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
