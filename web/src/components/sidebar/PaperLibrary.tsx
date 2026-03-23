import { motion } from 'framer-motion';
import { Plus, Search } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useRagStore } from '../../store/ragStore';

type Props = {
  collapsed: boolean;
  uploading?: boolean;
  onUploadClick?: () => void;
  onUploadFile?: (file: File | null) => void;
};

function qualityLabel(score: number): { text: string; cls: string } {
  if (score >= 0.9) return { text: 'Excellent', cls: 'bg-green-100 text-green-800' };
  if (score >= 0.7) return { text: 'Good', cls: 'bg-amber-100 text-amber-800' };
  if (score >= 0.5) return { text: 'Fair', cls: 'bg-orange-100 text-orange-800' };
  return { text: 'Poor', cls: 'bg-red-100 text-red-800' };
}

export function PaperLibrary({ collapsed, uploading = false, onUploadClick, onUploadFile }: Props) {
  const papers = useRagStore((s) => s.papers);
  const activePaperIds = useRagStore((s) => s.activePaperIds);
  const setPaperScope = useRagStore((s) => s.setPaperScope);
  const [query, setQuery] = useState('');
  const [dragActive, setDragActive] = useState(false);

  const filtered = useMemo(() => {
    const q = query.toLowerCase().trim();
    if (!q) return papers;
    return papers.filter((paper) => {
      const bag = `${paper.title} ${paper.authors.join(' ')} ${paper.venue} ${paper.year}`.toLowerCase();
      return bag.includes(q);
    });
  }, [papers, query]);

  return (
    <motion.aside
      animate={{ width: collapsed ? 0 : 240, opacity: collapsed ? 0 : 1 }}
      transition={{ duration: 0.2, ease: 'easeInOut' }}
      style={{ overflow: 'hidden' }}
      className="h-full border-r border-slate-300 bg-surface-primary"
    >
      <div className="flex h-full flex-col">
        <div className="border-b border-slate-300 p-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold">Papers ({papers.length})</h3>
            <button className="rounded-md border border-slate-300 p-1" title="Add paper" onClick={onUploadClick}>
              <Plus size={14} />
            </button>
          </div>
          <div className="mt-2 flex items-center gap-2 rounded-md border border-slate-300 px-2 py-1">
            <Search size={14} className="text-slate-500" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="w-full border-none bg-transparent text-xs outline-none"
              placeholder="Search papers"
            />
          </div>
        </div>

        <div className="flex-1 space-y-2 overflow-y-auto p-2">
          {filtered.map((paper) => {
            const active = activePaperIds.includes(paper.id);
            const quality = qualityLabel(paper.extractionQuality);
            return (
              <button
                key={paper.id}
                onClick={() => setPaperScope(active ? activePaperIds.filter((x) => x !== paper.id) : [...activePaperIds, paper.id])}
                className={`w-full rounded-lg border p-2 text-left transition ${
                  active ? 'border-blue-500 bg-blue-50' : 'border-slate-300 hover:bg-surface-secondary'
                }`}
              >
                <div className="truncate text-sm font-semibold">{paper.title}</div>
                <div className="mt-0.5 text-[11px] text-text-secondary">{paper.venue} {paper.year} · {paper.chunks} chunks · {paper.tables} tbl</div>
                <div className="mt-2 h-1.5 rounded bg-slate-200">
                  <div className="h-full rounded bg-blue-500" style={{ width: `${Math.round(paper.indexingProgress * 100)}%` }} />
                </div>
                <div className={`mt-2 inline-flex rounded-full px-2 py-0.5 text-[10px] font-medium ${quality.cls}`}>{quality.text}</div>
              </button>
            );
          })}
        </div>

        <div className="border-t border-dashed border-slate-300 p-3">
          <div
            role="button"
            tabIndex={0}
            onClick={onUploadClick}
            onDragOver={(event) => {
              event.preventDefault();
              setDragActive(true);
            }}
            onDragLeave={(event) => {
              event.preventDefault();
              setDragActive(false);
            }}
            onDrop={(event) => {
              event.preventDefault();
              setDragActive(false);
              const file = event.dataTransfer.files?.[0] ?? null;
              onUploadFile?.(file);
            }}
            onKeyDown={(event) => {
              if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                onUploadClick?.();
              }
            }}
            className={`rounded-lg border border-dashed p-3 text-center text-xs transition ${
              dragActive
                ? 'border-blue-500 bg-blue-50 text-blue-700'
                : 'border-slate-400 text-text-secondary hover:bg-surface-secondary'
            }`}
          >
            {uploading ? 'Uploading PDF...' : 'Drop PDF here or click to upload'}
          </div>
        </div>
      </div>
    </motion.aside>
  );
}
