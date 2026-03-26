import React, { useEffect, useRef, useState, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
// cmdk v1 — named exports only (no Command.Input etc.)
import {
  Command,
  CommandInput,
  CommandList,
  CommandItem,
  CommandGroup,
  CommandEmpty,
} from 'cmdk';
import {
  Search, Bell, BellRing, Upload, BarChart3, Settings,
  Clock, FileText, MessageSquare, X,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { useAppStore } from '../lib/store';
import { getQueryHistory } from '../lib/history';
import NotificationCenter from './NotificationCenter';

const ROUTE_LABELS: Record<string, string> = {
  '/':          'Dashboard',
  '/library':   'Library',
  '/query':     'Query',
  '/analytics': 'Analytics',
  '/settings':  'Settings',
};

export default function TopBar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { commandOpen, setCommandOpen, notifications } = useAppStore();
  const [notifOpen, setNotifOpen] = useState(false);
  const [cmdQuery, setCmdQuery] = useState('');

  const { data: papers = [] } = useQuery({
    queryKey: ['papers'],
    queryFn: api.papers,
    staleTime: 30_000,
  });

  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: api.stats,
    staleTime: 60_000,
  });

  const unreadCount = notifications.filter(n => !n.read).length;
  const history = getQueryHistory().slice(0, 5);

  // ⌘K shortcut
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCommandOpen(true);
      }
      if (e.key === 'Escape') {
        setCommandOpen(false);
        setNotifOpen(false);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [setCommandOpen]);

  useEffect(() => {
    if (!commandOpen) setCmdQuery('');
  }, [commandOpen]);

  // Close notif when clicking outside
  useEffect(() => {
    if (!notifOpen) return;
    const handler = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest('[data-notif-panel]') && !target.closest('[data-notif-btn]')) {
        setNotifOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [notifOpen]);

  // Breadcrumbs
  const routeParts = location.pathname.split('/').filter(Boolean);
  const breadcrumbs = [
    { label: 'Home', href: '/' },
    ...routeParts.map((part, i) => ({
      label: ROUTE_LABELS[`/${part}`] ?? part,
      href: '/' + routeParts.slice(0, i + 1).join('/'),
    })),
  ];

  const providerLabel = stats
    ? `${stats.embedding_provider?.split('/').pop() ?? 'BGE'} · ${stats.llm_provider?.split('/').pop() ?? 'Mistral'}`
    : '···';

  return (
    <>
      <header style={{
        height: 56, flexShrink: 0,
        display: 'flex', alignItems: 'center',
        padding: '0 20px', gap: 16,
        background: 'rgba(7,7,15,0.80)',
        backdropFilter: 'blur(24px) saturate(180%)',
        WebkitBackdropFilter: 'blur(24px) saturate(180%)',
        borderBottom: '1px solid var(--border-faint)',
        position: 'sticky', top: 0, zIndex: 50,
      }}>
        {/* Breadcrumbs */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: 4, flex: 1, minWidth: 0 }}>
          {breadcrumbs.map((crumb, i) => (
            <React.Fragment key={crumb.href}>
              {i > 0 && <span style={{ color: 'var(--text-muted)', fontSize: 13, padding: '0 2px' }}>/</span>}
              {i === breadcrumbs.length - 1 ? (
                <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>{crumb.label}</span>
              ) : (
                <button
                  onClick={() => navigate(crumb.href)}
                  style={{
                    background: 'none', border: 'none', cursor: 'pointer',
                    fontSize: 13, color: 'var(--text-muted)', padding: '2px 4px', borderRadius: 4,
                  }}
                  onMouseEnter={e => (e.currentTarget.style.color = 'var(--text-secondary)')}
                  onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-muted)')}
                >
                  {crumb.label}
                </button>
              )}
            </React.Fragment>
          ))}
        </nav>

        {/* Command bar trigger */}
        <button
          onClick={() => setCommandOpen(true)}
          style={{
            display: 'flex', alignItems: 'center', gap: 8,
            width: 340, padding: '0 12px', height: 34,
            background: 'var(--bg-sunken)',
            border: '1px solid var(--border-default)',
            borderRadius: 999, cursor: 'text',
            transition: 'border-color 150ms',
          }}
          onMouseEnter={e => (e.currentTarget.style.borderColor = 'var(--border-strong)')}
          onMouseLeave={e => (e.currentTarget.style.borderColor = 'var(--border-default)')}
        >
          <Search size={13} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
          <span style={{ flex: 1, fontSize: 13, color: 'var(--text-muted)', textAlign: 'left' }}>
            Search or ask...
          </span>
          <span style={{
            fontSize: 10, padding: '2px 5px',
            background: 'var(--bg-overlay)',
            color: 'var(--text-muted)', borderRadius: 4,
          }}>
            ⌘K
          </span>
        </button>

        {/* Right controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{
            fontSize: 11, fontWeight: 500,
            padding: '4px 10px',
            background: 'var(--bg-raised)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 999,
            color: 'var(--text-secondary)',
            whiteSpace: 'nowrap',
          }}>
            {providerLabel}
          </span>

          <div style={{ width: 1, height: 20, background: 'var(--border-faint)' }} />

          {/* Bell */}
          <div style={{ position: 'relative' }}>
            <button
              data-notif-btn
              onClick={() => setNotifOpen(v => !v)}
              style={{
                width: 32, height: 32,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                background: notifOpen ? 'var(--bg-raised)' : 'transparent',
                border: 'none', borderRadius: 8, cursor: 'pointer',
                color: 'var(--text-muted)',
                transition: 'background 120ms, color 120ms',
                position: 'relative',
              }}
              onMouseEnter={e => {
                (e.currentTarget as HTMLButtonElement).style.color = 'var(--text-primary)';
                (e.currentTarget as HTMLButtonElement).style.background = 'var(--bg-raised)';
              }}
              onMouseLeave={e => {
                if (!notifOpen) {
                  (e.currentTarget as HTMLButtonElement).style.color = 'var(--text-muted)';
                  (e.currentTarget as HTMLButtonElement).style.background = 'transparent';
                }
              }}
            >
              {unreadCount > 0 ? <BellRing size={15} /> : <Bell size={15} />}
              {unreadCount > 0 && (
                <span style={{
                  position: 'absolute', top: 5, right: 5,
                  width: 6, height: 6, borderRadius: '50%',
                  background: 'var(--rose-500)',
                  border: '1px solid var(--bg-canvas)',
                }} />
              )}
            </button>
            <AnimatePresence>
              {notifOpen && (
                <div data-notif-panel>
                  <NotificationCenter onClose={() => setNotifOpen(false)} />
                </div>
              )}
            </AnimatePresence>
          </div>

          {/* Avatar */}
          <div style={{
            width: 28, height: 28, borderRadius: '50%',
            background: 'linear-gradient(135deg, var(--brand-500), var(--accent-500))',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 11, fontWeight: 700, color: 'white', cursor: 'pointer', flexShrink: 0,
          }}>
            R
          </div>
        </div>
      </header>

      {/* Command Palette */}
      <AnimatePresence>
        {commandOpen && (
          <CommandPalette
            query={cmdQuery}
            setQuery={setCmdQuery}
            onClose={() => setCommandOpen(false)}
            papers={papers}
            history={history}
            navigate={navigate}
          />
        )}
      </AnimatePresence>
    </>
  );
}

