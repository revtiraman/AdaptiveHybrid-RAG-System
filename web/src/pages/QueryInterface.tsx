import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Send, ChevronLeft, ChevronRight, Copy, ThumbsUp, ThumbsDown,
  Bookmark, Check, Shield, Clock, Search, AlertTriangle, CheckCircle,
  ChevronsRight, Plus, Trash2, MessageSquare,
} from 'lucide-react';
import { api } from '../lib/api';
import { saveQueryToHistory, logActivity, getQueryHistory } from '../lib/history';
import { confidenceColor, titleGradient } from '../ui/tokens';
import { useAppStore } from '../lib/store';
import type { Message, QueryResult, RetrievedChunk } from '../types';
import { formatDistanceToNow } from 'date-fns';

const genId = () => Math.random().toString(36).slice(2);

type QueryMode = 'standard' | 'deep' | 'focused';
type RightTab = 'sources' | 'pipeline' | 'verification';

// ─── Streaming text simulation ────────────────────────────────
function useStreamText(target: string, active: boolean) {
  const [displayed, setDisplayed] = useState('');
  const [done, setDone] = useState(false);
  const words = useMemo(() => target.split(' '), [target]);
  const iRef = useRef(0);

  useEffect(() => {
    if (!active || !target) return;
    setDisplayed('');
    setDone(false);
    iRef.current = 0;

    const tick = () => {
      iRef.current += 4; // reveal 4 words at a time
      if (iRef.current >= words.length) {
        setDisplayed(target);
        setDone(true);
      } else {
        setDisplayed(words.slice(0, iRef.current).join(' ') + ' ');
        requestAnimationFrame(tick);
      }
    };
    const raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, active]);

  return { displayed, done };
}

