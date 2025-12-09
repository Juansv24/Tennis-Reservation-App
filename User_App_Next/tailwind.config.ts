import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'us-open-blue': '#001854',
        'us-open-light-blue': '#2478CC',
        'us-open-yellow': '#FFD400',
        'available-green': '#4CAF50',
        'taken-gray': '#9E9E9E',
        'maintenance-orange': '#FF9800',
      },
    },
  },
  plugins: [],
}
export default config
