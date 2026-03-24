import React, { useState } from 'react';
import type { QueryResult, Claim, Citation, Paper } from '../types';

interface Props {
  result: QueryResult;
  papers: Paper[];
}

export default function AnswerCard({ result, papers }: Props) {
  const [showClaims, setShowClaims]       = useState(false);
  const [showDiag, setShowDiag]           = useState(false);
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);

  const { answer, claims, retrieval_quality, retries, latency_ms, query_type, hops, diagnostic } = result;
  const verification = diagnostic?.verification;
  const qScore = Math.round(retrieval_quality * 100);
  const conf   = verification ? Math.round(verification.confidence * 100) : null;

  const paperMap = Object.fromEntries(papers.map(p => [p.paper_id, p.title]));

  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border)',
      borderRadius: '4px 12px 12px 12px', overflow: 'hidden',
    }}>
      {/* ── Answer body ── */}
      <div style={{ padding: '14px 16px' }}>
        {query_type === 'multi_hop' && hops.length > 1 && (
          <div style={{ marginBottom: 10 }}>
            <span style={{ fontSize: 10.5, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)' }}>
              Multi-hop · {hops.length} steps
            </span>
          </div>
        )}

        <div className="prose-answer">
          {answer ? formatAnswer(answer) : (
            <span style={{ color: 'var(--text-muted)' }}>No answer generated.</span>
          )}
        </div>
      </div>

      {/* ── Meta bar ── */}
      <div style={{
        display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 10,
        padding: '8px 16px', borderTop: '1px solid var(--border)',
        background: 'var(--bg-surface)',
      }}>
        {/* Retrieval quality */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flex: 1, minWidth: 140 }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>Retrieval</span>
          <div className="quality-bar-track" style={{ flex: 1 }}>
            <div className="quality-bar-fill" style={{
              width: `${qScore}%`,
              background: qScore >= 70 ? '#10b981' : qScore >= 45 ? '#f59e0b' : '#ef4444',
            }} />
          </div>
          <span style={{ fontSize: 11, fontWeight: 600, color: qualColor(qScore), minWidth: 28 }}>{qScore}%</span>
        </div>

        {/* Verification */}
        {verification && (
          <VerifBadge supported={verification.supported} confidence={conf!} />
        )}

        {/* Stats */}
        <div style={{ display: 'flex', gap: 8, fontSize: 11, color: 'var(--text-muted)' }}>
          <span>{latency_ms}ms</span>
          {retries > 0 && <span>{retries} retri{retries > 1 ? 'es' : 'y'}</span>}
          {diagnostic?.k_final && <span>{diagnostic.k_final} chunks</span>}
        </div>

        {/* Toggle buttons */}
        {claims.length > 0 && (
          <button onClick={() => setShowClaims(v => !v)} style={metaBtn(showClaims)}>
            {showClaims ? '▲' : '▼'} {claims.length} claim{claims.length > 1 ? 's' : ''}
          </button>
        )}
        <button onClick={() => setShowDiag(v => !v)} style={metaBtn(showDiag)}>
          {showDiag ? '▲' : '▼'} Debug
        </button>
      </div>

      {/* ── Claims ── */}
      {showClaims && claims.length > 0 && (
        <div style={{ borderTop: '1px solid var(--border)' }}>
          {claims.map((claim, i) => (
            <ClaimRow
              key={i}
              claim={claim}
              index={i + 1}
              paperMap={paperMap}
              onCitationClick={setActiveCitation}
            />
          ))}
        </div>
      )}

      {/* ── Diagnostic ── */}
      {showDiag && (
        <DiagPanel result={result} />
      )}

      {/* ── Citation modal ── */}
      {activeCitation && (
        <CitationModal
          citation={activeCitation}
          paperMap={paperMap}
          onClose={() => setActiveCitation(null)}
        />
      )}
    </div>
  );
}

