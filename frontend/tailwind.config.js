/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "../src/templates/**/*.html",
    "../src/static/js/**/*.js",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [
    require("@tailwindcss/typography"),
    require("daisyui"),
  ],
  daisyui: {
    themes: [
      {
        acoruss: {
          "primary": "#7A1C1C",          // Warmer, slightly brighter maroon — keeps brand identity, better contrast
          "primary-content": "#FFFFFF",
          "secondary": "#3D1C1C",        // Deep warm brown — dark accent for variety
          "secondary-content": "#F5F0EB",
          "accent": "#C8956A",           // Warm amber/gold — beautiful complement to maroon
          "accent-content": "#1A1612",
          "neutral": "#1A1612",          // Warm near-black (not harsh pure black)
          "neutral-content": "#F5F0EB",  // Warm off-white
          "base-100": "#FDFCFA",         // Warm white — easier on the eyes
          "base-200": "#F5F0EB",         // Warm light cream
          "base-300": "#E8E2DA",         // Warm light gray
          "base-content": "#2C2520",     // Warm dark brown for body text — softer than black
          "info": "#4A7FB5",             // Softer blue
          "success": "#4A8C5C",          // Muted green
          "warning": "#C89545",          // Warm amber
          "error": "#B54A4A",            // Muted red (not screaming)
        },
      },
    ],
    darkTheme: false,
    logs: false,
  },
};