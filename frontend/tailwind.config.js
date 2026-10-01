/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        panel: "var(--panel)",
        raised: "var(--raised)",
        line: "var(--line)",
        line2: "var(--line-strong)",
        fg: "var(--fg)",
        fg2: "var(--fg-2)",
        fg3: "var(--fg-3)",
        accent: "var(--accent)",
        ok: "var(--ok)",
        warn: "var(--warn)",
        bad: "var(--bad)",
      },
      fontFamily: {
        sans: ['"Geist"', "system-ui", "sans-serif"],
        mono: ['"Geist Mono"', "ui-monospace", "monospace"],
      },
      borderRadius: {
        panel: "10px",
      },
    },
  },
  plugins: [],
};