/* ── Claim row ── */
function ClaimRow({ claim, index, paperMap, onCitationClick }: {
  claim: Claim; index: number; paperMap: Record<string, string>;
  onCitationClick: (c: Citation) => void;
}) {
  return (
    <div style={{
      padding: '10px 16px', borderBottom: '1px solid var(--border)',
      display: 'flex', gap: 10, alignItems: 'flex-start',
    }}>
      <span style={{
        fontSize: 10, fontWeight: 700, color: 'var(--accent-hover)',
        background: 'var(--accent-dim)', borderRadius: 4, padding: '2px 5px',
        flexShrink: 0, marginTop: 2,
      }}>{index}</span>

      <div style={{ flex: 1 }}>
        <p style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.6, marginBottom: claim.citations.length ? 6 : 0 }}>
          {claim.claim}
        </p>
        {claim.citations.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {claim.citations.map((cit, j) => (
              <button
                key={j}
                onClick={() => onCitationClick(cit)}
                style={{
                  background: 'rgba(99,102,241,.1)', border: '1px solid rgba(99,102,241,.3)',
                  borderRadius: 4, padding: '2px 8px', cursor: 'pointer',
                  fontSize: 11, color: '#a5b4fc', display: 'flex', alignItems: 'center', gap: 4,
                  transition: 'all .12s',
                }}
                onMouseEnter={e => { (e.currentTarget).style.background = 'rgba(99,102,241,.2)'; }}
                onMouseLeave={e => { (e.currentTarget).style.background = 'rgba(99,102,241,.1)'; }}
                title={paperMap[cit.paper_id] || cit.paper_id}
              >
                📄 p.{cit.page_number} · {cit.section}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Verification badge ── */
function VerifBadge({ supported, confidence }: { supported: boolean; confidence: number }) {
  const color = supported ? '#10b981' : confidence > 50 ? '#f59e0b' : '#ef4444';
  const label = supported ? '✓ Verified' : confidence > 50 ? '~ Partial' : '✗ Unverified';
  return (
    <span style={{
      fontSize: 11, fontWeight: 600, color,
      background: `${color}18`, border: `1px solid ${color}40`,
      borderRadius: 5, padding: '2px 7px',
    }}>
      {label} {confidence}%
    </span>
  );
}

/* ── Diagnostic panel ── */
function DiagPanel({ result }: { result: QueryResult }) {
  const { diagnostic, query_type, hops } = result;
  if (!diagnostic) return null;

  return (
    <div style={{ padding: '12px 16px', borderTop: '1px solid var(--border)', background: 'var(--bg-surface)' }}>
      <p style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)', marginBottom: 8 }}>
        Diagnostic
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 8, marginBottom: 10 }}>
        <Stat label="Query type" value={query_type} />
        <Stat label="Chunks used"   value={String(diagnostic.k_final ?? '—')} />
        <Stat label="Citations aug" value={String(diagnostic.citation_augmented_count ?? 0)} />
        {diagnostic.llm_error && <Stat label="LLM error" value="See below" color="#ef4444" />}
      </div>

      {/* Stage scores */}
      {diagnostic.verification?.stage_scores && Object.keys(diagnostic.verification.stage_scores).length > 0 && (
        <>
          <p style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>Verification stages</p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {Object.entries(diagnostic.verification.stage_scores).map(([k, v]) => (
              <span key={k} style={{
                fontSize: 11, background: 'var(--bg-input)', borderRadius: 4,
                padding: '2px 7px', color: 'var(--text-secondary)',
              }}>
                {k}: <strong style={{ color: 'var(--text-primary)' }}>{Math.round(Number(v) * 100)}%</strong>
              </span>
            ))}
          </div>
        </>
      )}

      {/* Hops */}
      {query_type === 'multi_hop' && hops.length > 0 && (
        <div style={{ marginTop: 10 }}>
          <p style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>Reasoning hops</p>
          {hops.map((h, i) => (
            <div key={i} style={{ fontSize: 12, color: 'var(--text-secondary)', padding: '3px 0', display: 'flex', gap: 6 }}>
              <span style={{ color: '#818cf8', fontWeight: 600 }}>{i + 1}.</span> {h}
            </div>
          ))}
        </div>
      )}

      {/* LLM error */}
      {diagnostic.llm_error && (
        <div style={{ marginTop: 10, background: 'rgba(239,68,68,.08)', border: '1px solid rgba(239,68,68,.25)', borderRadius: 6, padding: '8px 10px' }}>
          <p style={{ fontSize: 11, color: '#f87171' }}>{diagnostic.llm_error}</p>
        </div>
      )}

      {/* Top chunks */}
      {diagnostic.retrieved_chunks?.length > 0 && (
        <div style={{ marginTop: 10 }}>
          <p style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>
            Top retrieved chunks ({diagnostic.retrieved_chunks.length})
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {diagnostic.retrieved_chunks.slice(0, 5).map((c, i) => (
              <div key={i} style={{
                display: 'flex', gap: 8, fontSize: 11, color: 'var(--text-secondary)',
                background: 'var(--bg-input)', borderRadius: 4, padding: '4px 8px', alignItems: 'center',
              }}>
                <span style={{ color: 'var(--text-muted)', minWidth: 14 }}>#{i + 1}</span>
                <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {c.section} · p.{c.page_number}
                </span>
                <span style={{ color: '#818cf8', fontWeight: 600, flexShrink: 0 }}>
                  {c.rerank_score.toFixed(3)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Citation modal ── */
function CitationModal({ citation, paperMap, onClose }: {
  citation: Citation; paperMap: Record<string, string>; onClose: () => void;
}) {
  const title = paperMap[citation.paper_id] || citation.paper_id;
  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,.6)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100,
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        className="animate-fade-up"
        style={{
          background: 'var(--bg-card)', border: '1px solid var(--border)',
          borderRadius: 12, padding: '20px 24px', maxWidth: 480, width: '90%',
          boxShadow: '0 24px 64px rgba(0,0,0,.6)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
          <span style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-primary)' }}>Citation</span>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', fontSize: 18, lineHeight: 1 }}>×</button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <Field label="Paper" value={title} />
          <Field label="Section" value={citation.section} />
          <Field label="Page" value={`${citation.page_number}`} />
          <Field label="Chunk ID" value={citation.chunk_id} mono />
        </div>
      </div>
    </div>
  );
}

/* ── tiny helpers ── */
function Stat({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div>
      <p style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 2, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{label}</p>
      <p style={{ fontSize: 13, fontWeight: 600, color: color || 'var(--text-primary)' }}>{value}</p>
    </div>
  );
}

function Field({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <span style={{ fontSize: 10.5, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{label}</span>
      <span style={{ fontSize: 13, color: 'var(--text-primary)', fontFamily: mono ? 'monospace' : 'inherit', wordBreak: 'break-all' }}>{value}</span>
    </div>
  );
}

function metaBtn(active: boolean): React.CSSProperties {
  return {
    background: active ? 'var(--accent-dim)' : 'none',
    border: `1px solid ${active ? 'rgba(99,102,241,.4)' : 'var(--border)'}`,
    color: active ? '#a5b4fc' : 'var(--text-muted)',
    borderRadius: 5, padding: '3px 8px', cursor: 'pointer', fontSize: 11,
  };
}

function qualColor(pct: number): string {
  return pct >= 70 ? '#10b981' : pct >= 45 ? '#f59e0b' : '#ef4444';
}

function formatAnswer(text: string): React.ReactNode {
  // Split into paragraphs and render
  const paragraphs = text.split(/\n\n+/).filter(Boolean);
  if (paragraphs.length <= 1) {
    return <p>{text}</p>;
  }
  return <>{paragraphs.map((p, i) => <p key={i}>{p}</p>)}</>;
}
