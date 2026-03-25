import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  ComposedChart, LineChart, Line, BarChart, Bar, AreaChart, Area,
  XAxis, YAxis, Tooltip, CartesianGrid, Cell, ResponsiveContainer,
  Legend,
} from 'recharts';
import { useAppStore } from '../lib/store';
import { getQueryHistory } from '../lib/history';
import { confidenceColor, latencyColor } from '../ui/tokens';
import { useNavigate } from 'react-router-dom';
import { formatDistanceToNow, format, subDays, isAfter } from 'date-fns';
import { MessageSquare, Zap, Target, BarChart3, ChevronRight, Trash2 } from 'lucide-react';
import QueryHistoryDrawer from '../components/QueryHistoryDrawer';

type Range = '24h' | '7d' | '30d' | 'all';

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: 'var(--bg-overlay)',
      border: '1px solid var(--border-subtle)',
      borderRadius: 10,
      padding: '10px 14px',
      boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
      fontSize: 12,
    }}>
      {label && <div style={{ color: 'var(--text-muted)', marginBottom: 6, fontSize: 11 }}>{label}</div>}
      {payload.map((p: any) => (
        <div key={p.name} style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: p.color, flexShrink: 0 }} />
          <span style={{ color: 'var(--text-secondary)' }}>{p.name}:</span>
          <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{p.value}</span>
        </div>
      ))}
    </div>
  );
}

