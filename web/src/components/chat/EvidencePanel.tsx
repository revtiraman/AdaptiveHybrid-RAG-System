import { ChevronDown, ChevronUp } from 'lucide-react';
import { useMemo, useState } from 'react';
import type { Citation, Claim } from '../../store/ragStore';

type Props = {
  claims: Claim[];
  onCitationClick: (citation: Citation) => void;
};

export function EvidencePanel({ claims, onCitationClick }: Props) {
  const [open, setOpen] = useState(false);

  const counts = useMemo(() => {
    const claimCount = claims.length;
    const contextCount = claims.reduce((acc, cur) => acc + (cur.citations?.length ?? 0), 0);
    return { claimCount, contextCount };
  }, [claims]);

  return (
    <div className="mt-2 rounded-md border border-slate-200 bg-slate-50 p-2">
      <div className="flex items-center justify-between">
        <div className="text-xs font-semibold">
          {counts.claimCount} evidence items · CLAIM {counts.claimCount} · CONTEXT {counts.contextCount}
        </div>
        <button onClick={() => setOpen((v) => !v)} className="rounded border border-slate-300 px-1.5 py-0.5 text-xs">
          {open ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
        </button>
      </div>

      {open ? (
        <div className="mt-2 space-y-2">
          {claims.map((claim, idx) => (
            <div key={`${claim.claim}-${idx}`} className="rounded-md border border-emerald-200 bg-emerald-50 p-2 text-xs">
              <div className="font-semibold text-emerald-800">[CLAIM]</div>
              <div className="mt-1 text-emerald-900">{claim.claim}</div>
              <div className="mt-2 flex flex-wrap gap-1">
                {(claim.citations ?? []).map((citation, cIdx) => (
                  <button
                    key={`${citation.chunk_id}-${cIdx}`}
                    onClick={() => onCitationClick(citation)}
                    className="rounded border border-blue-200 bg-blue-50 px-1.5 py-0.5 text-[10px] text-blue-700"
                  >
                    [{cIdx + 1}] p.{citation.page_number} {citation.section}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
