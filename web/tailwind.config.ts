import type { Config } from 'tailwindcss';
import typography from '@tailwindcss/typography';

export default {
  content: ['./src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter var', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      colors: {
        surface: {
          primary: 'hsl(var(--surface-primary) / <alpha-value>)',
          secondary: 'hsl(var(--surface-secondary) / <alpha-value>)',
          tertiary: 'hsl(var(--surface-tertiary) / <alpha-value>)',
        },
        text: {
          primary: 'hsl(var(--text-primary) / <alpha-value>)',
          secondary: 'hsl(var(--text-secondary) / <alpha-value>)',
        },
        claim: { DEFAULT: '#E1F5EE', text: '#085041' },
        context: { DEFAULT: '#E6F1FB', text: '#0C447C' },
        result: { DEFAULT: '#E1F5EE', text: '#085041' },
        method: { DEFAULT: '#E6F1FB', text: '#0C447C' },
        comp: { DEFAULT: '#EEEDFE', text: '#3C3489' },
        def: { DEFAULT: '#FAEEDA', text: '#633806' },
        figure: { DEFAULT: '#EEEDFE', text: '#3C3489' },
        table: { DEFAULT: '#FAEEDA', text: '#633806' },
      },
      animation: {
        'stream-in': 'stream-in 80ms ease forwards',
        shimmer: 'shimmer 1.4s ease infinite',
        'fade-up': 'fade-up 200ms ease',
      },
      keyframes: {
        'stream-in': {
          from: { opacity: '0', transform: 'translateY(2px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        'fade-up': {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
      borderWidth: { DEFAULT: '0.5px' },
      borderRadius: { sm: '6px', md: '8px', lg: '12px', xl: '16px' },
    },
  },
  plugins: [typography],
} satisfies Config;
