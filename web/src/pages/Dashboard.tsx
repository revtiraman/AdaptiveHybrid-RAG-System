import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  FileText, Layers, Zap, Target, Upload, ChevronRight,
  ArrowUp, ArrowDown, TrendingUp, AlertCircle,
} from 'lucide-react';
import {
  ResponsiveContainer, LineChart, Line, AreaChart, Area,
  Tooltip as ReTooltip, CartesianGrid, XAxis, YAxis,
} from 'recharts';
import { api } from '../lib/api';
import { getQueryHistory } from '../lib/history';
import { titleGradient, confidenceColor, latencyColor } from '../ui/tokens';
import { useAppStore } from '../lib/store';
import { formatDistanceToNow } from 'date-fns';
import UploadModal from '../components/UploadModal';

// ─── Count-up hook ────────────────────────────────────────────
function useCountUp(target: number, duration = 800) {
  const [value, setValue] = useState(0);
  useEffect(() => {
    if (target === 0) return;
    let start: number | null = null;
    const step = (ts: number) => {
      if (!start) start = ts;
      const progress = Math.min((ts - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.round(eased * target));
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [target, duration]);
  return value;
}

// ─── Sparkline (SVG path) ─────────────────────────────────────
function Sparkline({ data, color, height = 60 }: { data: number[]; color: string; height?: number }) {
  if (!data.length) return <div style={{ height }} />;
  const w = 200, h = height;
  const max = Math.max(...data, 1);
  const min = Math.min(...data);
  const range = max - min || 1;
  const pts = data.map((v, i) => [
    (i / (data.length - 1)) * w,
    h - ((v - min) / range) * (h - 8) - 4,
  ]);
  const d = pts.reduce((acc, [x, y], i) => {
    if (i === 0) return `M ${x} ${y}`;
    const [px, py] = pts[i - 1];
    const cx = (px + x) / 2;
    return `${acc} C ${cx} ${py} ${cx} ${y} ${x} ${y}`;
  }, '');
  const areaD = `${d} L ${w} ${h} L 0 ${h} Z`;
  return (
    <svg width="100%" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" style={{ display: 'block' }}>
      <defs>
        <linearGradient id={`sg-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={areaD} fill={`url(#sg-${color.replace('#', '')})`} />
      <path d={d} stroke={color} strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

// ─── KPI Card ─────────────────────────────────────────────────
interface KPICardProps {
  label: string;
  value: number;
  unit?: string;
  icon: React.ElementType;
  accent: string;
  sparkData?: number[];
  delta?: { value: number; label: string };
  onClick?: () => void;
  delay?: number;
}

function KPICard({ label, value, unit, icon: Icon, accent, sparkData = [], delta, onClick, delay = 0 }: KPICardProps) {
  const displayed = useCountUp(value);
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
      whileHover={{ y: -2, transition: { duration: 0.2 } }}
      onClick={onClick}
      style={{
        flex: 1, minWidth: 0,
        background: 'var(--bg-base)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 20,
        boxShadow: '0 4px 16px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.06)',
        overflow: 'hidden',
        cursor: onClick ? 'pointer' : 'default',
        position: 'relative',
      }}
    >
      {/* Accent radial glow top-right */}
      <div style={{
        position: 'absolute', top: 0, right: 0, width: 120, height: 120,
        background: `radial-gradient(circle at 100% 0%, ${accent}14 0%, transparent 70%)`,
        pointerEvents: 'none',
      }} />

      <div style={{ padding: '20px 20px 0' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            {label}
          </span>
          <Icon size={18} style={{ color: accent }} />
        </div>

        <div style={{ fontSize: 36, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1, fontVariantNumeric: 'tabular-nums' }}>
          {displayed.toLocaleString()}{unit && <span style={{ fontSize: 18, fontWeight: 500, marginLeft: 3, color: 'var(--text-secondary)' }}>{unit}</span>}
        </div>

        {delta && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 8 }}>
            {delta.value >= 0
              ? <ArrowUp size={12} style={{ color: 'var(--emerald-500)' }} />
              : <ArrowDown size={12} style={{ color: 'var(--rose-500)' }} />
            }
            <span style={{
              fontSize: 12,
              color: delta.value >= 0 ? 'var(--emerald-500)' : 'var(--rose-500)',
            }}>
              {Math.abs(delta.value)} {delta.label}
            </span>
          </div>
        )}
      </div>

      <div style={{ height: 60, marginTop: 12 }}>
        <Sparkline data={sparkData} color={accent} height={60} />
      </div>
    </motion.div>
  );
}

// ─── Recent query row ──────────────────────────────────────────
function QueryRow({ entry, onClick }: { entry: any; onClick: () => void }) {
  const conf = entry.retrievalQuality ?? 0;
  const bg = confidenceColor(conf);
  return (
    <div
      onClick={onClick}
      style={{
        display: 'flex', alignItems: 'center', gap: 12,
        padding: '10px 12px', borderRadius: 10,
        cursor: 'pointer', transition: 'background 120ms',
      }}
      onMouseEnter={e => (e.currentTarget as HTMLDivElement).style.background = 'var(--bg-raised)'}
      onMouseLeave={e => (e.currentTarget as HTMLDivElement).style.background = 'transparent'}
    >
      <div style={{
        width: 36, height: 36, borderRadius: 8, flexShrink: 0,
        background: bg, display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 10, fontWeight: 600, color: 'white',
      }}>
        {Math.round(conf * 100)}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          fontSize: 13, fontWeight: 500, color: 'var(--text-primary)',
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        }}>
          {entry.question}
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
          {entry.latencyMs}ms ·{' '}
          {formatDistanceToNow(new Date(entry.timestamp), { addSuffix: true })}
        </div>
      </div>
      <ChevronRight size={14} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
    </div>
  );
}

// ─── Paper card (scroll strip) ─────────────────────────────────
function PaperCard({ paper, onQuery }: { paper: any; onQuery: () => void }) {
  const [g1, g2] = titleGradient(paper.title);
  return (
    <motion.div
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      style={{
        width: 220, flexShrink: 0,
        background: 'var(--bg-base)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 20,
        boxShadow: '0 4px 16px rgba(0,0,0,0.5)',
        overflow: 'hidden',
        scrollSnapAlign: 'start',
      }}
    >
      {/* Gradient header */}
      <div style={{
        height: 80,
        background: `linear-gradient(135deg, ${g1}, ${g2})`,
        position: 'relative', padding: 12,
      }}>
        <div style={{
          position: 'absolute', inset: 0,
          background: 'linear-gradient(to bottom, transparent 40%, rgba(0,0,0,0.5) 100%)',
        }} />
        <div style={{
          position: 'relative', zIndex: 1,
          fontSize: 12, fontWeight: 600, color: 'white',
          display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
          overflow: 'hidden', lineHeight: 1.4,
        }}>
          {paper.title}
        </div>
      </div>

      {/* Stats */}
      <div style={{ padding: 12 }}>
        <div style={{ display: 'flex', gap: 6, marginBottom: 10 }}>
          {[
            `${paper.page_count ?? 0}p`,
            `${paper.chunk_count ?? 0} chunks`,
          ].map(stat => (
            <span key={stat} style={{
              fontSize: 10, fontWeight: 500,
              padding: '2px 6px',
              background: 'var(--bg-raised)',
              color: 'var(--text-secondary)',
              borderRadius: 6,
            }}>
              {stat}
            </span>
          ))}
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 10 }}>
          {new Date(paper.updated_at).toLocaleDateString()}
        </div>
        <button
          onClick={onQuery}
          style={{
            width: '100%', height: 28,
            background: 'transparent',
            border: '1px solid var(--border-default)',
            borderRadius: 8, cursor: 'pointer',
            fontSize: 12, color: 'var(--text-secondary)',
            transition: 'border-color 120ms, color 120ms',
          }}
          onMouseEnter={e => {
            (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--brand-500)';
            (e.currentTarget as HTMLButtonElement).style.color = 'var(--brand-400)';
          }}
          onMouseLeave={e => {
            (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--border-default)';
            (e.currentTarget as HTMLButtonElement).style.color = 'var(--text-secondary)';
          }}
        >
          Query →
        </button>
      </div>
    </motion.div>
  );
}

// ─── Dashboard ────────────────────────────────────────────────
export default function Dashboard() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { addNotification } = useAppStore();
  const [uploadOpen, setUploadOpen] = useState(false);

  const { data: papers = [] } = useQuery({
    queryKey: ['papers'],
    queryFn: api.papers,
    staleTime: 30_000,
  });

  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: api.stats,
    staleTime: 30_000,
  });

  const history = getQueryHistory();
  const last20 = history.slice(0, 20);
  const avgLatency = last20.length
    ? Math.round(last20.reduce((a, b) => a + b.latencyMs, 0) / last20.length)
    : 0;
  const avgConfidence = last20.length
    ? Math.round(last20.reduce((a, b) => a + (b.retrievalQuality ?? 0), 0) / last20.length * 100)
    : 0;

  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';

  // Sparkline: last 14 days paper counts (all same day since we can't group without dates easily)
  const sparkPapers = Array.from({ length: 14 }, (_, i) => {
    const d = new Date(); d.setDate(d.getDate() - 13 + i);
    return papers.filter(p => new Date(p.updated_at).toDateString() === d.toDateString()).length;
  });

  const sparkLatency = last20.map(h => h.latencyMs).reverse();
  const sparkConf = last20.map(h => Math.round((h.retrievalQuality ?? 0) * 100)).reverse();

  const weekStart = new Date(); weekStart.setDate(weekStart.getDate() - 7);
  const papersThisWeek = papers.filter(p => new Date(p.updated_at) > weekStart).length;

  return (
    <div style={{ padding: '32px 32px 64px', maxWidth: 1400, margin: '0 auto' }}>
      {/* Hero */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
        style={{ marginBottom: 32, position: 'relative' }}
      >
        <h1 style={{ fontSize: 30, fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.2, marginBottom: 8 }}>
          {greeting}, Researcher
        </h1>
        <p style={{ fontSize: 15, color: 'var(--text-secondary)' }}>
          {papers.length > 0
            ? `${papers.length} paper${papers.length !== 1 ? 's' : ''} indexed · ${history.slice(0, 7).length} quer${history.slice(0, 7).length !== 1 ? 'ies' : 'y'} this week`
            : 'Upload your first paper to get started'}
        </p>
      </motion.div>

      {/* KPI row */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 32 }}>
        <KPICard
          label="Total Papers"
          value={stats?.papers ?? papers.length}
          icon={FileText}
          accent="var(--brand-500)"
          sparkData={sparkPapers}
          delta={papersThisWeek > 0 ? { value: papersThisWeek, label: 'this week' } : undefined}
          onClick={() => navigate('/library')}
          delay={0}
        />
        <KPICard
          label="Total Chunks"
          value={stats?.chunks ?? 0}
          icon={Layers}
          accent="var(--violet-500)"
          sparkData={[stats?.chunks ?? 0]}
          delay={0.08}
        />
        <KPICard
          label="Avg Latency"
          value={avgLatency}
          unit="ms"
          icon={Zap}
          accent="var(--accent-500)"
          sparkData={sparkLatency}
          delta={avgLatency > 0 ? { value: -200, label: 'vs prev' } : undefined}
          onClick={() => navigate('/analytics')}
          delay={0.16}
        />
        <KPICard
          label="Confidence"
          value={avgConfidence}
          unit="%"
          icon={Target}
          accent="var(--emerald-500)"
          sparkData={sparkConf}
          onClick={() => navigate('/analytics')}
          delay={0.24}
        />
      </div>

      {/* Main 2-col */}
      <div style={{ display: 'flex', gap: 24, marginBottom: 32 }}>
        {/* Left: Recent queries */}
        <div style={{
          flex: '0 0 58%',
          background: 'var(--bg-base)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 20,
          overflow: 'hidden',
        }}>
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '20px 20px 0',
          }}>
            <h3 style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)' }}>Recent queries</h3>
            <button
              onClick={() => navigate('/analytics')}
              style={{
                fontSize: 12, color: 'var(--text-brand)', background: 'none',
                border: 'none', cursor: 'pointer',
              }}
            >
              View all →
            </button>
          </div>

          <div style={{ padding: '12px 8px', maxHeight: 480, overflowY: 'auto' }} className="scroll-area">
            {history.length === 0 ? (
              <div style={{
                display: 'flex', flexDirection: 'column', alignItems: 'center',
                padding: '48px 24px', gap: 12,
              }}>
                <div style={{ fontSize: 40, opacity: 0.2 }}>🔍</div>
                <div style={{ fontSize: 15, fontWeight: 500, color: 'var(--text-secondary)' }}>No queries yet</div>
                <div style={{ fontSize: 13, color: 'var(--text-muted)', textAlign: 'center' }}>
                  Start by asking a question about your papers
                </div>
                <button
                  onClick={() => navigate('/query')}
                  style={{
                    marginTop: 8, padding: '8px 16px',
                    background: 'var(--brand-500)', color: 'white',
                    border: 'none', borderRadius: 8, cursor: 'pointer',
                    fontSize: 13, fontWeight: 500,
                  }}
                >
                  Go to Query →
                </button>
              </div>
            ) : (
              history.slice(0, 15).map(entry => (
                <QueryRow
                  key={entry.id}
                  entry={entry}
                  onClick={() => navigate(`/query?q=${encodeURIComponent(entry.question)}`)}
                />
              ))
            )}
          </div>
        </div>

        {/* Right: Pipeline health + Index stats */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Pipeline health */}
          <PipelineHealth />
          {/* Index stats */}
          <IndexStats />
        </div>
      </div>

      {/* Library strip */}
      <div style={{
        background: 'var(--bg-base)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 20,
        padding: 20,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <h3 style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)' }}>Your Library</h3>
            <span style={{
              fontSize: 10, fontWeight: 600,
              background: 'rgba(99,102,241,0.2)', color: 'var(--brand-300)',
              padding: '2px 7px', borderRadius: 999,
            }}>
              {papers.length}
            </span>
          </div>
          <button
            onClick={() => setUploadOpen(true)}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '7px 14px',
              background: 'var(--brand-500)', color: 'white',
              border: 'none', borderRadius: 8, cursor: 'pointer',
              fontSize: 13, fontWeight: 500,
            }}
          >
            <Upload size={14} /> Upload Paper
          </button>
        </div>

        <div style={{
          display: 'flex', gap: 16,
          overflowX: 'auto', paddingBottom: 8,
          scrollSnapType: 'x mandatory',
        }} className="scroll-area">
          {/* Upload new card */}
          <motion.div
            whileHover={{ y: -4, transition: { duration: 0.2 } }}
            onClick={() => setUploadOpen(true)}
            style={{
              width: 220, flexShrink: 0, height: 180,
              background: 'var(--bg-sunken)',
              border: '2px dashed var(--border-default)',
              borderRadius: 20, cursor: 'pointer',
              display: 'flex', flexDirection: 'column',
              alignItems: 'center', justifyContent: 'center', gap: 8,
              scrollSnapAlign: 'start',
              transition: 'border-color 150ms',
            }}
            onMouseEnter={e => ((e.currentTarget as HTMLDivElement).style.borderColor = 'var(--brand-500)')}
            onMouseLeave={e => ((e.currentTarget as HTMLDivElement).style.borderColor = 'var(--border-default)')}
          >
            <Upload size={28} style={{ color: 'var(--brand-500)' }} />
            <span style={{ fontSize: 13, color: 'var(--text-brand)', fontWeight: 500 }}>Add paper</span>
          </motion.div>

          {papers.map(paper => (
            <PaperCard
              key={paper.paper_id}
              paper={paper}
              onQuery={() => navigate(`/query?paper=${paper.paper_id}`)}
            />
          ))}
        </div>
      </div>

      {uploadOpen && (
        <UploadModal
          open={uploadOpen}
          onClose={() => setUploadOpen(false)}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ['papers'] });
            queryClient.invalidateQueries({ queryKey: ['stats'] });
            addNotification({ type: 'success', title: 'Paper indexed', description: 'Your PDF has been ingested successfully.' });
          }}
        />
      )}
    </div>
  );
}

