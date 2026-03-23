import { ShieldCheck, ShieldAlert, ShieldX } from 'lucide-react';

type Props = { status: 'verified' | 'warning' | 'failed'; title?: string };

export function VerificationShield({ status, title }: Props) {
  const shared = 'inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-semibold';
  if (status === 'verified') return <span title={title} className={`${shared} bg-green-100 text-green-700`}><ShieldCheck size={12} />Verified</span>;
  if (status === 'warning') return <span title={title} className={`${shared} bg-amber-100 text-amber-700`}><ShieldAlert size={12} />Warning</span>;
  return <span title={title} className={`${shared} bg-red-100 text-red-700`}><ShieldX size={12} />Failed</span>;
}
