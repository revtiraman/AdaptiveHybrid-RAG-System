type Props = { venue: string; year: number };

function color(venue: string): string {
  const v = venue.toLowerCase();
  if (v.includes('neurips') || v.includes('icml')) return 'bg-blue-100 text-blue-700';
  if (v.includes('acl') || v.includes('emnlp')) return 'bg-teal-100 text-teal-700';
  if (v.includes('iclr')) return 'bg-violet-100 text-violet-700';
  if (v.includes('arxiv')) return 'bg-slate-100 text-slate-700';
  return 'bg-slate-100 text-slate-700';
}

export function PaperTag({ venue, year }: Props) {
  return <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${color(venue)}`}>{venue} {year}</span>;
}