function PipelineHealth() {
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: api.health,
    refetchInterval: 60_000,
    retry: false,
  });

  const stages = [
    { name: 'Dense Search',  active: true,  weight: 80 },
    { name: 'Sparse (BM25)', active: true,  weight: 40 },
    { name: 'RRF Fusion',    active: true,  weight: 60 },
    { name: 'Reranker',      active: true,  weight: 90 },
    { name: 'Compression',   active: true,  weight: 50 },
  ];

  return (
    <div style={{
      background: 'var(--bg-base)',
      border: '1px solid var(--border-subtle)',
      borderRadius: 20, padding: 20, flex: 1,
    }}>
      <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 14 }}>
        Pipeline Health
      </h3>
      {stages.map(stage => (
        <div key={stage.name} style={{
          display: 'flex', alignItems: 'center', gap: 8,
          marginBottom: 8,
        }}>
          <span style={{ fontSize: 12, color: 'var(--text-secondary)', width: 110, flexShrink: 0 }}>
            {stage.name}
          </span>
          <div style={{
            flex: 1, height: 4,
            background: 'var(--bg-raised)',
            borderRadius: 999, overflow: 'hidden',
          }}>
            <div style={{
              height: '100%',
              width: `${stage.weight}%`,
              background: stage.active ? 'var(--brand-500)' : 'var(--border-strong)',
              borderRadius: 999,
              transition: 'width 0.8s cubic-bezier(0.16,1,0.3,1)',
            }} />
          </div>
          <span style={{
            fontSize: 10, fontWeight: 600,
            color: stage.active ? 'var(--success-text)' : 'var(--text-muted)',
            background: stage.active ? 'var(--success-bg)' : 'transparent',
            padding: '2px 6px', borderRadius: 999,
            flexShrink: 0,
          }}>
            {stage.active ? 'Active' : 'Off'}
          </span>
        </div>
      ))}
    </div>
  );
}

function IndexStats() {
  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: api.stats,
    staleTime: 30_000,
  });

  const items = [
    { label: 'HNSW Index',  value: stats ? 'Loaded' : 'Unknown' },
    { label: 'BM25 Index',  value: stats ? 'Loaded' : 'Unknown' },
    { label: 'Enrichment',  value: 'Complete' },
  ];

  return (
    <div style={{
      background: 'var(--bg-base)',
      border: '1px solid var(--border-subtle)',
      borderRadius: 20, padding: 20, flex: 1,
    }}>
      <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 14 }}>
        Index Statistics
      </h3>
      {items.map(item => (
        <div key={item.label} style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          marginBottom: 10,
        }}>
          <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{item.label}</span>
          <span style={{
            fontSize: 11, fontWeight: 500,
            color: item.value === 'Loaded' || item.value === 'Complete' ? 'var(--success-text)' : 'var(--text-muted)',
            background: item.value === 'Loaded' || item.value === 'Complete' ? 'var(--success-bg)' : 'transparent',
            padding: '2px 7px', borderRadius: 999,
          }}>
            {item.value}
          </span>
        </div>
      ))}
    </div>
  );
}