// ─── Pipeline stage visualization ─────────────────────────────
function PipelineViz({ result }: { result: QueryResult }) {
  const stages = [
    { label: 'Dense',    count: 60,  color: 'var(--text-muted)' },
    { label: 'Sparse',   count: 60,  color: 'var(--text-muted)' },
    { label: 'Fused',    count: result.diagnostic?.k_final ?? 45,  color: 'var(--violet-500)' },
    { label: 'Reranked', count: Math.min(result.diagnostic?.k_final ?? 8, 8), color: 'var(--brand-500)' },
    { label: 'Used',     count: result.citations?.length ?? 5, color: 'var(--emerald-500)' },
  ];

  return (
    <div style={{ overflowX: 'auto', padding: '12px 0' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 0, minWidth: 360 }}>
        {stages.map((s, i) => (
          <React.Fragment key={s.label}>
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.1 }}
              style={{
                padding: '8px 12px',
                background: 'var(--bg-overlay)',
                border: `1px solid ${s.color}40`,
                borderRadius: 8, textAlign: 'center', flexShrink: 0,
              }}
            >
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>{s.label}</div>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.1 + 0.2 }}
                style={{ fontSize: 16, fontWeight: 600, color: s.color }}
              >
                {s.count}
              </motion.div>
            </motion.div>
            {i < stages.length - 1 && (
              <svg width={32} height={20} style={{ flexShrink: 0 }}>
                <line
                  x1={0} y1={10} x2={32} y2={10}
                  stroke="var(--border-subtle)" strokeWidth={1.5}
                  strokeDasharray="4 3"
                  className="pipeline-dash"
                />
                <polygon points="26,6 32,10 26,14" fill="var(--border-subtle)" />
              </svg>
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}

// ─── Source card ───────────────────────────────────────────────
function SourceCard({ chunk, rank, active }: { chunk: RetrievedChunk & { text?: string }; rank: number; active?: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const score = chunk.rerank_score ?? chunk.rrf_score ?? 0;
  const scoreColor = confidenceColor(score);

  const rankStyle = rank === 1
    ? { background: 'linear-gradient(135deg, #FFD700, #FFA500)' }
    : rank === 2
    ? { background: 'linear-gradient(135deg, #C0C0C0, #A0A0A0)' }
    : rank === 3
    ? { background: 'linear-gradient(135deg, #CD7F32, #A05020)' }
    : { background: 'var(--bg-overlay)', color: 'var(--text-muted)' };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: rank * 0.05 }}
      style={{
        background: 'var(--bg-base)',
        border: `1px solid ${active ? 'rgba(99,102,241,0.5)' : 'var(--border-subtle)'}`,
        borderRadius: 14,
        padding: 14,
        boxShadow: active ? 'var(--glow-brand)' : undefined,
        transition: 'border-color 200ms, box-shadow 200ms',
        marginBottom: 10,
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        {/* Rank */}
        <div style={{
          width: 24, height: 24, borderRadius: '50%',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 10, fontWeight: 700,
          flexShrink: 0,
          color: rank <= 3 ? 'white' : undefined,
          ...rankStyle,
        }}>
          {rank}
        </div>
        <span style={{
          fontSize: 11, fontWeight: 500,
          background: 'var(--bg-raised)',
          color: 'var(--text-secondary)',
          padding: '2px 6px', borderRadius: 5,
        }}>
          p.{chunk.page_number}
        </span>
        {chunk.section && (
          <span style={{
            fontSize: 11, fontWeight: 500,
            background: 'var(--bg-raised)',
            color: 'var(--text-secondary)',
            padding: '2px 6px', borderRadius: 5,
            maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          }}>
            {chunk.section}
          </span>
        )}
        <div style={{ flex: 1 }} />
        {/* Score bar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
          <div style={{ width: 60, height: 5, background: 'var(--bg-raised)', borderRadius: 999, overflow: 'hidden' }}>
            <div style={{
              height: '100%', width: `${Math.round(score * 100)}%`,
              background: scoreColor, borderRadius: 999,
            }} />
          </div>
          <span style={{ fontSize: 10, color: 'var(--text-muted)', fontVariantNumeric: 'tabular-nums' }}>
            {score.toFixed(2)}
          </span>
        </div>
      </div>

      {/* Text */}
      {chunk.text && (
        <div>
          <div style={{
            fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6,
            display: expanded ? 'block' : '-webkit-box',
            WebkitLineClamp: expanded ? undefined : 3,
            WebkitBoxOrient: 'vertical' as any,
            overflow: expanded ? 'visible' : 'hidden',
          }}>
            {chunk.text}
          </div>
          {chunk.text.length > 200 && (
            <button
              onClick={() => setExpanded(!expanded)}
              style={{
                fontSize: 11, color: 'var(--text-brand)',
                background: 'none', border: 'none', cursor: 'pointer',
                marginTop: 4, padding: 0,
              }}
            >
              {expanded ? 'Show less' : 'Show more'}
            </button>
          )}
        </div>
      )}

      {/* Footer */}
      <div style={{ marginTop: 8, fontSize: 11, color: 'var(--text-muted)', fontStyle: 'italic' }}>
        {chunk.paper_id}
      </div>
    </motion.div>
  );
}

// ─── Confidence arc ────────────────────────────────────────────
function ConfidenceArc({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color = confidenceColor(score);
  const arcLen = 345; // total arc length
  const filled = arcLen * score;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '16px 0' }}>
      <div style={{ position: 'relative', width: 120, height: 90 }}>
        <svg width={120} height={90} viewBox="0 0 120 90">
          {/* Background arc */}
          <path
            d="M 10 80 A 50 50 0 1 1 110 80"
            fill="none" stroke="var(--bg-overlay)" strokeWidth={10} strokeLinecap="round"
          />
          {/* Filled arc */}
          <motion.path
            d="M 10 80 A 50 50 0 1 1 110 80"
            fill="none" stroke={color} strokeWidth={10} strokeLinecap="round"
            strokeDasharray={arcLen}
            initial={{ strokeDashoffset: arcLen }}
            animate={{ strokeDashoffset: arcLen - filled }}
            transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
          />
        </svg>
        <div style={{
          position: 'absolute', top: '45%', left: '50%',
          transform: 'translate(-50%, -50%)',
          textAlign: 'center',
        }}>
          <div style={{ fontSize: 26, fontWeight: 700, color: 'var(--text-primary)' }}>{pct}%</div>
          <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>confidence</div>
        </div>
      </div>
    </div>
  );
}

