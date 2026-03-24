import React, { useState, useMemo } from 'react';
import type { Paper } from '../types';

interface Props {
  papers: Paper[];
  loading: boolean;
  selected: Set<string>;
  onToggle: (id: string) => void;
  onSelectAll: () => void;
  onClearSelection: () => void;
  onUpload: () => void;
  onRefresh: () => void;
}

export default function Sidebar({ papers, loading, selected, onToggle, onSelectAll, onClearSelection, onUpload, onRefresh }: Props) {
  const [search, setSearch] = useState('');

  const filtered = useMemo(() =>
    papers.filter(p => p.title.toLowerCase().includes(search.toLowerCase())),
    [papers, search],
  );

  const allSelected = papers.length > 0 && papers.every(p => selected.has(p.paper_id));

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', height: '100%',
      background: 'var(--bg-surface)', borderRight: '1px solid var(--border)',
    }}>
      {/* Header */}
      <div style={{ padding: '14px 14px 10px', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
          <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Paper Library
          </span>
          <div style={{ display: 'flex', gap: 4 }}>
            <IconButton onClick={onRefresh} title="Refresh">
              <RefreshIcon />
            </IconButton>
            <button onClick={onUpload} style={{
              display: 'flex', alignItems: 'center', gap: 5,
              background: 'var(--accent)', border: 'none', color: '#fff',
              borderRadius: 6, padding: '4px 10px', cursor: 'pointer',
              fontSize: 12, fontWeight: 500,
            }}>
              <UploadIcon /> Upload
            </button>
          </div>
        </div>

        {/* Search */}
        <div style={{ position: 'relative' }}>
          <SearchIcon style={{ position: 'absolute', left: 8, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search papers…"
            style={{
              width: '100%', background: 'var(--bg-input)', border: '1px solid var(--border)',
              borderRadius: 6, padding: '6px 8px 6px 28px', color: 'var(--text-primary)',
              fontSize: 12, outline: 'none',
            }}
          />
        </div>

        {/* Select all / clear */}
        {papers.length > 0 && (
          <div style={{ display: 'flex', gap: 6, marginTop: 8 }}>
            <button onClick={allSelected ? onClearSelection : onSelectAll} style={scopeBtn}>
              {allSelected ? 'Deselect all' : 'Select all'}
            </button>
            {selected.size > 0 && !allSelected && (
              <button onClick={onClearSelection} style={scopeBtn}>Clear</button>
            )}
          </div>
        )}
      </div>

      {/* Paper list */}
      <div className="scroll-area" style={{ flex: 1, padding: '8px 6px' }}>
        {loading ? (
          <LoadingSkeleton />
        ) : filtered.length === 0 ? (
          <EmptyLibrary search={search} onUpload={onUpload} />
        ) : (
          filtered.map(paper => (
            <PaperItem
              key={paper.paper_id}
              paper={paper}
              selected={selected.has(paper.paper_id)}
              onToggle={onToggle}
            />
          ))
        )}
      </div>

      {/* Footer */}
      {papers.length > 0 && (
        <div style={{
          padding: '8px 14px', borderTop: '1px solid var(--border)',
          fontSize: 11, color: 'var(--text-muted)', flexShrink: 0,
        }}>
          {papers.length} paper{papers.length !== 1 ? 's' : ''} indexed
          {selected.size > 0 && ` · ${selected.size} selected`}
        </div>
      )}
    </div>
  );
}

/* ── Paper item ── */
function PaperItem({ paper, selected, onToggle }: { paper: Paper; selected: boolean; onToggle: (id: string) => void }) {
  const initial = paper.title.charAt(0).toUpperCase();
  const color   = hashColor(paper.paper_id);

  return (
    <button
      onClick={() => onToggle(paper.paper_id)}
      style={{
        display: 'flex', alignItems: 'flex-start', gap: 10, width: '100%',
        background: selected ? 'rgba(99,102,241,.1)' : 'none',
        border: `1px solid ${selected ? 'rgba(99,102,241,.4)' : 'transparent'}`,
        borderRadius: 8, padding: '8px 10px', cursor: 'pointer',
        textAlign: 'left', marginBottom: 2, transition: 'background .12s, border-color .12s',
      }}
    >
      {/* Avatar */}
      <div style={{
        width: 30, height: 30, borderRadius: 6, flexShrink: 0,
        background: color, display: 'flex', alignItems: 'center',
        justifyContent: 'center', fontSize: 13, fontWeight: 700, color: '#fff',
      }}>
        {initial}
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          fontSize: 12.5, fontWeight: 500, color: selected ? '#a5b4fc' : 'var(--text-primary)',
          lineHeight: 1.4, marginBottom: 3,
          overflow: 'hidden', display: '-webkit-box',
          WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
        }}>
          {paper.title}
        </div>
        <div style={{ display: 'flex', gap: 8, fontSize: 10.5, color: 'var(--text-muted)' }}>
          <span>{paper.chunk_count} chunks</span>
          {paper.page_count > 0 && <span>{paper.page_count}pp</span>}
        </div>
      </div>

      {/* Checkbox */}
      <div style={{
        width: 16, height: 16, borderRadius: 4, flexShrink: 0, marginTop: 2,
        border: `1.5px solid ${selected ? '#6366f1' : 'var(--border-light)'}`,
        background: selected ? '#6366f1' : 'transparent',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        transition: 'all .12s',
      }}>
        {selected && (
          <svg width="9" height="7" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="1,3.5 3.5,6 8,1" />
          </svg>
        )}
      </div>
    </button>
  );
}

