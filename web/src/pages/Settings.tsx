import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Download, Trash2, RefreshCw } from 'lucide-react';
import { api } from '../lib/api';
import { getQueryHistory, clearQueryHistory } from '../lib/history';

export default function Settings() {
  const [confirmClear, setConfirmClear] = useState(false);
  const [cleared, setCleared] = useState(false);
  const [historyCount, setHistoryCount] = useState(() => getQueryHistory().length);

  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useQuery({
    queryKey: ['stats'],
    queryFn: api.stats,
  });

  const handleClearHistory = () => {
    if (!confirmClear) {
      setConfirmClear(true);
      return;
    }
    clearQueryHistory();
    setHistoryCount(0);
    setCleared(true);
    setConfirmClear(false);
    setTimeout(() => setCleared(false), 3000);
  };

  const handleExportHistory = () => {
    const history = getQueryHistory();
    const blob = new Blob([JSON.stringify(history, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `rag-query-history-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ padding: '32px', maxWidth: 800, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <h1
          style={{
            fontSize: 26,
            fontWeight: 700,
            color: 'var(--text-primary)',
            letterSpacing: '-0.5px',
            marginBottom: 6,
          }}
        >
          Settings
        </h1>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
          System configuration and query history management
        </p>
      </div>

      {/* Section 1: System Info */}
      <Section title="System Information" subtitle="Current backend configuration (read-only)">
        {statsLoading ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {[1, 2, 3].map((i) => (
              <div key={i} className="skeleton" style={{ height: 56, borderRadius: 8 }} />
            ))}
          </div>
        ) : stats ? (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <InfoCard label="Embedding Provider" value={stats.embedding_provider} />
            <InfoCard label="Reranker Provider" value={stats.reranker_provider} />
            <InfoCard label="LLM Provider" value={stats.llm_provider} />
            <InfoCard label="Papers Indexed" value={String(stats.papers)} />
            <InfoCard label="Total Chunks" value={stats.chunks.toLocaleString()} />
          </div>
        ) : (
          <ErrorMsg message="Could not load system stats. Is the backend running?" />
        )}

        <div style={{ marginTop: 12 }}>
          <button
            onClick={() => refetchStats()}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              background: 'none',
              border: '1px solid var(--border-strong)',
              borderRadius: 7,
              padding: '6px 12px',
              cursor: 'pointer',
              fontSize: 12,
              color: 'var(--text-secondary)',
            }}
          >
            <RefreshCw size={12} />
            Refresh Stats
          </button>
        </div>
      </Section>

      {/* Section 2: Query Parameters */}
      <Section
        title="Query Parameters"
        subtitle="These parameters are configured server-side via environment variables."
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <ParamInfo
            label="Base K"
            description="Number of initial candidates retrieved before reranking (default: 10–20)."
          />
          <ParamInfo
            label="Max Retries"
            description="Maximum number of query retries on low-quality results (default: 1–3)."
          />
          <ParamInfo
            label="Retrieval Strategy"
            description="Hybrid RRF (dense + sparse) fusion with cross-encoder reranking."
          />
          <ParamInfo
            label="Verification"
            description="Self-verified with claim extraction and confidence scoring."
          />
        </div>
      </Section>

      {/* Section 3: Query History */}
      <Section
        title="Query History"
        subtitle="Manage your locally stored query history."
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            flexWrap: 'wrap',
            marginBottom: 14,
          }}
        >
          <div
            style={{
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border)',
              borderRadius: 8,
              padding: '10px 16px',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <span style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)' }}>
              {historyCount}
            </span>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>queries stored</span>
          </div>

          <button
            onClick={handleExportHistory}
            disabled={historyCount === 0}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              background: 'none',
              border: '1px solid var(--border-strong)',
              borderRadius: 7,
              padding: '8px 14px',
              cursor: historyCount > 0 ? 'pointer' : 'default',
              fontSize: 12,
              color: historyCount > 0 ? 'var(--text-secondary)' : 'var(--text-muted)',
              opacity: historyCount > 0 ? 1 : 0.5,
            }}
          >
            <Download size={13} />
            Export JSON
          </button>

          <button
            onClick={handleClearHistory}
            disabled={historyCount === 0}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              background: confirmClear ? 'rgba(239,68,68,0.1)' : 'none',
              border: `1px solid ${confirmClear ? 'rgba(239,68,68,0.5)' : 'var(--border-strong)'}`,
              borderRadius: 7,
              padding: '8px 14px',
              cursor: historyCount > 0 ? 'pointer' : 'default',
              fontSize: 12,
              color: confirmClear ? '#f87171' : historyCount > 0 ? 'var(--danger)' : 'var(--text-muted)',
              opacity: historyCount > 0 ? 1 : 0.5,
              transition: 'all 0.15s',
            }}
          >
            <Trash2 size={13} />
            {confirmClear ? 'Click again to confirm' : 'Clear history'}
          </button>
        </div>

        {cleared && (
          <div
            style={{
              fontSize: 12,
              color: 'var(--success)',
              background: 'rgba(16,185,129,0.08)',
              border: '1px solid rgba(16,185,129,0.25)',
              borderRadius: 6,
              padding: '6px 12px',
              display: 'inline-block',
            }}
          >
            History cleared successfully.
          </div>
        )}

        {confirmClear && !cleared && (
          <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
            <button
              onClick={() => setConfirmClear(false)}
              style={{
                background: 'none',
                border: '1px solid var(--border-strong)',
                borderRadius: 6,
                padding: '4px 10px',
                cursor: 'pointer',
                fontSize: 11,
                color: 'var(--text-secondary)',
              }}
            >
              Cancel
            </button>
          </div>
        )}
      </Section>

      {/* Section 4: About */}
      <Section title="About" subtitle="Version and build information.">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <InfoCard label="Application" value="ResearchRAG" />
          <InfoCard label="Frontend Version" value="v2.0" />
          <InfoCard label="API Base" value="http://localhost:8000" mono />
          <InfoCard
            label="Backend Status"
            value={stats ? 'Connected' : statsLoading ? 'Connecting…' : 'Offline'}
            color={stats ? 'var(--success)' : statsLoading ? 'var(--warning)' : 'var(--danger)'}
          />
        </div>
      </Section>
    </div>
  );
}

function Section({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <div
      style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderRadius: 12,
        padding: 24,
        marginBottom: 20,
      }}
    >
      <div style={{ marginBottom: 18 }}>
        <h2 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>
          {title}
        </h2>
        <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>{subtitle}</p>
      </div>
      {children}
    </div>
  );
}

function InfoCard({
  label,
  value,
  mono,
  color,
}: {
  label: string;
  value: string;
  mono?: boolean;
  color?: string;
}) {
  return (
    <div
      style={{
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border)',
        borderRadius: 8,
        padding: '10px 14px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 10,
      }}
    >
      <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{label}</span>
      <span
        style={{
          fontSize: 13,
          fontWeight: 600,
          color: color ?? 'var(--text-primary)',
          fontFamily: mono ? 'JetBrains Mono, monospace' : 'inherit',
          textAlign: 'right',
        }}
      >
        {value}
      </span>
    </div>
  );
}

function ParamInfo({ label, description }: { label: string; description: string }) {
  return (
    <div
      style={{
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border)',
        borderRadius: 8,
        padding: '12px 14px',
      }}
    >
      <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
        {label}
      </p>
      <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
        {description}
      </p>
    </div>
  );
}

function ErrorMsg({ message }: { message: string }) {
  return (
    <div
      style={{
        background: 'rgba(239,68,68,0.06)',
        border: '1px solid rgba(239,68,68,0.25)',
        borderRadius: 8,
        padding: '12px 14px',
        fontSize: 13,
        color: '#f87171',
      }}
    >
      {message}
    </div>
  );
}
