import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter var', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      colors: {
        base:    '#0c0c15',
        surface: '#111120',
        card:    '#181828',
        input:   '#1c1c30',
        hover:   '#222238',
        border:  '#2a2a45',
        accent:  '#6366f1',
      },
    },
  },
  plugins: [],
} satisfies Config;