/* ── Helpers ── */
function EmptyLibrary({ search, onUpload }: { search: string; onUpload: () => void }) {
  if (search) return (
    <div style={{ padding: 16, textAlign: 'center', color: 'var(--text-muted)', fontSize: 12 }}>
      No papers match "{search}"
    </div>
  );
  return (
    <div style={{ padding: 20, textAlign: 'center' }}>
      <div style={{ fontSize: 28, marginBottom: 8 }}>📄</div>
      <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 12, lineHeight: 1.5 }}>
        No papers indexed yet.<br />Upload a PDF to get started.
      </p>
      <button onClick={onUpload} style={{
        background: 'var(--accent)', border: 'none', color: '#fff',
        borderRadius: 6, padding: '6px 14px', cursor: 'pointer', fontSize: 12, fontWeight: 500,
      }}>
        Upload PDF
      </button>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div style={{ padding: '4px 4px', display: 'flex', flexDirection: 'column', gap: 6 }}>
      {[1, 2, 3].map(i => (
        <div key={i} style={{ display: 'flex', gap: 10, padding: '8px 10px' }}>
          <div className="skeleton" style={{ width: 30, height: 30, borderRadius: 6, flexShrink: 0 }} />
          <div style={{ flex: 1 }}>
            <div className="skeleton" style={{ height: 12, marginBottom: 6, width: '85%' }} />
            <div className="skeleton" style={{ height: 10, width: '50%' }} />
          </div>
        </div>
      ))}
    </div>
  );
}

function IconButton({ onClick, title, children }: { onClick: () => void; title: string; children: React.ReactNode }) {
  return (
    <button onClick={onClick} title={title} style={{
      background: 'none', border: '1px solid var(--border)', borderRadius: 6,
      color: 'var(--text-secondary)', cursor: 'pointer', padding: 5,
      display: 'flex', alignItems: 'center',
    }}>
      {children}
    </button>
  );
}

const scopeBtn: React.CSSProperties = {
  background: 'var(--bg-input)', border: '1px solid var(--border)',
  color: 'var(--text-secondary)', borderRadius: 5, padding: '3px 8px',
  cursor: 'pointer', fontSize: 11,
};

function hashColor(id: string): string {
  let h = 0;
  for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) | 0;
  const colors = ['#6366f1','#8b5cf6','#ec4899','#14b8a6','#f59e0b','#3b82f6','#10b981','#ef4444'];
  return colors[Math.abs(h) % colors.length];
}

function RefreshIcon() {
  return (
    <svg width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M11 4.5A5 5 0 1 0 12 8" /><polyline points="12,1 12,4.5 8.5,4.5" />
    </svg>
  );
}
function UploadIcon() {
  return (
    <svg width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17,8 12,3 7,8"/><line x1="12" y1="3" x2="12" y2="15"/>
    </svg>
  );
}
function SearchIcon({ style }: { style?: React.CSSProperties }) {
  return (
    <svg width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" style={style}>
      <circle cx="6" cy="6" r="4"/><line x1="9.5" y1="9.5" x2="13" y2="13"/>
    </svg>
  );
}
