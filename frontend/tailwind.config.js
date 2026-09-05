/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        card: {
          DEFAULT: "var(--card)",
          foreground: "var(--card-foreground)",
        },
        primary: {
          DEFAULT: "var(--primary)",
          foreground: "var(--primary-foreground)",
          50: "#eff6ff",
          100: "#dbeafe",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
        },
        muted: {
          DEFAULT: "var(--muted)",
          foreground: "#94a3b8",
        },
        border: "var(--border)",
        success: {
          DEFAULT: "var(--success)",
          bg: "var(--success-bg)",
        },
        warning: {
          DEFAULT: "var(--warning)",
          bg: "var(--warning-bg)",
        },
        sidebar: {
          DEFAULT: "#ffffff",
          foreground: "#0f172a",
          border: "#e2e8f0",
          accent: "#f1f5f9",
          muted: "#64748b",
        },
      },
    },
  },
  plugins: [],
};
