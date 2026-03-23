import { motion } from 'framer-motion';
import {
  Bell,
  BookOpen,
  Bot,
  FileText,
  GitBranch,
  HelpCircle,
  LayoutPanelLeft,
  ListChecks,
  Moon,
  Radar,
  Settings,
  Sun,
  Upload,
} from 'lucide-react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts';
import { useActiveSession, useRagStore } from '../../store/ragStore';
import { CommandPalette, type Command } from '../CommandPalette';
import { PaperLibrary } from '../sidebar/PaperLibrary';

const navItems = [
  { to: '/chat', icon: Bot, title: 'Chat (Cmd+1)' },
  { to: '/structure', icon: LayoutPanelLeft, title: 'Document Structure (Cmd+2)' },
  { to: '/claims', icon: ListChecks, title: 'Claims (Cmd+3)' },
  { to: '/graph', icon: GitBranch, title: 'Graph (Cmd+4)' },
  { to: '/eval', icon: Radar, title: 'Evaluation (Cmd+5)' },
  { to: '/review', icon: BookOpen, title: 'Literature Review (Cmd+6)' },
  { to: '/annotate', icon: FileText, title: 'Annotation (Cmd+7)' },
];

const systemItems = [
  { to: '/monitor', icon: Radar, title: 'ArXiv Monitor' },
  { to: '/settings', icon: Settings, title: 'Settings (Cmd+,)' },
  { to: '/help', icon: HelpCircle, title: 'Help (?)' },
];