interface PaletteProps {
  query: string;
  setQuery: (q: string) => void;
  onClose: () => void;
  papers: any[];
  history: any[];
  navigate: (to: string) => void;
}

function CommandPalette({ query, setQuery, onClose, papers, history, navigate }: PaletteProps) {
  const handleSelect = useCallback((value: string) => {
    if (value.startsWith('nav:')) navigate(value.slice(4));
    else if (value.startsWith('ask:')) navigate(`/query?q=${encodeURIComponent(value.slice(4))}`);
    else if (value.startsWith('history:')) navigate(`/query?q=${encodeURIComponent(value.slice(8))}`);
    else if (value.startsWith('paper:')) navigate('/library');
    onClose();
  }, [navigate, onClose]);

  const filteredPapers = papers
    .filter(p => !query || p.title.toLowerCase().includes(query.toLowerCase()))
    .slice(0, 4);

  const filteredHistory = history
    .filter(h => !query || h.question.toLowerCase().includes(query.toLowerCase()))
    .slice(0, 4);

  const actions = [
    { value: 'nav:/library', label: 'Upload PDF', icon: Upload, color: 'var(--brand-500)' },
    { value: 'nav:/analytics', label: 'View Analytics', icon: BarChart3, color: 'var(--accent-500)' },
    { value: 'nav:/settings', label: 'Open Settings', icon: Settings, color: 'var(--text-muted)' },
  ].filter(a => !query || a.label.toLowerCase().includes(query.toLowerCase()));

  return (
    <>
      {/* Backdrop */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.15 }}
        onClick={onClose}
        style={{
          position: 'fixed', inset: 0, zIndex: 200,
          background: 'rgba(0,0,0,0.6)',
          backdropFilter: 'blur(8px)',
        }}
      />

      {/* Panel */}
      <motion.div
        initial={{ opacity: 0, y: -16, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -8, scale: 0.97 }}
        transition={{ type: 'spring', stiffness: 400, damping: 30 }}
        style={{
          position: 'fixed', top: '15%', left: '50%',
          transform: 'translateX(-50%)',
          width: 620, zIndex: 201,
          background: 'var(--bg-raised)',
          border: '1px solid var(--border-default)',
          borderRadius: 20,
          boxShadow: '0 24px 80px rgba(0,0,0,0.7)',
          overflow: 'hidden',
        }}
      >
        <Command shouldFilter={false} style={{ background: 'transparent' }}>
          {/* Input row */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 10,
            padding: '14px 18px',
            borderBottom: '1px solid var(--border-faint)',
          }}>
            <Search size={15} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
            <CommandInput
              value={query}
              onValueChange={setQuery}
              placeholder="Search papers, run queries, open pages..."
              style={{
                flex: 1, background: 'transparent', border: 'none', outline: 'none',
                fontSize: 15, fontWeight: 500, color: 'var(--text-primary)',
                fontFamily: 'inherit',
              }}
            />
            {query && (
              <button
                onClick={() => setQuery('')}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: 2 }}
              >
                <X size={13} />
              </button>
            )}
          </div>

          {/* Results */}
          <CommandList style={{ maxHeight: 380, overflowY: 'auto' }} className="scroll-area">
            <CommandEmpty style={{ padding: '28px', textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
              No results found.
            </CommandEmpty>

            {/* Live ask */}
            {query.length > 1 && (
              <CommandItem
                value={`ask:${query}`}
                onSelect={handleSelect}
                style={cmdItemStyle(true)}
              >
                <MessageSquare size={14} style={{ color: 'var(--brand-400)', flexShrink: 0 }} />
                <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 13 }}>
                  Ask: &ldquo;{query}&rdquo;
                </span>
                <span style={badgeStyle}>↵ Ask</span>
              </CommandItem>
            )}

            {filteredHistory.length > 0 && (
              <CommandGroup heading="Recent queries" style={groupStyle}>
                {filteredHistory.map(h => (
                  <CommandItem key={h.id} value={`history:${h.question}`} onSelect={handleSelect} style={cmdItemStyle()}>
                    <Clock size={13} style={{ color: 'var(--accent-500)', flexShrink: 0 }} />
                    <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 13 }}>
                      {h.question}
                    </span>
                  </CommandItem>
                ))}
              </CommandGroup>
            )}

            {filteredPapers.length > 0 && (
              <CommandGroup heading="Papers" style={groupStyle}>
                {filteredPapers.map(p => (
                  <CommandItem key={p.paper_id} value={`paper:${p.paper_id}`} onSelect={handleSelect} style={cmdItemStyle()}>
                    <FileText size={13} style={{ color: 'var(--violet-500)', flexShrink: 0 }} />
                    <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 13 }}>
                      {p.title}
                    </span>
                    <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{p.chunk_count} chunks</span>
                  </CommandItem>
                ))}
              </CommandGroup>
            )}

            {actions.length > 0 && (
              <CommandGroup heading="Actions" style={groupStyle}>
                {actions.map(a => (
                  <CommandItem key={a.value} value={a.value} onSelect={handleSelect} style={cmdItemStyle()}>
                    <a.icon size={13} style={{ color: a.color, flexShrink: 0 }} />
                    <span style={{ flex: 1, fontSize: 13 }}>{a.label}</span>
                  </CommandItem>
                ))}
              </CommandGroup>
            )}
          </CommandList>

          {/* Footer */}
          <div style={{
            display: 'flex', gap: 14, padding: '10px 18px',
            borderTop: '1px solid var(--border-faint)',
          }}>
            {['↑↓ navigate', '↵ select', 'esc dismiss'].map(hint => (
              <span key={hint} style={{ fontSize: 11, color: 'var(--text-muted)' }}>{hint}</span>
            ))}
          </div>
        </Command>
      </motion.div>
    </>
  );
}

const cmdItemStyle = (highlight = false): React.CSSProperties => ({
  display: 'flex', alignItems: 'center', gap: 10,
  padding: '8px 18px', cursor: 'pointer',
  color: 'var(--text-primary)',
  background: highlight ? 'rgba(99,102,241,0.08)' : 'transparent',
  borderLeft: highlight ? '2px solid var(--brand-500)' : '2px solid transparent',
  listStyle: 'none',
});

const groupStyle: React.CSSProperties = {
  paddingTop: 4,
};

const badgeStyle: React.CSSProperties = {
  fontSize: 10, padding: '2px 6px',
  background: 'var(--bg-overlay)',
  color: 'var(--text-muted)', borderRadius: 4, flexShrink: 0,
};
