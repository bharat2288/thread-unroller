/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'bg-base': '#0c0f0d',
        'bg-surface': '#151715',
        'bg-elevated': '#1a1d1a',
        'accent': '#a67c52',
        'accent-hover': '#b8905f',
        'text-primary': '#e5e5e5',
        'text-secondary': '#888888',
        'border': '#2a2d2a',
      },
    },
  },
  plugins: [],
}
