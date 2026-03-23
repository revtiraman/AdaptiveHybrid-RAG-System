import { useMemo } from 'react';
import { useRagStore } from '../../store/ragStore';

export function DocumentStructureViewer() {
  const papers = useRagStore((s) => s.papers);

  const sections = useMemo(
    () => [
      { name: 'abstract', chunks: 8, tables: 0 },
      { name: 'introduction', chunks: 16, tables: 0 },
      { name: 'method', chunks: 24, tables: 2 },
      { name: 'results', chunks: 18, tables: 5 },
      { name: 'conclusion', chunks: 7, tables: 0 },
    ],
    [],
  );

  return (
    <div className="grid h-full grid-cols-[280px_1fr] gap-0">
      <aside className="border-r border-slate-300 bg-surface-primary p-3">
        <h3 className="text-sm font-semibold">Section tree</h3>
        <div className="mt-3 space-y-2">
          {sections.map((section) => (
            <div key={section.name} className="rounded-md border border-slate-300 p-2 text-sm">
              <div className="font-medium">{section.name}</div>
              <div className="text-xs text-text-secondary">{section.chunks} chunks · {section.tables} tables</div>
            </div>
          ))}
        </div>
      </aside>
      <section className="overflow-y-auto p-4">
        <div className="rounded-lg border border-slate-300 bg-surface-primary p-4">
          <h3 className="font-semibold">Extraction summary</h3>
          <p className="mt-2 text-sm text-text-secondary">
            Parser quality insights and chunk inspector for selected paper. Indexed papers: {papers.length}.
          </p>
        </div>
      </section>
    </div>
  );
}
