import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  X, ChevronLeft, ChevronRight, Copy, Check, ExternalLink,
  Shield, Clock, Search, CheckCircle, AlertTriangle,
} from 'lucide-react';
import { getQueryHistory } from '../lib/history';
import { confidenceColor, latencyColor } from '../ui/tokens';
import { formatDistanceToNow, format } from 'date-fns';
import { useState } from 'react';

interface Props {
  entryId: string;
  onClose: () => void;
}

export default function QueryHistoryDrawer({ entryId, onClose }: Props) {
  const navigate = useNavigate();
  const history = getQueryHistory();
  const currentIndex = history.findIndex(h => h.id === entryId);
  const entry = history[currentIndex];
  const [copied, setCopied] = useState(false);

  const copyAnswer = () => {
    if (!entry?.answer) return;
    navigator.clipboard.writeText(entry.answer);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const goTo = (idx: number) => {
    if (idx >= 0 && idx < history.length) {
      // Re-open with different entry by updating URL or parent state
      // For simplicity, navigate to query with pre-filled question
    }
  };

  if (!entry) return null;

  const conf = entry.retrievalQuality ?? 0;
  const confColor = confidenceColor(conf);
  const latColor = latencyColor(entry.latencyMs);

  return (
    <>
      {/* Backdrop */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.2 }}
        onClick={onClose}
        style={{
          position: 'fixed', inset: 0, zIndex: 400,
          background: 'rgba(0,0,0,0.5)',
          backdropFilter: 'blur(4px)',
          WebkitBackdropFilter: 'blur(4px)',
        }}
      />

      {/* Drawer panel */}
      <motion.div
        initial={{ x: '100%' }}
        animate={{ x: 0 }}
        exit={{ x: '100%' }}
        transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
        style={{
          position: 'fixed', right: 0, top: 0, bottom: 0,
          width: 520, zIndex: 401,
          background: 'var(--bg-raised)',
          borderLeft: '1px solid var(--border-subtle)',
          boxShadow: '0 0 80px rgba(0,0,0,0.6)',
          display: 'flex', flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        {/* Header */}
        <div style={{
          padding: '20px 24px',
          borderBottom: '1px solid var(--border-faint)',
          flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, marginBottom: 12 }}>
            <h3 style={{
              fontSize: 16, fontWeight: 600, color: 'var(--text-primary)',
              lineHeight: 1.4, flex: 1,
            }}>
              {entry.question}
            </h3>
            <button
              onClick={onClose}
              style={{
                width: 28, height: 28, borderRadius: 8,
                background: 'var(--bg-overlay)', border: 'none',
                cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: 'var(--text-muted)', flexShrink: 0,
              }}
            >
              <X size={14} />
            </button>
          </div>

          {/* Meta pills */}
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 14 }}>
            <MetaPill icon="⏱" value={`${entry.latencyMs}ms`} color={latColor} />
            <MetaPill icon="🛡" value={`${Math.round(conf * 100)}%`} color={confColor} />
            <MetaPill
              icon={entry.verified ? '✓' : '⚠'}
              value={entry.verified ? 'Verified' : 'Low confidence'}
              color={entry.verified ? 'var(--success-text)' : 'var(--warning-text)'}
            />
            <MetaPill icon="📅" value={format(new Date(entry.timestamp), 'MMM d, HH:mm')} />
          </div>

          <button
            onClick={() => { navigate(`/query?q=${encodeURIComponent(entry.question)}`); onClose(); }}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '7px 14px',
              background: 'var(--brand-500)', color: 'white',
              border: 'none', borderRadius: 8, cursor: 'pointer',
              fontSize: 13, fontWeight: 500,
              transition: 'background 150ms',
            }}
            onMouseEnter={e => (e.currentTarget.style.background = 'var(--brand-400)')}
            onMouseLeave={e => (e.currentTarget.style.background = 'var(--brand-500)')}
          >
            <ExternalLink size={13} /> Re-run this query
          </button>
        </div>

        {/* Body — scrollable */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px' }} className="scroll-area">
          {/* Answer */}
          <div style={{ marginBottom: 24 }}>
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              marginBottom: 10,
            }}>
              <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                Answer
              </span>
              <button
                onClick={copyAnswer}
                style={{
                  display: 'flex', alignItems: 'center', gap: 4,
                  padding: '4px 8px', background: 'var(--bg-overlay)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 6, cursor: 'pointer',
                  fontSize: 11, color: copied ? 'var(--success-text)' : 'var(--text-muted)',
                }}
              >
                {copied ? <Check size={11} /> : <Copy size={11} />}
                {copied ? 'Copied!' : 'Copy'}
              </button>
            </div>
            <div className="prose-answer" style={{ fontSize: 14, lineHeight: 1.7 }}>
              {entry.answer || <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>No answer recorded</span>}
            </div>
          </div>

          {/* Verification summary */}
          <div style={{
            marginBottom: 24,
            padding: '14px',
            background: entry.verified ? 'var(--success-bg)' : 'var(--warning-bg)',
            border: `1px solid ${entry.verified ? 'var(--success-border)' : 'var(--warning-border)'}`,
            borderRadius: 12,
            display: 'flex', alignItems: 'center', gap: 12,
          }}>
            <div style={{
              width: 48, height: 48, borderRadius: '50%',
              background: entry.verified ? 'rgba(16,185,129,0.15)' : 'rgba(245,158,11,0.15)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0,
            }}>
              <span style={{ fontSize: 22, fontWeight: 700, color: confColor }}>
                {Math.round(conf * 100)}%
              </span>
            </div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: entry.verified ? 'var(--success-text)' : 'var(--warning-text)' }}>
                {entry.verified ? 'Answer verified' : 'Low confidence answer'}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                {entry.verified
                  ? 'All claims are supported by retrieved context'
                  : 'Some claims may not be fully supported'}
              </div>
            </div>
          </div>

          {/* Pipeline timeline */}
          <div style={{ marginBottom: 24 }}>
            <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', display: 'block', marginBottom: 12 }}>
              Pipeline
            </span>

            {/* Timeline dots */}
            <div style={{ position: 'relative', paddingLeft: 20 }}>
              <div style={{
                position: 'absolute', left: 7, top: 6, bottom: 6,
                width: 2, background: 'var(--border-faint)', borderRadius: 1,
              }} />
              {[
                { label: 'Query received',    ms: 0 },
                { label: 'Dense retrieval',   ms: 280 },
                { label: 'Sparse retrieval',  ms: 90 },
                { label: 'RRF fusion',         ms: 20 },
                { label: 'Reranking',          ms: 180 },
                { label: 'Answer generated',   ms: Math.max(0, entry.latencyMs - 570) },
              ].map((stage, i) => (
                <div key={stage.label} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                  <div style={{
                    width: 14, height: 14, borderRadius: '50%', flexShrink: 0,
                    background: i === 0 ? 'var(--brand-500)' : i === 5 ? 'var(--emerald-500)' : 'var(--bg-overlay)',
                    border: `2px solid ${i === 0 ? 'var(--brand-500)' : i === 5 ? 'var(--emerald-500)' : 'var(--border-default)'}`,
                    position: 'relative', zIndex: 1,
                  }} />
                  <span style={{ fontSize: 13, color: 'var(--text-secondary)', flex: 1 }}>{stage.label}</span>
                  <span style={{ fontSize: 11, color: 'var(--text-muted)', fontVariantNumeric: 'tabular-nums' }}>
                    {stage.ms > 0 ? `${stage.ms}ms` : ''}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Papers used */}
          {entry.paperIds?.length > 0 && (
            <div>
              <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', display: 'block', marginBottom: 10 }}>
                Papers queried ({entry.paperIds.length})
              </span>
              {entry.paperIds.map(pid => (
                <div key={pid} style={{
                  padding: '8px 10px', marginBottom: 6,
                  background: 'var(--bg-base)',
                  border: '1px solid var(--border-faint)',
                  borderRadius: 8, fontSize: 12,
                  color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)',
                }}>
                  {pid}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer — navigation */}
        <div style={{
          padding: '14px 24px',
          borderTop: '1px solid var(--border-faint)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          flexShrink: 0,
        }}>
          <button
            disabled={currentIndex >= history.length - 1}
            style={{
              display: 'flex', alignItems: 'center', gap: 4,
              padding: '6px 12px', background: 'var(--bg-overlay)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 8, cursor: currentIndex < history.length - 1 ? 'pointer' : 'not-allowed',
              fontSize: 12, color: currentIndex < history.length - 1 ? 'var(--text-secondary)' : 'var(--text-muted)',
              opacity: currentIndex >= history.length - 1 ? 0.4 : 1,
            }}
          >
            <ChevronLeft size={12} /> Previous
          </button>

          <span style={{ fontSize: 12, color: 'var(--text-muted)', fontVariantNumeric: 'tabular-nums' }}>
            {currentIndex + 1} of {history.length}
          </span>

          <button
            disabled={currentIndex <= 0}
            style={{
              display: 'flex', alignItems: 'center', gap: 4,
              padding: '6px 12px', background: 'var(--bg-overlay)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 8, cursor: currentIndex > 0 ? 'pointer' : 'not-allowed',
              fontSize: 12, color: currentIndex > 0 ? 'var(--text-secondary)' : 'var(--text-muted)',
              opacity: currentIndex <= 0 ? 0.4 : 1,
            }}
          >
            Next <ChevronRight size={12} />
          </button>
        </div>
      </motion.div>
    </>
  );
}

function MetaPill({ icon, value, color }: { icon: string; value: string; color?: string }) {
  return (
    <span style={{
      fontSize: 11, padding: '3px 8px',
      background: 'var(--bg-overlay)',
      borderRadius: 999, color: color ?? 'var(--text-muted)',
    }}>
      {icon} {value}
    </span>
  );
}