export function AppShell() {
  const location = useLocation();
  const navigate = useNavigate();
  const session = useActiveSession();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const sidebarCollapsed = useRagStore((s) => s.sidebarCollapsed);
  const toggleSidebar = useRagStore((s) => s.toggleSidebar);
  const papers = useRagStore((s) => s.papers);
  const setPapers = useRagStore((s) => s.setPapers);
  const setPaperScope = useRagStore((s) => s.setPaperScope);
  const clearSessionMessages = useRagStore((s) => s.clearSessionMessages);
  const commandPaletteOpen = useRagStore((s) => s.commandPaletteOpen);
  const toggleCommandPalette = useRagStore((s) => s.toggleCommandPalette);
  const [dark, setDark] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [toasts, setToasts] = useState<Array<{ id: string; text: string; tone: 'ok' | 'error' }>>([]);

  useKeyboardShortcuts();

  const status = useMemo(() => {
    const indexing = papers.some((p) => p.status === 'indexing' || p.status === 'queued');
    if (indexing) return { label: 'Indexing...', color: 'bg-amber-500' };
    const errored = papers.some((p) => p.status === 'error');
    if (errored) return { label: 'Error', color: 'bg-red-500' };
    return { label: 'System ready', color: 'bg-green-500' };
  }, [papers]);

  const apiBase = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000';

  const pushToast = useCallback((text: string, tone: 'ok' | 'error' = 'ok') => {
    const id = Math.random().toString(36).slice(2, 10);
    setToasts((prev) => [...prev, { id, text, tone }]);
    window.setTimeout(() => {
      setToasts((prev) => prev.filter((toast) => toast.id !== id));
    }, 2600);
  }, []);

  const mapPaper = useCallback((entry: Record<string, unknown>) => {
    const updatedRaw = String(entry.updated_at ?? '');
    const year = Number.isNaN(new Date(updatedRaw).getFullYear())
      ? new Date().getFullYear()
      : new Date(updatedRaw).getFullYear();
    return {
      id: String(entry.paper_id ?? ''),
      title: String(entry.title ?? 'Untitled paper'),
      authors: [],
      year,
      venue: 'Imported',
      chunks: Number(entry.chunk_count ?? 0),
      tables: 0,
      claims: 0,
      indexingProgress: 1,
      status: 'ready' as const,
      extractionQuality: 0.85,
      columnsDetected: 1,
      parser: 'docling' as const,
    };
  }, []);

  const refreshPapers = useCallback(async () => {
    try {
      const res = await fetch(`${apiBase}/papers`);
      if (!res.ok) throw new Error('Failed to fetch papers');
      const payload = (await res.json()) as { papers?: Array<Record<string, unknown>> };
      setPapers((payload.papers ?? []).map(mapPaper));
    } catch {
      pushToast('Could not refresh papers from backend', 'error');
    }
  }, [apiBase, mapPaper, pushToast, setPapers]);

  const onUploadFile = useCallback(async (file: File | null) => {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      pushToast('Only PDF uploads are supported', 'error');
      return;
    }
    setUploading(true);
    const form = new FormData();
    form.append('file', file);
    form.append('title', file.name.replace(/\.pdf$/i, ''));
    try {
      const res = await fetch(`${apiBase}/upload`, { method: 'POST', body: form });
      if (!res.ok) {
        const payload = (await res.json().catch(() => ({}))) as { detail?: string };
        throw new Error(payload.detail ?? 'Upload failed');
      }
      await refreshPapers();
      pushToast(`Uploaded ${file.name}`);
      navigate('/chat');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Upload failed';
      pushToast(message, 'error');
    } finally {
      setUploading(false);
    }
  }, [apiBase, navigate, pushToast, refreshPapers]);

  useEffect(() => {
    void refreshPapers();
  }, [refreshPapers]);

  const downloadMarkdown = () => {
    if (!session?.messages.length) return;
    const body = session.messages
      .map((message) => {
        const heading = message.role === 'user' ? '## User' : message.role === 'assistant' ? '## Assistant' : '## System';
        const text = (message.content || message.streamText || '').trim() || '(empty)';
        return `${heading}\n\n${text}`;
      })
      .join('\n\n---\n\n');
    const markdown = `# ${session.name}\n\n${body}\n`;
    const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' });
    const link = document.createElement('a');
    const safeName = session.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '') || 'session';
    link.href = URL.createObjectURL(blob);
    link.download = `${safeName}.md`;
    document.body.appendChild(link);
    link.click();
    URL.revokeObjectURL(link.href);
    document.body.removeChild(link);
  };

  const runCommand = (command: Command) => {
    switch (command.id) {
      case 'upload': {
        inputRef.current?.click();
        return;
      }
      case 'scope-all': {
        if (!papers.length) {
          pushToast('No papers available to scope', 'error');
          return;
        }
        setPaperScope(papers.map((paper) => paper.id));
        pushToast(`Scoped to ${papers.length} papers`);
        navigate('/chat');
        return;
      }
      case 'mode-multihop': {
        pushToast('Multi-hop mode selected');
        navigate('/chat?mode=multihop');
        return;
      }
      case 'clear': {
        if (session) clearSessionMessages(session.id);
        pushToast('Session cleared');
        navigate('/chat');
        return;
      }
      case 'export-markdown': {
        downloadMarkdown();
        pushToast('Session exported as markdown');
        navigate('/chat');
        return;
      }
      default: {
        navigate(command.to);
      }
    }
  };

  return (
    <div className={dark ? 'dark' : ''}>
      <div className="flex h-screen w-full flex-col bg-surface-secondary text-text-primary">
        <header className="flex h-11 items-center justify-between border-b border-slate-300 bg-surface-primary px-3">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <span className="inline-flex h-6 w-6 items-center justify-center rounded-md bg-blue-600 text-white">A</span>
            Adaptive Hybrid RAG
          </div>
          <div className="hidden items-center gap-2 md:flex">
            <button className="rounded-full border border-slate-300 px-2 py-0.5 text-xs">All papers ({papers.length})</button>
            <span className="inline-flex items-center gap-1 rounded-full border border-slate-300 px-2 py-0.5 text-xs">
              <span className={`h-2 w-2 rounded-full ${status.color}`} />
              {status.label}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <button className="rounded-md border border-slate-300 p-1.5" title="Upload" onClick={() => inputRef.current?.click()}>
              <Upload size={14} />
            </button>
            <button className="relative rounded-md border border-slate-300 p-1.5" title="Notifications">
              <Bell size={14} />
              <span className="absolute right-0.5 top-0.5 h-2 w-2 rounded-full bg-red-500" />
            </button>
            <button
              className="rounded-md border border-slate-300 p-1.5"
              title="Theme toggle"
              onClick={() => setDark((v) => !v)}
            >
              {dark ? <Sun size={14} /> : <Moon size={14} />}
            </button>
            <button className="rounded-full border border-slate-300 px-2 py-0.5 text-xs">Cmd+K</button>
          </div>
        </header>

        <div className="flex min-h-0 flex-1">
          <nav className="flex w-[52px] flex-col items-center border-r border-slate-300 bg-surface-primary py-2">
            {navItems.map((item) => {
              const active = location.pathname.startsWith(item.to);
              const Icon = item.icon;
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  title={item.title}
                  className={`mb-1 inline-flex h-9 w-9 items-center justify-center rounded-md border transition ${
                    active ? 'border-slate-500 bg-surface-secondary' : 'border-transparent hover:border-slate-300'
                  }`}
                >
                  <Icon size={16} />
                </Link>
              );
            })}
            <div className="my-2 h-px w-7 bg-slate-300" />
            <div className="mt-auto flex flex-col gap-1">
              {systemItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.to}
                    to={item.to}
                    title={item.title}
                    className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-transparent hover:border-slate-300"
                  >
                    <Icon size={16} />
                  </Link>
                );
              })}
            </div>
          </nav>

          <PaperLibrary
            collapsed={sidebarCollapsed}
            uploading={uploading}
            onUploadClick={() => inputRef.current?.click()}
            onUploadFile={(file) => {
              void onUploadFile(file);
            }}
          />

          <motion.main
            layout
            className="min-w-0 flex-1"
            transition={{ duration: 0.2, ease: 'easeInOut' }}
          >
            <div className="flex h-full flex-col">
              <div className="flex items-center justify-between border-b border-slate-300 bg-surface-primary px-3 py-1">
                <button onClick={toggleSidebar} className="rounded-md border border-slate-300 px-2 py-1 text-xs">
                  {sidebarCollapsed ? 'Show sidebar' : 'Hide sidebar'}
                </button>
                <button onClick={toggleCommandPalette} className="rounded-md border border-slate-300 px-2 py-1 text-xs">
                  Command Palette
                </button>
              </div>
              <div className="min-h-0 flex-1">
                <Outlet />
              </div>
            </div>
          </motion.main>
        </div>
      </div>

      {commandPaletteOpen ? <CommandPalette onClose={toggleCommandPalette} onRun={runCommand} /> : null}
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf,.pdf"
        className="hidden"
        onChange={(event) => {
          const file = event.target.files?.[0] ?? null;
          void onUploadFile(file);
          event.currentTarget.value = '';
        }}
      />
      <div className="pointer-events-none fixed bottom-3 right-3 z-50 flex w-80 max-w-[92vw] flex-col gap-2">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`rounded-md border px-3 py-2 text-xs shadow ${
              toast.tone === 'error' ? 'border-red-300 bg-red-50 text-red-700' : 'border-slate-300 bg-white text-text-primary'
            }`}
          >
            {toast.text}
          </div>
        ))}
      </div>
    </div>
  );
}