export default function Analytics() {
  const navigate = useNavigate();
  const { openQueryDrawer } = useAppStore();
  const [range, setRange] = useState<Range>('7d');
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerEntryId, setDrawerEntryId] = useState<string | null>(null);

  const allHistory = getQueryHistory();

  const filtered = useMemo(() => {
    if (range === 'all') return allHistory;
    const cutoff = {
      '24h': subDays(new Date(), 1),
      '7d':  subDays(new Date(), 7),
      '30d': subDays(new Date(), 30),
    }[range];
    return allHistory.filter(h => isAfter(new Date(h.timestamp), cutoff));
  }, [allHistory, range]);

  const avgLatency = filtered.length
    ? Math.round(filtered.reduce((a, b) => a + b.latencyMs, 0) / filtered.length)
    : 0;
  const avgConfidence = filtered.length
    ? Math.round(filtered.reduce((a, b) => a + (b.retrievalQuality ?? 0), 0) / filtered.length * 100)
    : 0;
  const successRate = filtered.length
    ? Math.round(filtered.filter(h => (h.retrievalQuality ?? 0) > 0.6).length / filtered.length * 100)
    : 0;

  // Daily query data for main chart
  const dailyData = useMemo(() => {
    const days = range === '24h' ? 1 : range === '7d' ? 7 : range === '30d' ? 30 : 30;
    return Array.from({ length: days }, (_, i) => {
      const d = subDays(new Date(), days - 1 - i);
      const ds = format(d, 'MMM d');
      const dayQueries = filtered.filter(h => format(new Date(h.timestamp), 'MMM d') === ds);
      return {
        date: ds,
        latency: dayQueries.length ? Math.round(dayQueries.reduce((a, b) => a + b.latencyMs, 0) / dayQueries.length) : 0,
        confidence: dayQueries.length ? Math.round(dayQueries.reduce((a, b) => a + (b.retrievalQuality ?? 0), 0) / dayQueries.length * 100) : 0,
        count: dayQueries.length,
      };
    });
  }, [filtered, range]);

  // Confidence distribution
  const confBuckets = useMemo(() => {
    return Array.from({ length: 10 }, (_, i) => {
      const min = i * 10, max = min + 10;
      return {
        label: `${min}-${max}`,
        count: filtered.filter(h => {
          const pct = (h.retrievalQuality ?? 0) * 100;
          return pct >= min && pct < max;
        }).length,
      };
    });
  }, [filtered]);

  const openDrawer = (id: string) => {
    setDrawerEntryId(id);
    setDrawerOpen(true);
  };

  const kpiCards = [
    { label: 'Queries', value: filtered.length, icon: MessageSquare, color: 'var(--brand-500)' },
    { label: 'Avg Latency', value: `${avgLatency}ms`, icon: Zap, color: 'var(--accent-500)' },
    { label: 'Success Rate', value: `${successRate}%`, icon: Target, color: 'var(--emerald-500)' },
    { label: 'Avg Confidence', value: `${avgConfidence}%`, icon: BarChart3, color: 'var(--violet-500)' },
  ];

  return (
    <div style={{ padding: '32px', maxWidth: 1400, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <h1 style={{ fontSize: 26, fontWeight: 600, color: 'var(--text-primary)' }}>Analytics</h1>

        {/* Range selector */}
        <div style={{
          display: 'flex', background: 'var(--bg-raised)',
          border: '1px solid var(--border-subtle)', borderRadius: 999, padding: 3, gap: 2,
        }}>
          {(['24h', '7d', '30d', 'all'] as Range[]).map(r => (
            <button
              key={r}
              onClick={() => setRange(r)}
              style={{
                padding: '4px 12px', borderRadius: 999,
                background: range === r ? 'var(--brand-500)' : 'transparent',
                border: 'none', cursor: 'pointer',
                fontSize: 12, fontWeight: range === r ? 600 : 400,
                color: range === r ? 'white' : 'var(--text-muted)',
                transition: 'background 150ms, color 150ms',
              }}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      {/* Insufficient data warning */}
      {filtered.length < 3 && (
        <div style={{
          background: 'var(--warning-bg)', border: '1px solid var(--warning-border)',
          borderRadius: 10, padding: '10px 16px', marginBottom: 20,
          fontSize: 13, color: 'var(--warning-text)',
        }}>
          Only {filtered.length} quer{filtered.length !== 1 ? 'ies' : 'y'} in this range. Charts will show when you have more data.
        </div>
      )}

      {/* KPI row */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 24 }}>
        {kpiCards.map((card, i) => (
          <motion.div
            key={card.label}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.06 }}
            style={{
              flex: 1,
              background: 'var(--bg-base)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 16, padding: '18px 20px',
              boxShadow: '0 4px 16px rgba(0,0,0,0.4)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
              <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                {card.label}
              </span>
              <card.icon size={16} style={{ color: card.color }} />
            </div>
            <div style={{ fontSize: 30, fontWeight: 700, color: 'var(--text-primary)', fontVariantNumeric: 'tabular-nums' }}>
              {card.value}
            </div>
          </motion.div>
        ))}
      </div>

      {/* Main chart */}
      <div style={{
        background: 'var(--bg-base)', border: '1px solid var(--border-subtle)',
        borderRadius: 16, padding: '20px', marginBottom: 20,
      }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 16 }}>
          Query Performance Over Time
        </h3>
        <ResponsiveContainer width="100%" height={240}>
          <ComposedChart data={dailyData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-faint)" />
            <XAxis dataKey="date" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
            <YAxis yAxisId="left" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
            <YAxis yAxisId="right" orientation="right" domain={[0, 100]} tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
            <Tooltip content={<CustomTooltip />} />
            <Bar yAxisId="left" dataKey="count" name="Queries" fill="rgba(99,102,241,0.1)" radius={[3, 3, 0, 0]} />
            <Area
              yAxisId="left"
              type="monotone"
              dataKey="latency"
              name="Latency (ms)"
              stroke="var(--brand-500)"
              fill="rgba(99,102,241,0.08)"
              strokeWidth={2}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="confidence"
              name="Confidence %"
              stroke="var(--emerald-500)"
              strokeWidth={1.5}
              dot={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Row 2: 3-col charts */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 20 }}>
        {/* Confidence distribution */}
        <div style={{
          flex: 1, background: 'var(--bg-base)', border: '1px solid var(--border-subtle)',
          borderRadius: 16, padding: 20,
        }}>
          <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>
            Confidence Distribution
          </h3>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={confBuckets}>
              <XAxis dataKey="label" tick={{ fontSize: 9, fill: 'var(--text-muted)' }} />
              <YAxis tick={{ fontSize: 10, fill: 'var(--text-muted)' }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" name="Queries" radius={[3, 3, 0, 0]}>
                {confBuckets.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={confidenceColor(index / 10)}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Top papers */}
        <div style={{
          flex: 1, background: 'var(--bg-base)', border: '1px solid var(--border-subtle)',
          borderRadius: 16, padding: 20,
        }}>
          <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>
            Query Volume by Day
          </h3>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={dailyData.slice(-7)}>
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: 'var(--text-muted)' }} />
              <YAxis tick={{ fontSize: 10, fill: 'var(--text-muted)' }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" name="Queries" fill="var(--brand-500)" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Latency distribution */}
        <div style={{
          flex: 1, background: 'var(--bg-base)', border: '1px solid var(--border-subtle)',
          borderRadius: 16, padding: 20,
        }}>
          <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>
            Latency Trend
          </h3>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={dailyData}>
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: 'var(--text-muted)' }} />
              <YAxis tick={{ fontSize: 10, fill: 'var(--text-muted)' }} />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="latency"
                name="Latency (ms)"
                stroke="var(--accent-500)"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* History table */}
      <div style={{
        background: 'var(--bg-base)', border: '1px solid var(--border-subtle)',
        borderRadius: 16, overflow: 'hidden',
      }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-faint)' }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
            Query History
            <span style={{
              marginLeft: 8, fontSize: 11,
              background: 'rgba(99,102,241,0.2)', color: 'var(--brand-300)',
              padding: '2px 7px', borderRadius: 999,
            }}>
              {filtered.length}
            </span>
          </h3>
        </div>

        {filtered.length === 0 ? (
          <div style={{ padding: '48px 24px', textAlign: 'center' }}>
            <div style={{ fontSize: 32, opacity: 0.2, marginBottom: 8 }}>📊</div>
            <div style={{ fontSize: 14, color: 'var(--text-muted)' }}>No queries in this time range</div>
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: 'var(--bg-raised)', borderBottom: '1px solid var(--border-subtle)' }}>
                {['Question', 'Mode', 'Latency', 'Confidence', 'Verified', 'When', ''].map(h => (
                  <th key={h} style={{
                    padding: '10px 16px', textAlign: 'left',
                    fontSize: 11, fontWeight: 600,
                    color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em',
                  }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.slice(0, 50).map(entry => {
                const latColor = latencyColor(entry.latencyMs);
                const confColor = confidenceColor(entry.retrievalQuality ?? 0);
                return (
                  <tr
                    key={entry.id}
                    style={{ borderBottom: '1px solid var(--border-faint)', transition: 'background 100ms' }}
                    onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = 'var(--bg-raised)'}
                    onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = 'transparent'}
                  >
                    <td style={{ padding: '11px 16px', cursor: 'pointer' }} onClick={() => openDrawer(entry.id)}>
                      <div style={{
                        fontSize: 13, fontWeight: 500, color: 'var(--text-primary)',
                        maxWidth: 280, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                      }}>
                        {entry.question}
                      </div>
                    </td>
                    <td style={{ padding: '11px 16px' }}>
                      <span style={{
                        fontSize: 10, fontWeight: 600,
                        padding: '2px 7px', borderRadius: 999,
                        background: 'var(--bg-raised)', color: 'var(--text-secondary)',
                      }}>
                        standard
                      </span>
                    </td>
                    <td style={{ padding: '11px 16px', fontSize: 13, color: latColor, fontVariantNumeric: 'tabular-nums' }}>
                      {entry.latencyMs}ms
                    </td>
                    <td style={{ padding: '11px 16px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <div style={{ width: 50, height: 4, background: 'var(--bg-overlay)', borderRadius: 999, overflow: 'hidden' }}>
                          <div style={{
                            height: '100%',
                            width: `${Math.round((entry.retrievalQuality ?? 0) * 100)}%`,
                            background: confColor, borderRadius: 999,
                          }} />
                        </div>
                        <span style={{ fontSize: 11, color: confColor, fontVariantNumeric: 'tabular-nums' }}>
                          {Math.round((entry.retrievalQuality ?? 0) * 100)}%
                        </span>
                      </div>
                    </td>
                    <td style={{ padding: '11px 16px' }}>
                      {entry.verified
                        ? <span style={{ fontSize: 12, color: 'var(--success-text)' }}>✓</span>
                        : <span style={{ fontSize: 12, color: 'var(--warning-text)' }}>⚠</span>
                      }
                    </td>
                    <td style={{ padding: '11px 16px', fontSize: 12, color: 'var(--text-muted)' }}>
                      {formatDistanceToNow(new Date(entry.timestamp), { addSuffix: true })}
                    </td>
                    <td style={{ padding: '11px 16px' }}>
                      <button
                        onClick={() => navigate(`/query?q=${encodeURIComponent(entry.question)}`)}
                        style={{
                          display: 'flex', alignItems: 'center', gap: 3,
                          padding: '4px 8px', background: 'none',
                          border: '1px solid var(--border-subtle)',
                          borderRadius: 6, cursor: 'pointer',
                          fontSize: 11, color: 'var(--text-muted)',
                          transition: 'color 120ms, border-color 120ms',
                        }}
                        onMouseEnter={e => {
                          (e.currentTarget as HTMLButtonElement).style.color = 'var(--brand-400)';
                          (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--brand-500)';
                        }}
                        onMouseLeave={e => {
                          (e.currentTarget as HTMLButtonElement).style.color = 'var(--text-muted)';
                          (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--border-subtle)';
                        }}
                      >
                        Re-run <ChevronRight size={10} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {drawerOpen && drawerEntryId && (
        <QueryHistoryDrawer
          entryId={drawerEntryId}
          onClose={() => setDrawerOpen(false)}
        />
      )}
    </div>
  );
}
