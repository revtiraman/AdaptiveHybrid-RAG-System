import React, { useEffect, useRef, useState, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Command } from 'cmdk';
import {
  Search, Bell, BellRing, Upload, BarChart3, Settings,
  Clock, FileText, MessageSquare, Trash2, X, ChevronRight,
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
  const inputRef = useRef<HTMLInputElement>(null);

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

  // Cmd+K shortcut
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCommandOpen(true);
      }
      if (e.key === 'Escape') setCommandOpen(false);
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [setCommandOpen]);

  useEffect(() => {
    if (commandOpen) {
      setCmdQuery('');
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [commandOpen]);

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
    : 'Loading...';

  return (
    <>
      <header style={{
        height: 56, flexShrink: 0,
        display: 'flex', alignItems: 'center',
        padding: '0 24px', gap: 16,
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
              {i > 0 && (
                <span style={{ color: 'var(--text-muted)', fontSize: 13, padding: '0 2px' }}>/</span>
              )}
              {i === breadcrumbs.length - 1 ? (
                <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>
                  {crumb.label}
                </span>
              ) : (
                <button
                  onClick={() => navigate(crumb.href)}
                  style={{
                    background: 'none', border: 'none', cursor: 'pointer',
                    fontSize: 13, color: 'var(--text-muted)', padding: '2px 4px', borderRadius: 4,
                    transition: 'color 120ms',
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
            width: 360, padding: '0 12px', height: 34,
            background: 'var(--bg-sunken)',
            border: '1px solid var(--border-default)',
            borderRadius: 999, cursor: 'text',
            transition: 'border-color 150ms, box-shadow 150ms',
          }}
          onMouseEnter={e => {
            (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--border-strong)';
          }}
          onMouseLeave={e => {
            (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--border-default)';
          }}
        >
          <Search size={14} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
          <span style={{ flex: 1, fontSize: 13, color: 'var(--text-muted)', textAlign: 'left' }}>
            Search or ask...
          </span>
          <span style={{
            fontSize: 10, padding: '2px 5px',
            background: 'var(--bg-overlay)',
            color: 'var(--text-muted)',
            borderRadius: 4,
          }}>
            ⌘K
          </span>
        </button>

        {/* Right controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {/* Provider badge */}
          <span style={{
            fontSize: 12, fontWeight: 500,
            padding: '4px 10px',
            background: 'var(--bg-raised)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 999,
            color: 'var(--text-secondary)',
            whiteSpace: 'nowrap',
          }}>
            {providerLabel}
          </span>

          {/* Separator */}
          <div style={{ width: 1, height: 20, background: 'var(--border-faint)' }} />

          {/* Notification bell */}
          <div style={{ position: 'relative' }}>
            <button
              onClick={() => setNotifOpen(!notifOpen)}
              style={{
                width: 32, height: 32,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                background: notifOpen ? 'var(--bg-raised)' : 'transparent',
                border: '1px solid transparent',
                borderRadius: 8, cursor: 'pointer',
                color: 'var(--text-muted)',
                transition: 'background 120ms, color 120ms',
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
              {unreadCount > 0 ? <BellRing size={16} /> : <Bell size={16} />}
              {unreadCount > 0 && (
                <span style={{
                  position: 'absolute', top: 4, right: 4,
                  width: 6, height: 6,
                  borderRadius: '50%',
                  background: 'var(--rose-500)',
                  border: '1px solid var(--bg-canvas)',
                }} />
              )}
            </button>

            <AnimatePresence>
              {notifOpen && (
                <NotificationCenter onClose={() => setNotifOpen(false)} />
              )}
            </AnimatePresence>
          </div>

          {/* Avatar */}
          <div
            style={{
              width: 28, height: 28,
              borderRadius: '50%',
              background: 'linear-gradient(135deg, var(--brand-500), var(--accent-500))',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 11, fontWeight: 700, color: 'white', cursor: 'pointer',
              flexShrink: 0,
            }}
            title="Profile"
          >
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
            inputRef={inputRef}
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

interface CommandPaletteProps {
  query: string;
  setQuery: (q: string) => void;
  inputRef: React.RefObject<HTMLInputElement>;
  onClose: () => void;
  papers: any[];
  history: any[];
  navigate: (to: string) => void;
}

function CommandPalette({ query, setQuery, inputRef, onClose, papers, history, navigate }: CommandPaletteProps) {
  const handleSelect = useCallback((value: string) => {
    if (value.startsWith('nav:')) {
      navigate(value.replace('nav:', ''));
    } else if (value.startsWith('ask:')) {
      navigate(`/query?q=${encodeURIComponent(value.replace('ask:', ''))}`);
    } else if (value.startsWith('history:')) {
      navigate(`/query?q=${encodeURIComponent(value.replace('history:', ''))}`);
    } else if (value.startsWith('paper:')) {
      navigate(`/library`);
    }
    onClose();
  }, [navigate, onClose]);

  const filteredPapers = papers.filter(p =>
    p.title.toLowerCase().includes(query.toLowerCase())
  ).slice(0, 4);

  const filteredHistory = history.filter(h =>
    h.question.toLowerCase().includes(query.toLowerCase())
  ).slice(0, 4);

  const actions = [
    { value: 'nav:/library?upload=1', label: 'Upload PDF', icon: Upload, color: 'var(--brand-500)' },
    { value: 'nav:/analytics',        label: 'View Analytics', icon: BarChart3, color: 'var(--accent-500)' },
    { value: 'nav:/settings',         label: 'Open Settings', icon: Settings, color: 'var(--text-muted)' },
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
          WebkitBackdropFilter: 'blur(8px)',
        }}
      />

      {/* Panel */}
      <motion.div
        initial={{ opacity: 0, y: -20, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -10, scale: 0.97 }}
        transition={{ type: 'spring', stiffness: 400, damping: 30 }}
        style={{
          position: 'fixed', top: '15%', left: '50%', transform: 'translateX(-50%)',
          width: 640, zIndex: 201,
          background: 'var(--bg-raised)',
          border: '1px solid var(--border-default)',
          borderRadius: 20,
          boxShadow: '0 24px 80px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.10)',
          overflow: 'hidden',
        }}
      >
        <Command label="Command palette" shouldFilter={false}>
          {/* Search input */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 10,
            padding: '16px 20px',
            borderBottom: '1px solid var(--border-faint)',
          }}>
            <Search size={16} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
            <Command.Input
              ref={inputRef}
              value={query}
              onValueChange={setQuery}
              placeholder="Search papers, run queries, open pages..."
              style={{
                flex: 1, background: 'transparent', border: 'none', outline: 'none',
                fontSize: 16, fontWeight: 500, color: 'var(--text-primary)',
                fontFamily: 'inherit',
              }}
            />
            {query && (
              <button
                onClick={() => setQuery('')}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: 2 }}
              >
                <X size={14} />
              </button>
            )}
          </div>

          {/* Results */}
          <Command.List
            style={{ maxHeight: 400, overflowY: 'auto', padding: '8px 0' }}
            className="scroll-area"
          >
            <Command.Empty style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
              No results found.
            </Command.Empty>

            {/* Live query option */}
            {query.length > 2 && (
              <Command.Group heading="">
                <CmdItem
                  value={`ask:${query}`}
                  onSelect={handleSelect}
                  icon={<MessageSquare size={15} style={{ color: 'var(--brand-400)' }} />}
                  label={`Ask: "${query}"`}
                  badge="↵ Ask"
                  highlight
                />
              </Command.Group>
            )}

            {/* Recent queries */}
            {filteredHistory.length > 0 && (
              <Command.Group heading="Recent queries">
                {filteredHistory.map(h => (
                  <CmdItem
                    key={h.id}
                    value={`history:${h.question}`}
                    onSelect={handleSelect}
                    icon={<Clock size={15} style={{ color: 'var(--accent-500)' }} />}
                    label={h.question}
                    secondary={new Date(h.timestamp).toLocaleDateString()}
                  />
                ))}
              </Command.Group>
            )}

            {/* Papers */}
            {filteredPapers.length > 0 && (
              <Command.Group heading="Papers">
                {filteredPapers.map(p => (
                  <CmdItem
                    key={p.paper_id}
                    value={`paper:${p.paper_id}`}
                    onSelect={handleSelect}
                    icon={<FileText size={15} style={{ color: 'var(--violet-500)' }} />}
                    label={p.title}
                    secondary={`${p.chunk_count} chunks`}
                  />
                ))}
              </Command.Group>
            )}

            {/* Actions */}
            {actions.length > 0 && (
              <Command.Group heading="Actions">
                {actions.map(a => (
                  <CmdItem
                    key={a.value}
                    value={a.value}
                    onSelect={handleSelect}
                    icon={<a.icon size={15} style={{ color: a.color }} />}
                    label={a.label}
                  />
                ))}
              </Command.Group>
            )}
          </Command.List>

          {/* Footer hints */}
          <div style={{
            display: 'flex', gap: 12, padding: '10px 20px',
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

function CmdItem({
  value, onSelect, icon, label, secondary, badge, highlight,
}: {
  value: string; onSelect: (v: string) => void;
  icon: React.ReactNode; label: string;
  secondary?: string; badge?: string; highlight?: boolean;
}) {
  return (
    <Command.Item
      value={value}
      onSelect={onSelect}
      style={{
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '8px 20px', cursor: 'pointer',
        fontSize: 13, color: 'var(--text-primary)',
        background: highlight ? 'rgba(99,102,241,0.08)' : 'transparent',
        borderLeft: highlight ? '2px solid var(--brand-500)' : '2px solid transparent',
        transition: 'background 80ms',
      }}
      data-selected-style={{
        background: 'var(--bg-overlay)',
        borderLeft: '2px solid var(--brand-500)',
      }}
    >
      {icon}
      <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
        {label}
      </span>
      {secondary && (
        <span style={{ fontSize: 11, color: 'var(--text-muted)', flexShrink: 0 }}>{secondary}</span>
      )}
      {badge && (
        <span style={{
          fontSize: 10, padding: '2px 6px',
          background: 'var(--bg-overlay)',
          color: 'var(--text-muted)',
          borderRadius: 4,
        }}>
          {badge}
        </span>
      )}
    </Command.Item>
  );
}
