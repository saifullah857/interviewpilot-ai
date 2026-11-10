/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: { DEFAULT: '#FB873F', soft: '#FFEBDD', deep: '#B84A0D' },
        ink: { DEFAULT: '#171B26', soft: '#4A5163', mute: '#6B7285' },
        deck: { DEFAULT: '#1B2438', raised: '#26324B' },
        surface: '#FFFFFF',
        canvas: '#F4F6F9',
        line: '#DDE1E9',
        ok: { DEFAULT: '#1D7A4C', soft: '#E2F4EA' },
        warn: { DEFAULT: '#8A5A00', soft: '#FFF1CF' },
        bad: { DEFAULT: '#B42318', soft: '#FDE8E6' },
        info: { DEFAULT: '#2457B8', soft: '#E4ECFB' },
      },
      fontFamily: {
        display: ['"Bricolage Grotesque Variable"', 'system-ui', 'sans-serif'],
        sans: ['"Public Sans Variable"', 'system-ui', 'Segoe UI', 'sans-serif'],
      },
      boxShadow: { lift: '0 1px 2px rgba(23,27,38,.06), 0 6px 18px -8px rgba(23,27,38,.18)' },
    },
  },
  plugins: [],
}
