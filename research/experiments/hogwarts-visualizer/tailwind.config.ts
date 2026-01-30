import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        gryffindor: {
          primary: '#ae0001',
          secondary: '#d3a625',
          accent: '#740001',
          text: '#d3a625',
          border: '#ae0001',
        },
        slytherin: {
          primary: '#2a623d',
          secondary: '#5d5d5d',
          accent: '#1a472a',
          text: '#aaaaaa',
          border: '#2a623d',
        },
        hufflepuff: {
          primary: '#ecb939',
          secondary: '#000000',
          accent: '#372e29',
          text: '#372e29',
          border: '#ecb939',
        },
        ravenclaw: {
          primary: '#0e4a99',
          secondary: '#946b2d',
          accent: '#222f5b',
          text: '#946b2d',
          border: '#0e4a99',
        },
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
};

export default config;
