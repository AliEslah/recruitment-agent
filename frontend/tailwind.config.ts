import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#f7f8fb",
        foreground: "#172033",
        panel: "#ffffff",
        muted: "#667085",
        line: "#d9dee9",
        accent: "#136f63",
        accentDark: "#0d5149",
        warning: "#a15c07",
        danger: "#b42318",
        success: "#087443",
      },
      boxShadow: {
        soft: "0 10px 30px rgba(16, 24, 40, 0.08)",
      },
    },
  },
  plugins: [],
};

export default config;
