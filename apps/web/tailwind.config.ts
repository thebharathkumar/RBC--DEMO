import type { Config } from "tailwindcss";

/**
 * Design system reads as a sell-side research product: serif headlines for
 * editorial weight, dense sans-serif for tables, a restrained slate palette,
 * and a single gold accent for emphasis. No rounded chunky cards.
 */
const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          50: "#f6f7f8",
          100: "#eceef1",
          200: "#d3d8df",
          300: "#a9b2bd",
          400: "#7c8693",
          500: "#5b6473",
          600: "#444c58",
          700: "#343a44",
          800: "#1f242c",
          900: "#0f1318",
        },
        slate: {
          50: "#f5f7fa",
          900: "#0b1220",
        },
        gold: {
          400: "#c8a24a",
          500: "#b48a2c",
          600: "#8c6a1f",
        },
        bull: "#2f6a3d",
        bear: "#9b2b2b",
      },
      fontFamily: {
        serif: ['"Source Serif 4"', "Georgia", "serif"],
        sans: ['"Inter"', "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
      },
      borderRadius: {
        none: "0",
        sm: "2px",
        DEFAULT: "3px",
      },
      letterSpacing: {
        editorial: "-0.01em",
      },
    },
  },
  plugins: [],
};

export default config;
