import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // 60% Dominant Canvas
        "canvas-obsidian": "#0B0F19",
        "canvas-midnight": "#0F1624",
        // 30% Structural Surface
        "surface-slate": "#131C2E",
        "surface-elevated": "#1B263B",
        "border-hairline": "#23324D",
        "quant-teal": "#0D9488",
        "quant-teal-dark": "#047857",
        // 10% Accent
        "signal-emerald": "#10B981",
        "signal-emerald-dark": "#059669",
        "alpha-amber": "#F59E0B",
        "alpha-amber-dark": "#D97706",
        // Typography & Semantic States
        "text-primary": "#F8FAFC",
        "text-secondary": "#CBD5E1",
        "text-muted": "#94A3B8",
        "semantic-loss": "#F87171",
        "semantic-warn": "#FBBF24",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "Inter", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
