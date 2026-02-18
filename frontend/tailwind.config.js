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
                primary: {
                    DEFAULT: "#E53935",
                    hover: "#C62828",
                    light: "rgba(229, 57, 53, 0.15)",
                },
                background: {
                    DEFAULT: "#0B0B0D",
                    soft: "#141418",
                    card: "#1A1A1F",
                    elevated: "#222228",
                },
                foreground: {
                    DEFAULT: "#FFFFFF",
                    muted: "#9A9A9A",
                    subtle: "#666666",
                },
                border: {
                    DEFAULT: "#2A2A30",
                    hover: "#3A3A42",
                },
                success: "#22C55E",
                warning: "#F59E0B",
                error: "#EF4444",
                info: "#3B82F6",
            },
            fontFamily: {
                sans: ["var(--font-geist-sans)", "system-ui", "-apple-system", "sans-serif"],
                mono: ["var(--font-geist-mono)", "monospace"],
            },
        },
    },
    plugins: [],
};
