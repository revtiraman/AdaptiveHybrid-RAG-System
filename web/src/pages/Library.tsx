import React, { useState, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  LayoutGrid, List, Search, Upload, Trash2, MessageSquare,
  Layers, X, MoreHorizontal, ChevronUp, ChevronDown,
} from 'lucide-react';
import { api } from '../lib/api';
import { titleGradient } from '../ui/tokens';
import { useAppStore } from '../lib/store';
import type { Paper } from '../types';
import UploadModal from '../components/UploadModal';

type SortKey = 'newest' | 'oldest' | 'chunks' | 'alpha';
type ViewMode = 'grid' | 'list';


export default function Library() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { addNotification } = useAppStore();

  const [uploadOpen, setUploadOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState<SortKey>('newest');
  const [view, setView] = useState<ViewMode>('grid');
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const { data: papers = [], isLoading } = useQuery({
    queryKey: ['papers'],
    queryFn: api.papers,
    staleTime: 30_000,
  });

  const filtered = useMemo(() => {
    let list = [...papers];
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(p => p.title.toLowerCase().includes(q));
    }
    switch (sort) {
      case 'newest': list.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()); break;
      case 'oldest': list.sort((a, b) => new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime()); break;
      case 'chunks': list.sort((a, b) => b.chunk_count - a.chunk_count); break;
      case 'alpha':  list.sort((a, b) => a.title.localeCompare(b.title)); break;
    }
    return list;
  }, [papers, search, sort]);

  const toggleSelect = (id: string) => {
    setSelected(s => {
      const n = new Set(s);
      n.has(id) ? n.delete(id) : n.add(id);
      return n;
    });
  };

  const handleDelete = async (paperId: string) => {
    if (!confirm('Delete this paper?')) return;
    try {
      await api.deletePaper(paperId);
      queryClient.invalidateQueries({ queryKey: ['papers'] });
      addNotification({ type: 'info', title: 'Paper deleted', description: 'Paper removed from index.' });
    } catch {
      addNotification({ type: 'error', title: 'Delete failed', description: 'Could not delete paper.' });
    }
  };

  const handleDeleteSelected = async () => {
    if (!confirm(`Delete ${selected.size} papers?`)) return;
    for (const id of selected) await handleDelete(id);
    setSelected(new Set());
  };

  return (
    <div style={{ padding: '32px', maxWidth: 1400, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <h1 style={{ fontSize: 26, fontWeight: 600, color: 'var(--text-primary)' }}>Library</h1>
          <motion.span
            key={papers.length}
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 0.4, ease: [0.34, 1.56, 0.64, 1] }}
            style={{
              fontSize: 12, fontWeight: 600,
              background: 'rgba(99,102,241,0.2)', color: 'var(--brand-300)',
              padding: '3px 9px', borderRadius: 999,
            }}
          >
            {papers.length}
          </motion.span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {/* Search */}
          <div style={{ position: 'relative' }}>
            <Search size={13} style={{
              position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)',
              color: 'var(--text-muted)', pointerEvents: 'none',
            }} />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search papers..."
              style={{
                paddingLeft: 30, paddingRight: search ? 30 : 12,
                paddingTop: 7, paddingBottom: 7,
                background: 'var(--bg-sunken)',
                border: '1px solid var(--border-default)',
                borderRadius: 999, color: 'var(--text-primary)',
                fontSize: 13, outline: 'none', width: 200,
                fontFamily: 'inherit',
              }}
              onFocus={e => (e.currentTarget.style.borderColor = 'var(--brand-500)')}
              onBlur={e => (e.currentTarget.style.borderColor = 'var(--border-default)')}
            />
            {search && (
              <button
                onClick={() => setSearch('')}
                style={{
                  position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)',
                  background: 'none', border: 'none', cursor: 'pointer',
                  color: 'var(--text-muted)', padding: 2,
                }}
              >
                <X size={12} />
              </button>
            )}
          </div>

          {/* Sort */}
          <select
            value={sort}
            onChange={e => setSort(e.target.value as SortKey)}
            style={{
              padding: '7px 28px 7px 10px',
              background: 'var(--bg-raised)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 8, color: 'var(--text-secondary)',
              fontSize: 13, cursor: 'pointer', outline: 'none',
              fontFamily: 'inherit',
            }}
          >
            <option value="newest">Newest first</option>
            <option value="oldest">Oldest first</option>
            <option value="chunks">Most chunks</option>
            <option value="alpha">Alphabetical</option>
          </select>

          {/* View toggle */}
          <div style={{
            display: 'flex', background: 'var(--bg-raised)',
            border: '1px solid var(--border-subtle)', borderRadius: 8, overflow: 'hidden',
          }}>
            {([['grid', LayoutGrid], ['list', List]] as const).map(([mode, Icon]) => (
              <button
                key={mode}
                onClick={() => setView(mode)}
                style={{
                  padding: '7px 10px', background: view === mode ? 'var(--bg-overlay)' : 'transparent',
                  border: 'none', cursor: 'pointer',
                  color: view === mode ? 'var(--brand-400)' : 'var(--text-muted)',
                  transition: 'background 120ms, color 120ms',
                  display: 'flex', alignItems: 'center',
                }}
              >
                <Icon size={15} />
              </button>
            ))}
          </div>

          {/* Upload */}
          <button
            onClick={() => setUploadOpen(true)}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '8px 16px',
              background: 'var(--brand-500)', color: 'white',
              border: 'none', borderRadius: 8, cursor: 'pointer',
              fontSize: 13, fontWeight: 500,
              transition: 'background 150ms',
            }}
            onMouseEnter={e => (e.currentTarget.style.background = 'var(--brand-400)')}
            onMouseLeave={e => (e.currentTarget.style.background = 'var(--brand-500)')}
          >
            <Upload size={14} /> Upload Paper
          </button>
        </div>
      </div>

      {/* Empty state */}
      {!isLoading && filtered.length === 0 && (
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          padding: '80px 24px', gap: 12,
        }}>
          <div style={{ fontSize: 48, opacity: 0.2 }}>📚</div>
          <div style={{ fontSize: 17, fontWeight: 500, color: 'var(--text-secondary)' }}>
            {search ? 'No papers match your search' : 'No papers yet'}
          </div>
          <div style={{ fontSize: 14, color: 'var(--text-muted)' }}>
            {search ? 'Try a different query' : 'Upload a PDF to get started'}
          </div>
          {!search && (
            <button
              onClick={() => setUploadOpen(true)}
              style={{
                marginTop: 8, padding: '9px 20px',
                background: 'var(--brand-500)', color: 'white',
                border: 'none', borderRadius: 8, cursor: 'pointer', fontSize: 14, fontWeight: 500,
              }}
            >
              Upload PDF
            </button>
          )}
        </div>
      )}

      {/* Grid view */}
      {view === 'grid' && filtered.length > 0 && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
          gap: 16,
        }}>
          {filtered.map((paper, i) => (
            <PaperCardGrid
              key={paper.paper_id}
              paper={paper}
              delay={i * 0.03}
              selected={selected.has(paper.paper_id)}
              onSelect={() => toggleSelect(paper.paper_id)}
              onQuery={() => navigate(`/query?paper=${paper.paper_id}`)}
              onDelete={() => handleDelete(paper.paper_id)}
            />
          ))}
        </div>
      )}

      {/* List view */}
      {view === 'list' && filtered.length > 0 && (
        <PaperTable
          papers={filtered}
          selected={selected}
          onSelect={toggleSelect}
          onQuery={id => navigate(`/query?paper=${id}`)}
          onDelete={handleDelete}
        />
      )}

      {/* Bulk actions bar */}
      <AnimatePresence>
        {selected.size > 0 && (
          <motion.div
            initial={{ y: 80, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 80, opacity: 0 }}
            transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
            style={{
              position: 'fixed', bottom: 24,
              left: '50%', transform: 'translateX(-50%)',
              display: 'flex', alignItems: 'center', gap: 12,
              padding: '12px 20px',
              background: 'rgba(20,20,40,0.95)',
              backdropFilter: 'blur(20px)',
              border: '1px solid var(--border-default)',
              borderRadius: 14,
              boxShadow: '0 24px 80px rgba(0,0,0,0.7)',
              zIndex: 100,
            }}
          >
            <span style={{ fontSize: 14, fontWeight: 500, color: 'var(--text-primary)' }}>
              {selected.size} selected
            </span>
            <button
              onClick={handleDeleteSelected}
              style={{
                display: 'flex', alignItems: 'center', gap: 6,
                padding: '6px 12px',
                background: 'var(--danger-bg)',
                border: '1px solid var(--danger-border)',
                borderRadius: 8, cursor: 'pointer',
                fontSize: 12, color: 'var(--danger-text)',
              }}
            >
              <Trash2 size={12} /> Delete selected
            </button>
            <button
              onClick={() => setSelected(new Set())}
              style={{
                width: 28, height: 28, background: 'var(--bg-overlay)',
                border: 'none', borderRadius: 6, cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: 'var(--text-muted)',
              }}
            >
              <X size={13} />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {uploadOpen && (
        <UploadModal
          open={uploadOpen}
          onClose={() => setUploadOpen(false)}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ['papers'] });
            queryClient.invalidateQueries({ queryKey: ['stats'] });
            addNotification({ type: 'success', title: 'Paper indexed', description: 'Your PDF has been ingested.' });
          }}
        />
      )}
    </div>
  );
}

