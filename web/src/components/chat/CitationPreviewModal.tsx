import type { Citation } from '../../store/ragStore';

type Props = {
  citation: Citation;
  onClose: () => void;
};

export function CitationPreviewModal({ citation, onClose }: Props) {
  return (
    <div className="fixed inset-0 z-50 bg-black/30 p-6" onClick={onClose}>
      <div
        className="mx-auto mt-16 max-w-2xl rounded-xl border border-slate-300 bg-surface-primary p-4"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="text-base font-semibold">Citation Source</h3>
            <p className="mt-1 text-xs text-text-secondary">
              paper {citation.paper_id} · section {citation.section} · p.{citation.page_number}
            </p>
          </div>
          <button onClick={onClose} className="rounded-md border border-slate-300 px-2 py-1 text-xs">
            Close
          </button>
        </div>

        <div className="mt-3 rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm">
          <div className="text-xs font-semibold text-text-secondary">Chunk</div>
          <div className="mt-1 break-all font-mono text-xs">{citation.chunk_id}</div>
          <p className="mt-3 text-xs text-text-secondary">
            Use Document Structure view to inspect this section and highlighted source passage.
          </p>
        </div>
      </div>
    </div>
  );
}