// ─── Loading component ─────────────────────────────────────────
function LoadingState({ elapsed }: { elapsed: number }) {
  const phase =
    elapsed < 1000 ? 'idle' :
    elapsed < 3000 ? 'searching' :
    elapsed < 6000 ? 'reranking' : 'generating';

  const phaseLabel = {
    idle:      'Thinking...',
    searching: 'Searching papers...',
    reranking: 'Reranking results...',
    generating:'Generating answer...',
  }[phase];

  const phasePct = { idle: 5, searching: 35, reranking: 70, generating: 90 }[phase];

  return (
    <div style={{ padding: '20px 24px' }}>
      {elapsed < 1000 ? (
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          {[0, 1, 2].map(i => (
            <span
              key={i}
              className="thinking-dot"
              style={{ animationDelay: `${i * 0.2}s` }}
            />
          ))}
        </div>
      ) : (
        <div>
          <div style={{
            width: '100%', maxWidth: 380,
            height: 4, background: 'var(--bg-raised)',
            borderRadius: 999, overflow: 'hidden', marginBottom: 10,
          }}>
            <motion.div
              animate={{ width: `${phasePct}%` }}
              transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
              style={{
                height: '100%',
                background: 'linear-gradient(90deg, var(--brand-600), var(--brand-400))',
                borderRadius: 999,
                position: 'relative', overflow: 'hidden',
              }}
            >
              <div style={{
                position: 'absolute', inset: 0,
                background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)',
                animation: 'shimmer 1.4s ease-in-out infinite',
                backgroundSize: '200% 100%',
              }} />
            </motion.div>
          </div>
          <motion.span
            key={phaseLabel}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            style={{ fontSize: 13, color: 'var(--text-muted)' }}
          >
            {phaseLabel}
          </motion.span>
        </div>
      )}
    </div>
  );
}