function PaperCardGrid({ paper, delay, selected, onSelect, onQuery, onDelete }: {
  paper: Paper; delay: number; selected: boolean;
  onSelect: () => void; onQuery: () => void; onDelete: () => void;
}) {
  const [hovered, setHovered] = useState(false);
  const [g1, g2] = titleGradient(paper.title);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: 'var(--bg-base)',
        border: `1px solid ${selected ? 'var(--brand-500)' : 'var(--border-subtle)'}`,
        borderRadius: 20,
        overflow: 'hidden',
        boxShadow: selected ? 'var(--glow-brand)' : '0 4px 16px rgba(0,0,0,0.5)',
        cursor: 'pointer',
        position: 'relative',
      }}
    >
      {/* Gradient header */}
      <div
        style={{
          height: 80,
          background: `linear-gradient(135deg, ${g1}, ${g2})`,
          position: 'relative',
        }}
        className="hex-overlay"
      >
        <div style={{
          position: 'absolute', inset: 0,
          background: 'linear-gradient(to bottom, transparent 30%, rgba(0,0,0,0.55) 100%)',
        }} />

        {/* Status dot */}
        <div style={{
          position: 'absolute', top: 8, right: 8,
          width: 8, height: 8, borderRadius: '50%',
          background: 'var(--emerald-500)',
        }} className="status-pulse" />

        {/* Checkbox */}
        <div
          style={{
            position: 'absolute', top: 8, left: 8,
            width: 18, height: 18,
            borderRadius: 4,
            background: selected ? 'var(--brand-500)' : 'rgba(0,0,0,0.4)',
            border: `1px solid ${selected ? 'var(--brand-500)' : 'rgba(255,255,255,0.3)'}`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}
          onClick={e => { e.stopPropagation(); onSelect(); }}
        >
          {selected && <span style={{ color: 'white', fontSize: 10, fontWeight: 700 }}>✓</span>}
        </div>

        <div style={{
          position: 'absolute', bottom: 8, left: 10, right: 10, zIndex: 1,
          fontSize: 12, fontWeight: 600, color: 'white',
          display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
          overflow: 'hidden', lineHeight: 1.4,
        }}>
          {paper.title}
        </div>
      </div>

      {/* Stats */}
      <div style={{ padding: '12px 12px 8px' }}>
        <div style={{ display: 'flex', gap: 6, marginBottom: 8, flexWrap: 'wrap' }}>
          {[`${paper.page_count}p`, `${paper.chunk_count} chunks`].map(s => (
            <span key={s} style={{
              fontSize: 10, fontWeight: 500,
              padding: '2px 6px',
              background: 'var(--bg-raised)', color: 'var(--text-secondary)',
              borderRadius: 6,
            }}>
              {s}
            </span>
          ))}
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 8 }}>
          {new Date(paper.updated_at).toLocaleDateString()}
        </div>
      </div>

      {/* Action strip — slides up on hover */}
      <AnimatePresence>
        {hovered && (
          <motion.div
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
            style={{
              position: 'absolute', bottom: 0, left: 0, right: 0,
              height: 40,
              background: 'rgba(0,0,0,0.6)',
              backdropFilter: 'blur(8px)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
            }}
          >
            <ActionBtn icon={MessageSquare} onClick={onQuery} title="Query" color="var(--brand-400)" />
            <ActionBtn icon={Layers} onClick={() => {}} title="Structure" color="var(--accent-500)" />
            <ActionBtn icon={Trash2} onClick={onDelete} title="Delete" color="var(--rose-500)" />
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

function ActionBtn({ icon: Icon, onClick, title, color }: { icon: any; onClick: () => void; title: string; color: string }) {
  return (
    <button
      onClick={e => { e.stopPropagation(); onClick(); }}
      title={title}
      style={{
        width: 28, height: 28,
        background: 'rgba(255,255,255,0.1)',
        border: 'none', borderRadius: 7, cursor: 'pointer',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color, transition: 'background 120ms',
      }}
      onMouseEnter={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.2)')}
      onMouseLeave={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.1)')}
    >
      <Icon size={13} />
    </button>
  );
}

function PaperTable({ papers, selected, onSelect, onQuery, onDelete }: {
  papers: Paper[];
  selected: Set<string>;
  onSelect: (id: string) => void;
  onQuery: (id: string) => void;
  onDelete: (id: string) => void;
}) {
  const [sortCol, setSortCol] = useState<'title' | 'chunks' | 'pages' | 'date'>('date');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  const sorted = useMemo(() => {
    return [...papers].sort((a, b) => {
      let cmp = 0;
      switch (sortCol) {
        case 'title':  cmp = a.title.localeCompare(b.title); break;
        case 'chunks': cmp = a.chunk_count - b.chunk_count; break;
        case 'pages':  cmp = a.page_count - b.page_count; break;
        case 'date':   cmp = new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime(); break;
      }
      return sortDir === 'asc' ? cmp : -cmp;
    });
  }, [papers, sortCol, sortDir]);

  const toggleSort = (col: typeof sortCol) => {
    if (sortCol === col) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortCol(col); setSortDir('desc'); }
  };

  const SortIcon = ({ col }: { col: typeof sortCol }) =>
    sortCol === col
      ? (sortDir === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />)
      : null;

  const allSelected = papers.length > 0 && papers.every(p => selected.has(p.paper_id));

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{
            background: 'var(--bg-raised)',
            borderBottom: '1px solid var(--border-subtle)',
          }}>
            <th style={{ width: 40, padding: '10px 12px' }}>
              <input
                type="checkbox"
                checked={allSelected}
                onChange={() => {
                  if (allSelected) papers.forEach(p => selected.has(p.paper_id) && onSelect(p.paper_id));
                  else papers.forEach(p => !selected.has(p.paper_id) && onSelect(p.paper_id));
                }}
                style={{ accentColor: 'var(--brand-500)' }}
              />
            </th>
            {([['title', 'Title'], ['chunks', 'Chunks'], ['pages', 'Pages'], ['date', 'Ingested']] as const).map(([col, label]) => (
              <th
                key={col}
                onClick={() => toggleSort(col)}
                style={{
                  padding: '10px 12px', textAlign: 'left', cursor: 'pointer',
                  fontSize: 12, fontWeight: 600, color: 'var(--text-muted)',
                  letterSpacing: '0.05em', textTransform: 'uppercase',
                  userSelect: 'none',
                }}
              >
                <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  {label} <SortIcon col={col} />
                </span>
              </th>
            ))}
            <th style={{ width: 60, padding: '10px 12px' }} />
          </tr>
        </thead>
        <tbody>
          {sorted.map(paper => (
            <tr
              key={paper.paper_id}
              style={{
                borderBottom: '1px solid var(--border-faint)',
                background: selected.has(paper.paper_id) ? 'rgba(99,102,241,0.06)' : 'transparent',
                transition: 'background 100ms',
              }}
              onMouseEnter={e => { if (!selected.has(paper.paper_id)) (e.currentTarget as HTMLElement).style.background = 'var(--bg-raised)'; }}
              onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = selected.has(paper.paper_id) ? 'rgba(99,102,241,0.06)' : 'transparent'; }}
            >
              <td style={{ padding: '10px 12px' }}>
                <input
                  type="checkbox"
                  checked={selected.has(paper.paper_id)}
                  onChange={() => onSelect(paper.paper_id)}
                  style={{ accentColor: 'var(--brand-500)' }}
                />
              </td>
              <td style={{ padding: '10px 12px', cursor: 'pointer' }} onClick={() => onQuery(paper.paper_id)}>
                <div style={{ fontSize: 14, fontWeight: 500, color: 'var(--text-primary)' }}>
                  {paper.title}
                </div>
              </td>
              <td style={{ padding: '10px 12px', fontSize: 13, color: 'var(--text-secondary)', fontVariantNumeric: 'tabular-nums' }}>
                {paper.chunk_count}
              </td>
              <td style={{ padding: '10px 12px', fontSize: 13, color: 'var(--text-secondary)', fontVariantNumeric: 'tabular-nums' }}>
                {paper.page_count}
              </td>
              <td style={{ padding: '10px 12px', fontSize: 12, color: 'var(--text-muted)' }}>
                {new Date(paper.updated_at).toLocaleDateString()}
              </td>
              <td style={{ padding: '10px 12px' }}>
                <div style={{ display: 'flex', gap: 4 }}>
                  <button
                    onClick={() => onQuery(paper.paper_id)}
                    style={{ width: 28, height: 28, background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', borderRadius: 6 }}
                    title="Query"
                  >
                    <MessageSquare size={13} />
                  </button>
                  <button
                    onClick={() => onDelete(paper.paper_id)}
                    style={{ width: 28, height: 28, background: 'none', border: 'none', cursor: 'pointer', color: 'var(--rose-500)', borderRadius: 6 }}
                    title="Delete"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
