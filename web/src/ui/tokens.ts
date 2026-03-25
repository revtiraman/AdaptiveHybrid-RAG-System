/** Single source of truth for all design tokens. */

export const colors = {
  bg: {
    canvas:  '#07070f',
    base:    '#0d0d1a',
    raised:  '#141428',
    overlay: '#1c1c36',
    sunken:  '#050510',
  },
  border: {
    faint:   'rgba(255,255,255,0.04)',
    subtle:  'rgba(255,255,255,0.08)',
    default: 'rgba(255,255,255,0.12)',
    strong:  'rgba(255,255,255,0.20)',
    focus:   'rgba(99,102,241,0.60)',
  },
  brand: {
    300: '#a5b4fc',
    400: '#818cf8',
    500: '#6366f1',
    600: '#4f46e5',
    glow: 'rgba(99,102,241,0.20)',
  },
  accent: {
    400: '#22d3ee',
    500: '#06b6d4',
    glow: 'rgba(6,182,212,0.15)',
  },
  violet:  { 500: '#8b5cf6', glow: 'rgba(139,92,246,0.15)' },
  emerald: { 500: '#10b981' },
  amber:   { 500: '#f59e0b' },
  rose:    { 500: '#f43f5e' },
  text: {
    primary:   '#eeeeff',
    secondary: '#8888bb',
    muted:     '#44446a',
    brand:     '#818cf8',
  },
  semantic: {
    success: { bg: 'rgba(16,185,129,0.10)', border: 'rgba(16,185,129,0.25)', text: '#34d399' },
    warning: { bg: 'rgba(245,158,11,0.10)', border: 'rgba(245,158,11,0.25)', text: '#fbbf24' },
    danger:  { bg: 'rgba(244,63,94,0.10)',  border: 'rgba(244,63,94,0.25)',  text: '#fb7185' },
    info:    { bg: 'rgba(99,102,241,0.10)', border: 'rgba(99,102,241,0.25)', text: '#a5b4fc' },
  },
} as const;

export const shadows = {
  sm:        '0 1px 2px rgba(0,0,0,0.4)',
  md:        '0 4px 16px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.06)',
  lg:        '0 12px 40px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.08)',
  xl:        '0 24px 80px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.10)',
  glowBrand: '0 0 0 1px rgba(99,102,241,0.60), 0 0 20px rgba(99,102,241,0.20)',
  glowAccent:'0 0 20px rgba(6,182,212,0.15)',
  inset:     'inset 0 1px 0 rgba(255,255,255,0.08)',
} as const;

export const motion = {
  duration: {
    instant: 80,
    fast:    150,
    normal:  250,
    slow:    400,
    crawl:   600,
  },
  ease: {
    outExpo:  [0.16, 1, 0.3, 1]    as [number,number,number,number],
    outQuart: [0.25, 1, 0.5, 1]    as [number,number,number,number],
    spring:   [0.34, 1.56, 0.64, 1] as [number,number,number,number],
    inExpo:   [0.7, 0, 0.84, 0]    as [number,number,number,number],
  },
} as const;

export const radius = {
  xs:   4,
  sm:   6,
  md:   10,
  lg:   14,
  xl:   20,
  '2xl':28,
  full: 9999,
} as const;

/** Paper card gradient palette — deterministic from title hash */
export const paperGradients: [string, string][] = [
  ['#6366f1', '#8b5cf6'],  // indigo → violet
  ['#06b6d4', '#3b82f6'],  // cyan → blue
  ['#8b5cf6', '#f43f5e'],  // violet → rose
  ['#10b981', '#06b6d4'],  // emerald → cyan
  ['#f59e0b', '#f97316'],  // amber → orange
  ['#f43f5e', '#8b5cf6'],  // rose → violet
];

export function titleGradient(title: string): [string, string] {
  const hash = title.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0);
  return paperGradients[hash % paperGradients.length];
}

export function confidenceColor(score: number): string {
  if (score >= 0.7) return colors.emerald[500];
  if (score >= 0.4) return colors.amber[500];
  return colors.rose[500];
}

export function latencyColor(ms: number): string {
  if (ms < 2000) return colors.emerald[500];
  if (ms < 5000) return colors.amber[500];
  return colors.rose[500];
}
