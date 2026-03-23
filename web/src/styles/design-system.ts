export const tokens = {
  colors: {
    surface: {
      primary: 'hsl(0 0% 100%)',
      secondary: 'hsl(240 5% 96%)',
      tertiary: 'hsl(240 4% 92%)',
      overlay: 'hsl(240 5% 96% / 0.8)',
    },
    text: {
      primary: 'hsl(240 10% 8%)',
      secondary: 'hsl(240 5% 40%)',
      tertiary: 'hsl(240 4% 60%)',
      inverse: 'hsl(0 0% 100%)',
    },
    success: { bg: '#EAF3DE', border: '#C0DD97', text: '#27500A' },
    warning: { bg: '#FAEEDA', border: '#FAC775', text: '#633806' },
    danger: { bg: '#FCEBEB', border: '#F7C1C1', text: '#791F1F' },
    info: { bg: '#E6F1FB', border: '#B5D4F4', text: '#0C447C' },
    claim: { bg: '#E1F5EE', text: '#085041' },
    context: { bg: '#E6F1FB', text: '#0C447C' },
    table: { bg: '#FAEEDA', text: '#633806' },
    figure: { bg: '#EEEDFE', text: '#3C3489' },
    method: { bg: '#E6F1FB', text: '#0C447C' },
    result: { bg: '#E1F5EE', text: '#085041' },
    def: { bg: '#FAEEDA', text: '#633806' },
    comp: { bg: '#EEEDFE', text: '#3C3489' },
  },
  radius: {
    sm: '6px',
    md: '8px',
    lg: '12px',
    xl: '16px',
    full: '9999px',
  },
  border: {
    subtle: '0.5px solid hsl(240 5% 88%)',
    default: '0.5px solid hsl(240 5% 80%)',
    emphasis: '0.5px solid hsl(240 5% 65%)',
  },
  font: {
    sans: '"Inter var", "Inter", system-ui, sans-serif',
    mono: '"JetBrains Mono", "Fira Code", monospace',
    serif: 'Georgia, serif',
  },
  motion: {
    fast: '120ms ease',
    default: '200ms ease',
    slow: '350ms ease',
    spring: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
  },
} as const;

export function injectTokens(): void {
  const root = document.documentElement;

  root.style.setProperty('--radius-sm', tokens.radius.sm);
  root.style.setProperty('--radius-md', tokens.radius.md);
  root.style.setProperty('--radius-lg', tokens.radius.lg);

  root.style.setProperty('--font-sans', tokens.font.sans);
  root.style.setProperty('--font-mono', tokens.font.mono);

  root.style.setProperty('--motion-fast', tokens.motion.fast);
  root.style.setProperty('--motion-default', tokens.motion.default);

  root.style.setProperty('--surface-primary', '0 0% 100%');
  root.style.setProperty('--surface-secondary', '240 5% 96%');
  root.style.setProperty('--surface-tertiary', '240 4% 92%');

  root.style.setProperty('--text-primary', '240 10% 8%');
  root.style.setProperty('--text-secondary', '240 5% 40%');

  root.style.setProperty('--surface-primary-dark', '240 10% 8%');
  root.style.setProperty('--surface-secondary-dark', '240 8% 14%');
  root.style.setProperty('--text-primary-dark', '0 0% 98%');
  root.style.setProperty('--text-secondary-dark', '240 8% 70%');
}
