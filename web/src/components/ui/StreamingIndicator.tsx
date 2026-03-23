type Props = { stage: string };

export function StreamingIndicator({ stage }: Props) {
  return (
    <div className="rounded-md border border-slate-300 bg-surface-primary p-2 text-xs">
      <div className="mb-2 flex items-center gap-1">
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-slate-500" />
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-slate-500 [animation-delay:120ms]" />
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-slate-500 [animation-delay:240ms]" />
      </div>
      <div className="text-text-secondary">{stage}</div>
    </div>
  );
}
