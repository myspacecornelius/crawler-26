import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
      },
      colors: {
        background: "#F5F1EA",
        surface: {
          primary: "#FFFFFF",
          warm: "#FAF8F4",
        },
        text: {
          primary: "#1A1A17",
          secondary: "#65635C",
          muted: "#9A978F",
        },
        honey: {
          500: "#E5B94B",
          400: "#F0CC6B",
          glow: "rgba(229,185,75,0.22)",
          tint: "rgba(229,185,75,0.12)",
        },
        petrol: {
          600: "#2F5E63",
          700: "#23474B",
          800: "#1A3538",
          mist: "#DCE8E8",
        },
        charcoal: {
          900: "#171512",
          800: "#1E1B16",
          700: "#2A2620",
          text: "#E8E5DF",
          border: "#2E2A24",
        },
        border: {
          subtle: "#E5E2DA",
          strong: "#CCC9C0",
        },
        success: "#3A8A5C",
        danger: "#C0392B",
      },
      borderRadius: {
        card: "16px",
        glass: "18px",
        button: "10px",
      },
      boxShadow: {
        card: "0 8px 30px rgba(0,0,0,0.06)",
        "card-hover": "0 12px 40px rgba(0,0,0,0.10)",
        "honey-ring": "0 0 0 2px rgba(229,185,75,0.35)",
        "honey-glow": "0 0 20px rgba(229,185,75,0.18)",
        "petrol-glow": "0 0 24px rgba(47,94,99,0.15)",
      },
      maxWidth: {
        container: "1200px",
      },
    },
  },
  plugins: [],
};
export default config;
