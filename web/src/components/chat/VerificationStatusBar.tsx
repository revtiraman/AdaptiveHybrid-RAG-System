import { ChevronDown, ChevronUp, ShieldAlert, ShieldCheck, ShieldX } from 'lucide-react';
import { useMemo, useState } from 'react';
import type { VerificationResult } from '../../store/ragStore';

type Props = {
  verification: VerificationResult;
};

export function VerificationStatusBar({ verification }: Props) {
  const [expanded, setExpanded] = useState(false);

  const status = useMemo(() => {
    if (!verification.supported) {
      return {
        icon: <ShieldX size={14} />,
        cls: 'border-red-200 bg-red-50 text-red-700',
        label: `Failed - ${verification.unsupported_claims.length} unsupported claims`,
      };
    }
    if (verification.confidence < 0.75) {
      return {
        icon: <ShieldAlert size={14} />,
        cls: 'border-amber-200 bg-amber-50 text-amber-700',
        label: 'Warnings - some claims have lower grounding confidence',
      };
    }
    return {
      icon: <ShieldCheck size={14} />,
      cls: 'border-green-200 bg-green-50 text-green-700',
      label: `Verified - all grounded · confidence ${verification.confidence.toFixed(2)}`,
    };
  }, [verification]);

  return (
    <div className="mt-2">
      <div className={`flex items-center justify-between gap-2 rounded-md border p-2 text-xs ${status.cls}`}>
        <div className="inline-flex items-center gap-1">
          {status.icon}
          <span>{status.label}</span>
        </div>
        <button onClick={() => setExpanded((v) => !v)} className="rounded border border-current/30 px-1.5 py-0.5">
          {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
        </button>
      </div>

      {expanded ? (
        <div className="mt-1 rounded-md border border-slate-200 bg-slate-50 p-2 text-[11px] text-text-secondary">
          <div>Entity check: {verification.issues?.some((i) => i.type === 'entity') ? 'Warnings present' : 'All entities grounded'}</div>
          <div>Number check: {verification.issues?.some((i) => i.type === 'numeric') ? 'Warnings present' : 'Numbers verified'}</div>
          <div>Citation check: {verification.issues?.some((i) => i.type === 'citation') ? 'Warnings present' : 'Citations valid'}</div>
          <div>Completeness: {verification.issues?.some((i) => i.type === 'completeness') ? 'Potentially incomplete' : 'Sufficient coverage'}</div>
        </div>
      ) : null}
    </div>
  );
}
