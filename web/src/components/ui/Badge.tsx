import clsx from 'clsx';
import type { ReactNode } from 'react';

type Variant = 'claim' | 'result' | 'method' | 'context' | 'table' | 'figure' | 'def' | 'comp';

type Props = {
  variant: Variant;
  children: ReactNode;
};

const variants: Record<Variant, string> = {
  claim: 'bg-claim text-claim-text',
  result: 'bg-result text-result-text',
  method: 'bg-method text-method-text',
  context: 'bg-context text-context-text',
  table: 'bg-table text-table-text',
  figure: 'bg-figure text-figure-text',
  def: 'bg-def text-def-text',
  comp: 'bg-comp text-comp-text',
};

export function Badge({ variant, children }: Props) {
  return <span className={clsx('rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase', variants[variant])}>{children}</span>;
}
