import { ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import type { ReasoningStep } from '../../store/ragStore';

type Props = {
  steps: ReasoningStep[];
};

export function ReasoningTrace({ steps }: Props) {
  const [expanded, setExpanded] = useState(false);

  if (!steps.length) return null;

  return (
    <div className="mt-2 rounded-md border border-slate-200 bg-slate-50 p-2">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-semibold">Reasoning Trace</h4>
        <button onClick={() => setExpanded((v) => !v)} className="rounded border border-slate-300 px-1.5 py-0.5 text-xs">
          {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
        </button>
      </div>
      {expanded ? (
        <div className="mt-2 space-y-2">
          {steps.map((step, idx) => (
            <div key={`${step.step}-${idx}`} className="relative pl-4 text-xs">
              <span className="absolute left-0 top-1.5 h-1.5 w-1.5 rounded-full bg-slate-500" />
              <div className="text-text-primary">{step.step}</div>
              {step.latencyMs ? <div className="text-[10px] text-text-secondary">latency {step.latencyMs}ms</div> : null}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
