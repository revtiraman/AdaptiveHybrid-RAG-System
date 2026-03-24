import React, { useState, useEffect, useRef, useCallback } from 'react';
import type { Paper, SystemStats, Message, QueryResult } from './types';
import { fetchPapers, fetchStats, queryRAG } from './api';
import Sidebar from './components/Sidebar';
import ChatView from './components/ChatView';
import UploadModal from './components/UploadModal';

function genId() {
  return Math.random().toString(36).slice(2, 10);
}

export default function App() {
  const [papers, setPapers]             = useState<Paper[]>([]);
  const [stats, setStats]               = useState<SystemStats | null>(null);
  const [loadingPapers, setLoadingPapers] = useState(true);
  const [backendOk, setBackendOk]       = useState<boolean | null>(null);
  const [selectedPapers, setSelectedPapers] = useState<Set<string>>(new Set());
  const [messages, setMessages]         = useState<Message[]>([]);
  const [querying, setQuerying]         = useState(false);
  const [showUpload, setShowUpload]     = useState(false);
  const [sidebarOpen, setSidebarOpen]   = useState(true);
  const [sidebarWidth, setSidebarWidth] = useState(272);

  const resizing = useRef(false);
  const startX   = useRef(0);
  const startW   = useRef(0);

  /* ── load ── */
  const refreshPapers = useCallback(async () => {
    try {
      const list = await fetchPapers();
      setPapers(list);
      setBackendOk(true);
    } catch {
      setBackendOk(false);
    } finally {
      setLoadingPapers(false);
    }
  }, []);

  useEffect(() => {
    refreshPapers();
    fetchStats().then(setStats).catch(() => {});
  }, [refreshPapers]);

  /* ── resize sidebar ── */
  const onResizeStart = (e: React.MouseEvent) => {
    resizing.current = true;
    startX.current = e.clientX;
    startW.current = sidebarWidth;
    e.preventDefault();
  };
  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (!resizing.current) return;
      setSidebarWidth(Math.max(200, Math.min(420, startW.current + e.clientX - startX.current)));
    };
    const onUp = () => { resizing.current = false; };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    return () => { window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp); };
  }, []);

  /* ── query ── */
  const sendQuery = useCallback(async (question: string) => {
    if (!question.trim() || querying) return;
    const uid = genId(), aid = genId();
    setMessages(prev => [...prev,
      { id: uid, role: 'user', content: question.trim(), timestamp: new Date() },
      { id: aid, role: 'assistant', content: '', isLoading: true, timestamp: new Date() },
    ]);
    setQuerying(true);
    try {
      const result: QueryResult = await queryRAG(
        question.trim(),
        selectedPapers.size > 0 ? [...selectedPapers] : undefined,
      );
      setMessages(prev => prev.map(m =>
        m.id === aid ? { ...m, content: result.answer, result, isLoading: false } : m
      ));
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setMessages(prev => prev.map(m =>
        m.id === aid ? { ...m, content: '', error: msg, isLoading: false } : m
      ));
    } finally {
      setQuerying(false);
    }
  }, [querying, selectedPapers]);

  const togglePaper    = (id: string) => setSelectedPapers(prev => { const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); return n; });
  const selectAll      = () => setSelectedPapers(new Set(papers.map(p => p.paper_id)));
  const clearSelection = () => setSelectedPapers(new Set());
  const clearChat      = () => setMessages([]);

  const refreshAll = () => {
    refreshPapers();
    fetchStats().then(setStats).catch(() => {});
  };

  return (
    <div style={{ display:'flex', flexDirection:'column', height:'100%' }}>

      {/* ── Header ── */}
      <header style={{
        display:'flex', alignItems:'center', gap:10,
        height:52, padding:'0 14px', flexShrink:0,
        background:'var(--bg-surface)', borderBottom:'1px solid var(--border)', zIndex:10,
      }}>
        <button onClick={() => setSidebarOpen(o=>!o)} style={iconBtn} title="Toggle sidebar">
          <MenuIcon />
        </button>

        <span style={{ fontSize:17 }}>🔬</span>
        <span style={{ fontWeight:700, fontSize:15, letterSpacing:'-0.3px', color:'var(--text-primary)' }}>
          Research RAG
        </span>

        <div style={{ display:'flex', gap:5, marginLeft:4 }}>
          {stats && <>
            <Pill c="#6366f1">{stats.papers} papers</Pill>
            <Pill c="#10b981">{(stats.chunks||0).toLocaleString()} chunks</Pill>
            <Pill c="#f59e0b">{stats.llm_provider}</Pill>
          </>}
          {backendOk === false && <Pill c="#ef4444">⚠ Backend offline</Pill>}
        </div>

        <div style={{ flex:1 }} />

        {selectedPapers.size > 0 && (
          <div style={{
            display:'flex', alignItems:'center', gap:6,
            background:'rgba(99,102,241,.12)', border:'1px solid rgba(99,102,241,.4)',
            borderRadius:6, padding:'3px 10px', fontSize:12, color:'#818cf8',
          }}>
            Scoped to {selectedPapers.size} paper{selectedPapers.size>1?'s':''}
            <button onClick={clearSelection} style={{ background:'none', border:'none', cursor:'pointer', color:'inherit', lineHeight:1 }}>✕</button>
          </div>
        )}

        {messages.length > 0 && (
          <button onClick={clearChat} style={{
            background:'none', border:'1px solid var(--border)',
            color:'var(--text-secondary)', borderRadius:6,
            padding:'4px 10px', cursor:'pointer', fontSize:12,
          }}>Clear</button>
        )}
      </header>

      {/* ── Body ── */}
      <div style={{ display:'flex', flex:1, overflow:'hidden' }}>
        {sidebarOpen && (
          <>
            <div style={{ width:sidebarWidth, flexShrink:0, overflow:'hidden' }}>
              <Sidebar
                papers={papers}
                loading={loadingPapers}
                selected={selectedPapers}
                onToggle={togglePaper}
                onSelectAll={selectAll}
                onClearSelection={clearSelection}
                onUpload={() => setShowUpload(true)}
                onRefresh={refreshAll}
              />
            </div>
            <div className="resize-handle" onMouseDown={onResizeStart} />
          </>
        )}
        <div style={{ flex:1, overflow:'hidden' }}>
          <ChatView messages={messages} querying={querying} papers={papers} onSend={sendQuery} />
        </div>
      </div>

      {showUpload && (
        <UploadModal onClose={() => setShowUpload(false)} onSuccess={() => { setShowUpload(false); refreshAll(); }} />
      )}
    </div>
  );
}

const iconBtn: React.CSSProperties = {
  background:'none', border:'none', cursor:'pointer',
  color:'var(--text-secondary)', padding:6, borderRadius:6,
  display:'flex', alignItems:'center',
};

function MenuIcon() {
  return (
    <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="2" y1="4"  x2="14" y2="4"/><line x1="2" y1="8"  x2="14" y2="8"/><line x1="2" y1="12" x2="14" y2="12"/>
    </svg>
  );
}

function Pill({ children, c }: { children: React.ReactNode; c: string }) {
  return (
    <span style={{
      background:`${c}1a`, border:`1px solid ${c}40`, color:c,
      borderRadius:999, padding:'2px 8px', fontSize:11, fontWeight:500, whiteSpace:'nowrap',
    }}>{children}</span>
  );
}
