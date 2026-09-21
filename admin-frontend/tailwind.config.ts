import type { Config } from 'tailwindcss';
import defaultTheme from 'tailwindcss/defaultTheme';

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-inter)', ...defaultTheme.fontFamily.sans],
      },
      colors: {
        brand: {
          50: '#eefcf9',
          100: '#d1f5ec',
          200: '#a6ecda',
          300: '#6fdcc2',
          400: '#3cc4a5',
          500: '#1ea88a',
          600: '#158671',
          700: '#146c5c',
          800: '#14564b',
          900: '#12483f',
          950: '#052924',
        },
        ink: {
          800: '#1a2233',
          900: '#131a29',
          950: '#0b0f19',
        },
      },
      boxShadow: {
        soft: '0 1px 2px 0 rgb(15 23 42 / 0.04), 0 1px 3px 0 rgb(15 23 42 / 0.06)',
        card: '0 1px 2px 0 rgb(15 23 42 / 0.04), 0 8px 24px -12px rgb(15 23 42 / 0.12)',
        glow: '0 0 0 1px rgb(30 168 138 / 0.15), 0 8px 24px -8px rgb(30 168 138 / 0.35)',
      },
      backgroundImage: {
        'sidebar-gradient': 'linear-gradient(180deg, #131a29 0%, #0b0f19 100%)',
      },
    },
  },
  plugins: [],
};

export default config;
