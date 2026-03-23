import { useState } from 'react';

export function LiteratureReviewPanel() {
  const [topic, setTopic] = useState('Transformer-based retrieval');

  return (
    <div className="h-full overflow-y-auto p-4">
      <div className="rounded-lg border border-slate-300 bg-surface-primary p-4">
        <h3 className="font-semibold">Literature Review Generator</h3>
        <div className="mt-3 grid gap-3 md:grid-cols-[1fr_auto]">
          <input value={topic} onChange={(event) => setTopic(event.target.value)} className="rounded-md border border-slate-300 px-3 py-2 text-sm" />
          <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white">Generate</button>
        </div>
      </div>
    </div>
  );
}
