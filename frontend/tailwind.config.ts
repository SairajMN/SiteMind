import type { Config } from "tailwindcss";

export default {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        stitch: {
          bg: "var(--stitch-bg)",
          surface: "var(--stitch-surface)",
          cyan: "var(--stitch-accent-cyan)",
          violet: "var(--stitch-accent-violet)",
        },
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-geist-mono)", "monospace"],
      },
      borderRadius: {
        stitch: "var(--stitch-radius-lg)",
      },
      boxShadow: {
        stitch: "var(--stitch-shadow-md)",
        "stitch-glow": "var(--stitch-shadow-glow)",
      },
    },
  },
  plugins: [],
} satisfies Config;
