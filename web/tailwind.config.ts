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
        // Background hierarchy
        canvas:  '#07070f',
        base:    '#0d0d1a',
        raised:  '#141428',
        overlay: '#1c1c36',
        sunken:  '#050510',
        // Brand
        brand: {
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#6366f1',
          600: '#4f46e5',
        },
        // Accent
        accent: {
          400: '#22d3ee',
          500: '#06b6d4',
        },
        violet: { 500: '#8b5cf6' },
        emerald: { 500: '#10b981' },
        amber:   { 500: '#f59e0b' },
        rose:    { 500: '#f43f5e' },
        // Text
        primary:   '#eeeeff',
        secondary: '#8888bb',
        muted:     '#44446a',
      },
      spacing: {
        '4.5': '18px',
      },
      borderRadius: {
        xs:   '4px',
        sm:   '6px',
        md:   '10px',
        lg:   '14px',
        xl:   '20px',
        '2xl':'28px',
      },
      boxShadow: {
        sm: '0 1px 2px rgba(0,0,0,0.4)',
        md: '0 4px 16px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.06)',
        lg: '0 12px 40px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.08)',
        xl: '0 24px 80px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.10)',
        'glow-brand': '0 0 0 1px rgba(99,102,241,0.60), 0 0 20px rgba(99,102,241,0.20)',
        'glow-accent': '0 0 20px rgba(6,182,212,0.15)',
      },
      transitionDuration: {
        '80':  '80ms',
        '150': '150ms',
        '250': '250ms',
        '400': '400ms',
        '600': '600ms',
      },
      transitionTimingFunction: {
        'out-expo':  'cubic-bezier(0.16, 1, 0.3, 1)',
        'out-quart': 'cubic-bezier(0.25, 1, 0.5, 1)',
        'spring':    'cubic-bezier(0.34, 1.56, 0.64, 1)',
        'in-expo':   'cubic-bezier(0.7, 0, 0.84, 0)',
      },
      keyframes: {
        fadeUp: {
          from: { opacity: '0', transform: 'translateY(12px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          from: { opacity: '0' },
          to:   { opacity: '1' },
        },
        slideInRight: {
          from: { opacity: '0', transform: 'translateX(20px)' },
          to:   { opacity: '1', transform: 'translateX(0)' },
        },
        pulse: {
          '0%,100%': { opacity: '1' },
          '50%':     { opacity: '0.3' },
        },
        pulseDot: {
          '0%,100%': { transform: 'scale(1)', opacity: '1' },
          '30%':     { transform: 'scale(1.5)', opacity: '0' },
        },
        shimmer: {
          '0%':   { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        spin: {
          to: { transform: 'rotate(360deg)' },
        },
        bobUp: {
          '0%,100%': { transform: 'translateY(0)' },
          '50%':     { transform: 'translateY(-6px)' },
        },
        drawOrb: {
          from: { transform: 'scale(0.92)', opacity: '0' },
          to:   { transform: 'scale(1)',    opacity: '1' },
        },
        scaleBounce: {
          '0%':   { transform: 'scale(1)' },
          '40%':  { transform: 'scale(1.2)' },
          '100%': { transform: 'scale(1)' },
        },
        countUp: {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'fade-up':       'fadeUp 0.35s cubic-bezier(0.16,1,0.3,1) both',
        'fade-in':       'fadeIn 0.25s ease both',
        'slide-right':   'slideInRight 0.25s cubic-bezier(0.16,1,0.3,1) both',
        'pulse-dot':     'pulseDot 2s ease-in-out infinite',
        shimmer:         'shimmer 1.4s ease-in-out infinite',
        spin:            'spin 0.7s linear infinite',
        'bob-up':        'bobUp 2s ease-in-out infinite',
        'scale-bounce':  'scaleBounce 0.4s cubic-bezier(0.34,1.56,0.64,1) both',
        'count-up':      'countUp 0.4s cubic-bezier(0.16,1,0.3,1) both',
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
} satisfies Config;