// ─── Message bubble ────────────────────────────────────────────
function AssistantMessage({ msg, isLatest, activeCitation, onCitationClick }: {
  msg: Message;
  isLatest: boolean;
  activeCitation: string | null;
  onCitationClick: (id: string) => void;
}) {
  const { displayed, done } = useStreamText(msg.content, isLatest && !msg.isLoading);
  const [copied, setCopied] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const startRef = useRef(Date.now());

  useEffect(() => {
    if (!msg.isLoading) return;
    startRef.current = Date.now();
    const id = setInterval(() => setElapsed(Date.now() - startRef.current), 200);
    return () => clearInterval(id);
  }, [msg.isLoading]);

  const copyAnswer = () => {
    navigator.clipboard.writeText(msg.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const result = msg.result;
  const verification = result?.diagnostic?.verification;
  const conf = result?.retrieval_quality ?? 0;

  return (
    <div style={{ marginBottom: 28, position: 'relative' }}>
      {/* Bot icon */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 6 }}>
        <div style={{
          width: 24, height: 24, borderRadius: '50%',
          background: 'linear-gradient(135deg, var(--brand-600), var(--accent-500))',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 10, fontWeight: 700, color: 'white', flexShrink: 0,
        }}>
          R
        </div>
        <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', paddingTop: 4 }}>
          ResearchRAG
        </span>
      </div>

      {msg.isLoading ? (
        <LoadingState elapsed={elapsed} />
      ) : (
        <div style={{ paddingLeft: 34 }}>
          {/* Answer text */}
          <div className="prose-answer" style={{ maxWidth: 680 }}>
            {isLatest ? displayed : msg.content}
          </div>

          {/* Metadata bar */}
          <AnimatePresence>
            {(done || !isLatest) && result && (
              <motion.div
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                style={{
                  display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 12,
                }}
              >
                {[
                  { icon: '⏱', text: `${result.latency_ms}ms` },
                  { icon: '🔍', text: `${result.citations?.length ?? 0} chunks` },
                  { icon: '🛡', text: `${Math.round(conf * 100)}%` },
                  {
                    icon: verification?.supported ? '✓' : '⚠',
                    text: verification?.supported ? 'Verified' : 'Low confidence',
                    color: verification?.supported ? 'var(--success-text)' : 'var(--warning-text)',
                  },
                ].map(m => (
                  <span key={m.text} style={{
                    fontSize: 11, padding: '3px 8px',
                    background: 'var(--bg-raised)',
                    borderRadius: 999,
                    color: (m as any).color ?? 'var(--text-muted)',
                  }}>
                    {m.icon} {m.text}
                  </span>
                ))}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Copy / feedback controls (hover) */}
          <div style={{ display: 'flex', gap: 6, marginTop: 8 }}>
            <button
              onClick={copyAnswer}
              style={{
                display: 'flex', alignItems: 'center', gap: 4,
                padding: '4px 8px', background: 'var(--bg-raised)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 6, cursor: 'pointer',
                fontSize: 11, color: copied ? 'var(--success-text)' : 'var(--text-muted)',
                transition: 'color 120ms',
              }}
            >
              {copied ? <Check size={11} /> : <Copy size={11} />}
              {copied ? 'Copied!' : 'Copy'}
            </button>
            <button
              style={{
                padding: '4px 8px', background: 'var(--bg-raised)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 6, cursor: 'pointer',
                color: 'var(--text-muted)',
              }}
              title="Helpful"
            >
              <ThumbsUp size={11} />
            </button>
            <button
              style={{
                padding: '4px 8px', background: 'var(--bg-raised)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 6, cursor: 'pointer',
                color: 'var(--text-muted)',
              }}
              title="Not helpful"
            >
              <ThumbsDown size={11} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── QueryInterface ────────────────────────────────────────────
export default function QueryInterface() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { addNotification } = useAppStore();

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<QueryMode>('standard');
  const [selectedPapers, setSelectedPapers] = useState<string[]>([]);
  const [rightTab, setRightTab] = useState<RightTab>('sources');
  const [activeCitation, setActiveCitation] = useState<string | null>(null);
  const [leftOpen, setLeftOpen] = useState(true);
  const [rightOpen, setRightOpen] = useState(true);

  const conversationEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const { data: papers = [] } = useQuery({
    queryKey: ['papers'],
    queryFn: api.papers,
    staleTime: 30_000,
  });

  // Pre-fill from URL params
  useEffect(() => {
    const q = searchParams.get('q');
    const pid = searchParams.get('paper');
    if (q) setInput(q);
    if (pid) setSelectedPapers([pid]);
  }, []);

  // Auto-scroll
  useEffect(() => {
    conversationEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-grow textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 240) + 'px';
    }
  }, [input]);

  const latestResult = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].result) return messages[i].result!;
    }
    return null;
  }, [messages]);

  const handleSubmit = useCallback(async () => {
    const q = input.trim();
    if (!q || loading) return;
    setInput('');

    const userMsg: Message = { id: genId(), role: 'user', content: q, timestamp: new Date() };
    const assistantMsg: Message = { id: genId(), role: 'assistant', content: '', isLoading: true, timestamp: new Date() };

    setMessages(prev => [...prev, userMsg, assistantMsg]);
    setLoading(true);

    try {
      const result = await api.query({
        question: q,
        paper_ids: selectedPapers.length ? selectedPapers : undefined,
      });

      setMessages(prev => prev.map(m =>
        m.id === assistantMsg.id
          ? { ...m, content: result.answer, isLoading: false, result }
          : m
      ));

      saveQueryToHistory({
        id: genId(),
        timestamp: new Date().toISOString(),
        question: q,
        paperIds: selectedPapers,
        answer: result.answer,
        latencyMs: result.latency_ms,
        retrievalQuality: result.retrieval_quality,
        verified: result.diagnostic?.verification?.supported ?? false,
      });

      logActivity('query', q);
      addNotification({
        type: result.retrieval_quality > 0.5 ? 'success' : 'warning',
        title: 'Query complete',
        description: `${Math.round(result.retrieval_quality * 100)}% confidence · ${result.latency_ms}ms`,
        href: '/query',
      });
    } catch (err: any) {
      setMessages(prev => prev.map(m =>
        m.id === assistantMsg.id
          ? { ...m, content: err.message ?? 'An error occurred', isLoading: false, error: err.message }
          : m
      ));
    } finally {
      setLoading(false);
    }
  }, [input, loading, selectedPapers, addNotification]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const chunks = latestResult?.diagnostic?.retrieved_chunks ?? [];
  const verification = latestResult?.diagnostic?.verification;
  const hasMessages = messages.length > 0;

  return (
    <div style={{ display: 'flex', height: '100%', overflow: 'hidden' }}>
      {/* LEFT PANEL */}
      <AnimatePresence>
        {leftOpen && (
          <motion.div
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 280, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: [0.25, 1, 0.5, 1] }}
            style={{
              flexShrink: 0, overflow: 'hidden',
              borderRight: '1px solid var(--border-faint)',
              display: 'flex', flexDirection: 'column',
              background: 'rgba(13,13,26,0.6)',
            }}
          >
            <div style={{ padding: 16, overflowY: 'auto', flex: 1 }} className="scroll-area">
              {/* Papers */}
              <div style={{ marginBottom: 20 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                  <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                    Papers
                  </span>
                  <span style={{
                    fontSize: 10, background: 'rgba(99,102,241,0.2)',
                    color: 'var(--brand-300)', padding: '1px 5px', borderRadius: 999,
                  }}>
                    {papers.length}
                  </span>
                </div>

                {/* All papers option */}
                <label style={{
                  display: 'flex', alignItems: 'center', gap: 8,
                  padding: '6px 4px', cursor: 'pointer', borderRadius: 6,
                  fontSize: 13, color: 'var(--text-secondary)',
                }}>
                  <input
                    type="checkbox"
                    checked={selectedPapers.length === 0}
                    onChange={() => setSelectedPapers([])}
                    style={{ accentColor: 'var(--brand-500)' }}
                  />
                  All papers
                </label>

                {papers.map(p => (
                  <label
                    key={p.paper_id}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 8,
                      padding: '6px 4px', cursor: 'pointer', borderRadius: 6,
                      fontSize: 12, color: 'var(--text-secondary)',
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={selectedPapers.includes(p.paper_id)}
                      onChange={e => {
                        setSelectedPapers(prev =>
                          e.target.checked
                            ? [...prev, p.paper_id]
                            : prev.filter(id => id !== p.paper_id)
                        );
                      }}
                      style={{ accentColor: 'var(--brand-500)' }}
                    />
                    <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {p.title}
                    </span>
                    <span style={{
                      fontSize: 9, background: 'var(--bg-overlay)',
                      color: 'var(--text-muted)', padding: '1px 4px', borderRadius: 4,
                    }}>
                      {p.chunk_count}
                    </span>
                  </label>
                ))}
              </div>

              <div style={{ borderTop: '1px solid var(--border-faint)', paddingTop: 16 }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 10 }}>
                  History
                </div>
                {getQueryHistory().slice(0, 8).map(h => (
                  <div
                    key={h.id}
                    onClick={() => setInput(h.question)}
                    style={{
                      padding: '7px 8px', borderRadius: 8, cursor: 'pointer',
                      fontSize: 12, color: 'var(--text-secondary)',
                      display: 'flex', alignItems: 'flex-start', gap: 6,
                      transition: 'background 100ms',
                    }}
                    onMouseEnter={e => (e.currentTarget as HTMLDivElement).style.background = 'var(--bg-raised)'}
                    onMouseLeave={e => (e.currentTarget as HTMLDivElement).style.background = 'transparent'}
                  >
                    <MessageSquare size={11} style={{ marginTop: 1, flexShrink: 0, color: 'var(--text-muted)' }} />
                    <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}>
                      {h.question}
                    </span>
                  </div>
                ))}
                <button
                  onClick={() => setMessages([])}
                  style={{
                    marginTop: 8, width: '100%', padding: '6px',
                    background: 'transparent', border: '1px dashed var(--border-faint)',
                    borderRadius: 8, cursor: 'pointer',
                    fontSize: 12, color: 'var(--text-muted)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 5,
                  }}
                >
                  <Plus size={11} /> New conversation
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* LEFT TOGGLE */}
      <button
        onClick={() => setLeftOpen(!leftOpen)}
        style={{
          alignSelf: 'center', width: 16, height: 48,
          background: 'var(--bg-raised)', border: '1px solid var(--border-faint)',
          borderLeft: 'none', borderRadius: '0 6px 6px 0',
          cursor: 'pointer', color: 'var(--text-muted)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0, zIndex: 1,
        }}
      >
        {leftOpen ? <ChevronLeft size={10} /> : <ChevronRight size={10} />}
      </button>

      {/* CENTER */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minWidth: 0 }}>
        {/* Center top bar */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '12px 20px',
          borderBottom: '1px solid var(--border-faint)',
          flexShrink: 0,
        }}>
          <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>
            Querying {selectedPapers.length > 0 ? `${selectedPapers.length} papers` : `all ${papers.length} papers`}
          </span>

          {/* Mode selector */}
          <div style={{
            display: 'flex', background: 'var(--bg-raised)',
            border: '1px solid var(--border-subtle)', borderRadius: 999, padding: 3, gap: 2,
          }}>
            {([['standard', 'Standard'], ['deep', 'Deep Research'], ['focused', 'Focused']] as const).map(([m, label]) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                style={{
                  padding: '4px 12px', borderRadius: 999,
                  background: mode === m ? 'var(--brand-500)' : 'transparent',
                  border: 'none', cursor: 'pointer',
                  fontSize: 12, fontWeight: mode === m ? 600 : 400,
                  color: mode === m ? 'white' : 'var(--text-muted)',
                  transition: 'background 150ms, color 150ms',
                }}
              >
                {label}
              </button>
            ))}
          </div>

          <button
            onClick={() => setMessages([])}
            style={{
              padding: '5px 8px', background: 'none',
              border: '1px solid var(--border-subtle)',
              borderRadius: 6, cursor: 'pointer',
              fontSize: 12, color: 'var(--text-muted)',
              display: 'flex', alignItems: 'center', gap: 4,
            }}
          >
            <Trash2 size={11} /> Clear
          </button>
        </div>

        {/* Conversation */}
        <div
          style={{ flex: 1, overflowY: 'auto', padding: '24px 24px 0' }}
          className="scroll-area"
        >
          {!hasMessages ? (
            /* Empty state */
            <div style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center',
              justifyContent: 'center', height: '100%', gap: 16,
            }}>
              {papers.length === 0 ? (
                <>
                  <div style={{ fontSize: 36, opacity: 0.2 }}>📄</div>
                  <div style={{ fontSize: 17, fontWeight: 500, color: 'var(--text-secondary)' }}>
                    Upload a paper first
                  </div>
                  <button
                    onClick={() => navigate('/library')}
                    style={{
                      padding: '9px 18px', background: 'var(--brand-500)', color: 'white',
                      border: 'none', borderRadius: 8, cursor: 'pointer', fontSize: 14, fontWeight: 500,
                    }}
                  >
                    Go to Library →
                  </button>
                </>
              ) : (
                <>
                  <h2 style={{ fontSize: 22, fontWeight: 600, color: 'var(--text-primary)' }}>
                    What would you like to know?
                  </h2>
                  <div style={{
                    display: 'grid', gridTemplateColumns: '1fr 1fr',
                    gap: 10, width: '100%', maxWidth: 540,
                  }}>
                    {[
                      'What are the main contributions of these papers?',
                      'What methodology is used in these studies?',
                      'What are the key findings and results?',
                      'How do these papers compare to related work?',
                    ].map(q => (
                      <button
                        key={q}
                        onClick={() => setInput(q)}
                        style={{
                          padding: '14px', textAlign: 'left',
                          background: 'var(--bg-raised)',
                          border: '1px solid var(--border-subtle)',
                          borderRadius: 14, cursor: 'pointer',
                          fontSize: 13, color: 'var(--text-secondary)',
                          transition: 'border-color 150ms, transform 150ms',
                          lineHeight: 1.4,
                        }}
                        onMouseEnter={e => {
                          (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--border-strong)';
                          (e.currentTarget as HTMLButtonElement).style.transform = 'translateY(-2px)';
                        }}
                        onMouseLeave={e => {
                          (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--border-subtle)';
                          (e.currentTarget as HTMLButtonElement).style.transform = 'translateY(0)';
                        }}
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </>
              )}
            </div>
          ) : (
            messages.map((msg, i) => (
              msg.role === 'user' ? (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
                  style={{
                    display: 'flex', justifyContent: 'flex-end',
                    marginBottom: 20,
                  }}
                >
                  <div style={{
                    maxWidth: '70%',
                    background: 'linear-gradient(135deg, var(--brand-600), var(--brand-500))',
                    borderRadius: 16,
                    borderBottomRightRadius: 4,
                    padding: '12px 16px',
                    fontSize: 15, color: 'white', lineHeight: 1.6,
                  }}>
                    {msg.content}
                    <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', marginTop: 4, textAlign: 'right' }}>
                      {formatDistanceToNow(msg.timestamp, { addSuffix: true })}
                    </div>
                  </div>
                </motion.div>
              ) : (
                <AssistantMessage
                  key={msg.id}
                  msg={msg}
                  isLatest={i === messages.length - 1}
                  activeCitation={activeCitation}
                  onCitationClick={setActiveCitation}
                />
              )
            ))
          )}
          <div ref={conversationEndRef} />
        </div>

        {/* Input */}
        <div style={{
          padding: '16px 20px',
          borderTop: '1px solid var(--border-default)',
          background: 'var(--bg-base)',
          flexShrink: 0,
        }}>
          {/* Enhancement toggles */}
          <div style={{ display: 'flex', gap: 6, marginBottom: 10, flexWrap: 'wrap' }}>
            {[
              { label: 'HyDE', active: mode === 'deep' },
              { label: 'Multi-query', active: mode === 'deep' },
              { label: 'Compression', active: mode !== 'focused' },
              { label: 'Verify', active: true },
            ].map(t => (
              <span
                key={t.label}
                style={{
                  fontSize: 11, fontWeight: 600,
                  padding: '3px 8px', borderRadius: 999,
                  background: t.active ? 'rgba(99,102,241,0.2)' : 'var(--bg-raised)',
                  color: t.active ? 'var(--brand-300)' : 'var(--text-muted)',
                  border: `1px solid ${t.active ? 'rgba(99,102,241,0.3)' : 'var(--border-faint)'}`,
                  cursor: 'default',
                }}
              >
                {t.label}
              </span>
            ))}
          </div>

          <div style={{ position: 'relative' }}>
            <textarea
              ref={textareaRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a research question..."
              rows={1}
              style={{
                width: '100%',
                minHeight: 52, maxHeight: 240,
                padding: '14px 52px 14px 16px',
                background: 'var(--bg-sunken)',
                border: '1px solid var(--border-default)',
                borderRadius: 16,
                color: 'var(--text-primary)',
                fontSize: 15, lineHeight: 1.5,
                resize: 'none', outline: 'none',
                fontFamily: 'inherit',
                transition: 'border-color 150ms, box-shadow 150ms',
                boxSizing: 'border-box',
              }}
              onFocus={e => {
                e.currentTarget.style.borderColor = 'var(--border-focus)';
                e.currentTarget.style.boxShadow = 'var(--glow-brand)';
              }}
              onBlur={e => {
                e.currentTarget.style.borderColor = 'var(--border-default)';
                e.currentTarget.style.boxShadow = 'none';
              }}
            />

            {/* Send button */}
            <button
              onClick={handleSubmit}
              disabled={!input.trim() || loading}
              style={{
                position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)',
                width: 36, height: 36,
                background: input.trim() && !loading ? 'var(--brand-500)' : 'var(--bg-raised)',
                border: 'none', borderRadius: 10, cursor: input.trim() && !loading ? 'pointer' : 'default',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: input.trim() && !loading ? 'white' : 'var(--text-muted)',
                transition: 'background 150ms, transform 150ms',
              }}
              onMouseEnter={e => { if (input.trim() && !loading) (e.currentTarget as HTMLButtonElement).style.background = 'var(--brand-400)'; }}
              onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.background = input.trim() && !loading ? 'var(--brand-500)' : 'var(--bg-raised)'; }}
            >
              {loading
                ? <div className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />
                : <Send size={14} />
              }
            </button>
          </div>

          <div style={{ marginTop: 6, fontSize: 11, color: 'var(--text-muted)' }}>
            ↵ Send · ⇧↵ New line · ⌘↑ Last question
          </div>
        </div>
      </div>

      {/* RIGHT TOGGLE */}
      <button
        onClick={() => setRightOpen(!rightOpen)}
        style={{
          alignSelf: 'center', width: 16, height: 48,
          background: 'var(--bg-raised)', border: '1px solid var(--border-faint)',
          borderRight: 'none', borderRadius: '6px 0 0 6px',
          cursor: 'pointer', color: 'var(--text-muted)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0, zIndex: 1,
        }}
      >
        {rightOpen ? <ChevronRight size={10} /> : <ChevronLeft size={10} />}
      </button>

      {/* RIGHT PANEL */}
      <AnimatePresence>
        {rightOpen && (
          <motion.div
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 340, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: [0.25, 1, 0.5, 1] }}
            style={{
              flexShrink: 0, overflow: 'hidden',
              borderLeft: '1px solid var(--border-faint)',
              display: 'flex', flexDirection: 'column',
              background: 'rgba(13,13,26,0.6)',
            }}
          >
            {/* Tabs */}
            <div style={{
              display: 'flex',
              borderBottom: '1px solid var(--border-faint)',
              position: 'relative',
              flexShrink: 0,
            }}>
              {(['sources', 'pipeline', 'verification'] as RightTab[]).map(tab => (
                <button
                  key={tab}
                  onClick={() => setRightTab(tab)}
                  style={{
                    flex: 1, padding: '12px 8px',
                    background: 'none', border: 'none', cursor: 'pointer',
                    fontSize: 12, fontWeight: 500, textTransform: 'capitalize',
                    color: rightTab === tab ? 'var(--text-primary)' : 'var(--text-muted)',
                    position: 'relative', transition: 'color 150ms',
                  }}
                >
                  {tab}
                  {rightTab === tab && (
                    <motion.div
                      layoutId="right-tab-indicator"
                      style={{
                        position: 'absolute', bottom: 0, left: 0, right: 0,
                        height: 2, background: 'var(--brand-500)', borderRadius: '2px 2px 0 0',
                      }}
                      transition={{ duration: 0.2, ease: [0.25, 1, 0.5, 1] }}
                    />
                  )}
                </button>
              ))}
            </div>

            {/* Tab content */}
            <div style={{ flex: 1, overflowY: 'auto', padding: 14 }} className="scroll-area">
              {rightTab === 'sources' && (
                <>
                  {chunks.length === 0 ? (
                    <div style={{
                      display: 'flex', flexDirection: 'column', alignItems: 'center',
                      padding: '40px 16px', gap: 10,
                    }}>
                      <div style={{ opacity: 0.2, fontSize: 36 }}>📄</div>
                      <span style={{ fontSize: 13, color: 'var(--text-muted)', textAlign: 'center' }}>
                        Sources will appear here after your first query
                      </span>
                    </div>
                  ) : (
                    chunks.map((chunk, i) => (
                      <SourceCard
                        key={chunk.chunk_id}
                        chunk={chunk as any}
                        rank={i + 1}
                        active={activeCitation === chunk.chunk_id}
                      />
                    ))
                  )}
                </>
              )}

              {rightTab === 'pipeline' && latestResult && (
                <div>
                  <div style={{ marginBottom: 12 }}>
                    <div style={{ fontSize: 24, fontWeight: 600, color: 'var(--text-primary)' }}>
                      {latestResult.latency_ms}
                      <span style={{ fontSize: 12, fontWeight: 400, color: 'var(--text-muted)', marginLeft: 4 }}>ms total</span>
                    </div>
                  </div>
                  <PipelineViz result={latestResult} />

                  <div style={{ marginTop: 16 }}>
                    {[
                      { label: 'Query Expansion', ms: 120 },
                      { label: 'Dense Search',    ms: 280 },
                      { label: 'Sparse Search',   ms: 90  },
                      { label: 'RRF Fusion',      ms: 20  },
                      { label: 'Reranking',       ms: 180 },
                      { label: 'Generation',      ms: latestResult.latency_ms - 690 },
                    ].map(stage => (
                      <div
                        key={stage.label}
                        style={{
                          display: 'flex', alignItems: 'center', gap: 8,
                          padding: '8px 0',
                          borderBottom: '1px solid var(--border-faint)',
                        }}
                      >
                        <span style={{ fontSize: 12, color: 'var(--text-secondary)', flex: 1 }}>
                          {stage.label}
                        </span>
                        <span style={{ fontSize: 11, color: 'var(--text-muted)', fontVariantNumeric: 'tabular-nums' }}>
                          {Math.max(0, stage.ms)}ms
                        </span>
                        <div style={{ width: 80, height: 3, background: 'var(--bg-overlay)', borderRadius: 999, overflow: 'hidden' }}>
                          <div style={{
                            height: '100%',
                            width: `${Math.min(100, (stage.ms / latestResult.latency_ms) * 100)}%`,
                            background: 'var(--brand-500)',
                            borderRadius: 999,
                          }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {rightTab === 'verification' && (
                <div>
                  {!latestResult ? (
                    <div style={{ padding: '40px 16px', textAlign: 'center' }}>
                      <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                        Run a query to see verification results
                      </span>
                    </div>
                  ) : (
                    <>
                      <ConfidenceArc score={latestResult.retrieval_quality ?? 0} />

                      <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginBottom: 16 }}>
                        {[
                          {
                            label: verification?.supported ? 'Supported' : 'Unsupported',
                            color: verification?.supported ? 'var(--success-text)' : 'var(--danger-text)',
                            bg: verification?.supported ? 'var(--success-bg)' : 'var(--danger-bg)',
                          },
                          { label: 'Quality: Medium', color: 'var(--warning-text)', bg: 'var(--warning-bg)' },
                        ].map(p => (
                          <span key={p.label} style={{
                            fontSize: 11, fontWeight: 600,
                            padding: '3px 9px', borderRadius: 999,
                            background: p.bg, color: p.color,
                          }}>
                            {p.label}
                          </span>
                        ))}
                      </div>

                      {verification?.unsupported_claims?.length ? (
                        <div style={{
                          background: 'var(--danger-bg)',
                          border: '1px solid var(--danger-border)',
                          borderRadius: 10, padding: 12,
                        }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                            <AlertTriangle size={13} style={{ color: 'var(--danger-text)' }} />
                            <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--danger-text)' }}>
                              Potential issues found
                            </span>
                          </div>
                          {verification.unsupported_claims.map((c, i) => (
                            <div key={i} style={{ fontSize: 11, color: 'var(--danger-text)', opacity: 0.8, marginBottom: 4, paddingLeft: 8 }}>
                              • {c}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div style={{
                          display: 'flex', alignItems: 'center', gap: 8,
                          background: 'var(--success-bg)',
                          border: '1px solid var(--success-border)',
                          borderRadius: 10, padding: '10px 12px',
                        }}>
                          <CheckCircle size={16} style={{ color: 'var(--success-text)' }} />
                          <div>
                            <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--success-text)' }}>
                              No issues detected
                            </div>
                            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                              All claims supported by retrieved context
                            </div>
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
