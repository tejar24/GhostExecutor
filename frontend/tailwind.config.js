/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'ghost': {
          'bg': '#0d1117',
          'surface': '#161b22',
          'border': '#30363d',
          'text': '#c9d1d9',
          'text-muted': '#8b949e',
          'green': '#3fb950',
          'red': '#f85149',
          'yellow': '#d29922',
          'blue': '#58a6ff',
        }
      },
      fontFamily: {
        'mono': ['Consolas', 'Monaco', 'Courier New', 'monospace'],
      }
    },
  },
  plugins: [],
}
