import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { useRagStore } from '../../store/ragStore';

const data = [
  { name: 'Full', value: 0.89 },
  { name: 'Rerank', value: 0.84 },
  { name: 'RRF', value: 0.71 },
  { name: 'Vector', value: 0.52 },
  { name: 'BM25', value: 0.48 },
  { name: 'Claims', value: 0.85 },
];

export function EvaluationDashboard() {
  const evalResults = useRagStore((s) => s.evalResults);

  return (
    <div className="h-full overflow-y-auto p-4">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-md border border-slate-300 bg-surface-primary p-3">Precision@5 0.89</div>
        <div className="rounded-md border border-slate-300 bg-surface-primary p-3">Faithfulness 0.91</div>
        <div className="rounded-md border border-slate-300 bg-surface-primary p-3">Latency 487ms</div>
        <div className="rounded-md border border-slate-300 bg-surface-primary p-3">Cache hit 34%</div>
      </div>
      <div className="mt-4 h-80 rounded-md border border-slate-300 bg-surface-primary p-3">
        <h3 className="mb-2 text-sm font-semibold">Retrieval comparison</h3>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" domain={[0, 1]} />
            <YAxis type="category" dataKey="name" width={80} />
            <Tooltip />
            <Bar dataKey="value" fill="#0ea5e9" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      {evalResults ? <pre className="mt-4 rounded-md border border-slate-300 bg-slate-900 p-3 text-xs text-slate-100">{JSON.stringify(evalResults, null, 2)}</pre> : null}
    </div>
  );
}
