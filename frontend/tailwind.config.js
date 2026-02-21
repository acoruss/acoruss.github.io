/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "../src/templates/**/*.html",
    "../src/static/js/**/*.js",
  ],
  theme: {
    extend: {},
  },
  plugins: [
    require("@tailwindcss/typography"),
    require("daisyui"),
  ],
  daisyui: {
    themes: [
      {
        acoruss: {
          "primary": "#590303",
          "primary-content": "#ffffff",
          "secondary": "#732D2D",
          "secondary-content": "#ffffff",
          "accent": "#A68080",
          "accent-content": "#0D0D0D",
          "neutral": "#0D0D0D",
          "neutral-content": "#F2F2F2",
          "base-100": "#FFFFFF",
          "base-200": "#F2F2F2",
          "base-300": "#e5e5e5",
          "base-content": "#0D0D0D",
          "info": "#3b82f6",
          "success": "#22c55e",
          "warning": "#f59e0b",
          "error": "#ef4444",
        },
      },
    ],
    darkTheme: false,
    logs: false,
  },
};