/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#FFFFFF",
        canvas: "#F8FAFC",
        surface: "#FFFFFF",
        border: "#E2E8F0",
        foreground: "#0F172A",
        muted: "#64748B",
        primary: {
          DEFAULT: "#0F172A",
          hover: "#1E293B",
        },
        accent: {
          blue: "#2563EB",
          teal: "#0D9488",
          amber: "#D97706",
          rose: "#E11D48",
        },
        action: {
          allow: "#0D9488",
          review: "#D97706",
          block: "#E11D48",
        },
      },
    },
  },
  plugins: [],
};

