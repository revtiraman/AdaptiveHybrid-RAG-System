type Props = { level: 'HIGH' | 'MEDIUM' | 'LOW' };

const map = {
  HIGH: 'bg-green-100 text-green-700',
  MEDIUM: 'bg-amber-100 text-amber-700',
  LOW: 'bg-red-100 text-red-700',
} as const;

export function ConfidenceBadge({ level }: Props) {
  return <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${map[level]}`}>{level}</span>;
}
