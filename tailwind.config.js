/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.html",
    "./components/**/*.html",
    "./build.py",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "surface": "#fcfbf7",
        "surface-dim": "#f5f4f0",
        "inverse-surface": "#2f3131",
        "secondary": "#5a5e63",
        "on-surface": "#1c1c1c",
        "primary": "#6558b5",
        "secondary-accent": "#df8e1d",
        "tertiary": "#6558b5",
        "surface-container": "#f1f0ec",
        "surface-container-low": "#f8f7f3",
        "surface-container-lowest": "#ffffff",
        "surface-container-high": "#ebeae5",
        "outline-variant": "#d1d1cc",
        "on-surface-variant": "#4a4c4c",
      },
      fontFamily: {
        "headline": ["JetBrains Mono"],
        "body": ["Inter", "system-ui", "sans-serif"],
        "label": ["JetBrains Mono"],
        "mono": ["JetBrains Mono"],
      },
      borderRadius: {
        DEFAULT: "0.125rem",
        lg: "0.25rem",
        xl: "0.5rem",
        full: "0.75rem",
      },
    },
  },
  plugins: [
    require("@tailwindcss/forms"),
    require("@tailwindcss/container-queries"),
  ],
};
