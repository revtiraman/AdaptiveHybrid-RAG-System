import { useMemo, useState } from 'react';

const mockClaims = [
  { id: '1', type: 'result', confidence: 0.97, text: 'Transformer achieves strong BLEU on WMT.', section: 'results', page: 7 },
  { id: '2', type: 'method', confidence: 0.91, text: 'Model uses multi-head self-attention.', section: 'method', page: 4 },
  { id: '3', type: 'limitation', confidence: 0.72, text: 'Long context costs memory.', section: 'discussion', page: 9 },
];

export function ClaimsPanel() {
  const [query, setQuery] = useState('');
  const [kind, setKind] = useState('all');
  const rows = useMemo(
    () =>
      mockClaims.filter((claim) => {
        if (kind !== 'all' && claim.type !== kind) return false;
        return claim.text.toLowerCase().includes(query.toLowerCase());
      }),
    [kind, query],
  );

  return (
    <div className="h-full overflow-y-auto p-4">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          className="rounded-md border border-slate-300 px-3 py-2 text-sm"
          placeholder="Search claims"
        />
        <select value={kind} onChange={(event) => setKind(event.target.value)} className="rounded-md border border-slate-300 px-2 py-2 text-sm">
          <option value="all">All</option>
          <option value="result">Result</option>
          <option value="method">Method</option>
          <option value="limitation">Limitation</option>
        </select>
      </div>
      <div className="grid gap-2">
        {rows.map((claim) => (
          <div key={claim.id} className="rounded-md border border-slate-300 bg-surface-primary p-3">
            <div className="text-xs uppercase text-text-secondary">{claim.type} · {claim.confidence}</div>
            <div className="mt-1 text-sm">{claim.text}</div>
            <div className="mt-2 text-xs text-text-secondary">{claim.section} · p.{claim.page}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
