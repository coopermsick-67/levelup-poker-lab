/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        felt: '#1a6b3c',
        'felt-dark': '#0f4a28',
        gold: '#f0c040',
        'gold-dark': '#d4a020',
      },
    },
  },
  plugins: [],
}
