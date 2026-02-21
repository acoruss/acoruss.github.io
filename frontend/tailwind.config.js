/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "../src/templates/**/*.html",
    "../src/static/js/**/*.js",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Urbanist', 'ui-sans-serif', 'system-ui', 'sans-serif'],
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
          "color-scheme": "dark",
          "primary": "#7A1C1C",          // Warm maroon - CTAs, highlights
          "primary-content": "#FFFFFF",
          "secondary": "#3D1C1C",        // Deep warm brown - variety card fills
          "secondary-content": "#F5F0EB",
          "accent": "#C8956A",           // Warm amber/gold - emphasis, featured elements
          "accent-content": "#0F0D0B",
          "neutral": "#0C0A08",          // Deepest dark - footer/CTA subtle diff
          "neutral-content": "#F5F0EB",  // Warm off-white text on dark
          "base-100": "#0F0D0B",         // Very dark warm - page background
          "base-200": "#1A1612",         // Slightly lighter - cards, elevated surfaces
          "base-300": "#2C2520",         // Medium dark - borders, dividers
          "base-content": "#E8E2DA",     // Warm off-white - body text
          "info": "#5B9BD5",             // Soft blue
          "success": "#5B9B6B",          // Muted green
          "warning": "#D4A843",          // Warm gold
          "error": "#C94444",            // Warm red
        },
      },
    ],
    darkTheme: false,
    logs: false,
  },
};