/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        sdu: {
          night: '#090b18',
          ink: '#0d102d',
          navy: '#1f235f',
          royal: '#2c3279',
          copper: '#f1a86d',
          sand: '#f8eee6',
          mist: '#c7cee9'
        }
      },
      boxShadow: {
        glow: '0 20px 60px rgba(13, 16, 45, 0.45)',
        copper: '0 12px 40px rgba(241, 168, 109, 0.18)'
      },
      keyframes: {
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(18px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' }
        },
        shimmer: {
          '0%': { backgroundPosition: '200% 0' },
          '100%': { backgroundPosition: '-200% 0' }
        }
      },
      animation: {
        'fade-up': 'fade-up 0.7s ease-out both',
        shimmer: 'shimmer 2.5s linear infinite'
      }
    }
  },
  plugins: []
}
