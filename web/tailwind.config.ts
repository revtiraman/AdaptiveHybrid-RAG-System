import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        canvas: '#F4EFE6',
        ink: '#111827',
        accent: '#0F766E',
        signal: '#BE123C',
      },
      fontFamily: {
        display: ['Space Grotesk', 'sans-serif'],
        body: ['IBM Plex Sans', 'sans-serif'],
      },
      backgroundImage: {
        mesh: 'radial-gradient(circle at 15% 20%, rgba(15,118,110,0.15), transparent 40%), radial-gradient(circle at 85% 0%, rgba(190,18,60,0.12), transparent 35%), linear-gradient(180deg, #f4efe6 0%, #ffffff 60%)',
      },
    },
  },
  plugins: [],
} satisfies Config;
