type Props = {
  onClose: () => void;
};

export function ExportModal({ onClose }: Props) {
  return (
    <div className="fixed inset-0 z-50 bg-black/30 p-6" onClick={onClose}>
      <div className="mx-auto mt-20 max-w-xl rounded-lg border border-slate-300 bg-surface-primary p-4" onClick={(e) => e.stopPropagation()}>
        <h3 className="font-semibold">Export Session</h3>
        <div className="mt-3 grid gap-2">
          <button className="rounded-md border border-slate-300 px-3 py-2 text-left text-sm">Markdown</button>
          <button className="rounded-md border border-slate-300 px-3 py-2 text-left text-sm">PDF</button>
          <button className="rounded-md border border-slate-300 px-3 py-2 text-left text-sm">BibTeX</button>
          <button className="rounded-md border border-slate-300 px-3 py-2 text-left text-sm">JSON</button>
        </div>
      </div>
    </div>
  );
}
