/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          900: "#070b16",
        },
        sky: {
          300: "#8fd0ff",
          400: "#5cb8ff",
          500: "#38a5ff",
        },
        fragile: "#ff7a90",
      },
      fontFamily: {
        // Rounded, friendly — falls back through platform rounded faces
        // then a clean sans, no web-font fetch required.
        rounded: [
          "ui-rounded",
          '"SF Pro Rounded"',
          '"Hiragino Maru Gothic ProN"',
          '"Quicksand"',
          '"Varela Round"',
          "system-ui",
          "sans-serif",
        ],
      },
      boxShadow: {
        glow: "0 0 40px -8px rgba(92, 184, 255, 0.35)",
        card: "0 8px 40px -12px rgba(0, 0, 0, 0.6)",
      },
      keyframes: {
        floaty: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-6px)" },
        },
      },
      animation: {
        floaty: "floaty 6s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
