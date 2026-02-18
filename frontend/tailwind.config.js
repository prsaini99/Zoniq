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
                    DEFAULT: "#DC2626",
                    hover: "#B91C1C",
                    light: "rgba(220, 38, 38, 0.12)",
                    glow: "rgba(220, 38, 38, 0.35)",
                },
                accent: {
                    DEFAULT: "#F97316",
                    light: "rgba(249, 115, 22, 0.12)",
                    glow: "rgba(249, 115, 22, 0.3)",
                },
                background: {
                    DEFAULT: "#09090B",
                    soft: "#111113",
                    card: "#18181B",
                    elevated: "#27272A",
                },
                foreground: {
                    DEFAULT: "#FAFAFA",
                    muted: "#A1A1AA",
                    subtle: "#52525B",
                },
                border: {
                    DEFAULT: "#27272A",
                    hover: "#3F3F46",
                },
                success: "#10B981",
                warning: "#F59E0B",
                error: "#EF4444",
                info: "#3B82F6",
            },
            fontFamily: {
                sans: ["var(--font-sans)", "system-ui", "-apple-system", "sans-serif"],
                mono: ["var(--font-mono)", "monospace"],
            },
            backgroundImage: {
                "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
                "gradient-conic": "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
                "shimmer": "linear-gradient(110deg, transparent 33%, rgba(255,255,255,0.03) 50%, transparent 67%)",
            },
            animation: {
                "fade-in": "fadeIn 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards",
                "fade-up": "fadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards",
                "slide-in": "slideIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards",
                "scale-in": "scaleIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards",
                "glow-pulse": "glowPulse 3s ease-in-out infinite",
                "shimmer": "shimmer 2.5s ease-in-out infinite",
                "float": "float 6s ease-in-out infinite",
            },
            keyframes: {
                fadeIn: {
                    from: { opacity: "0" },
                    to: { opacity: "1" },
                },
                fadeUp: {
                    from: { opacity: "0", transform: "translateY(24px)" },
                    to: { opacity: "1", transform: "translateY(0)" },
                },
                slideIn: {
                    from: { opacity: "0", transform: "translateX(-16px)" },
                    to: { opacity: "1", transform: "translateX(0)" },
                },
                scaleIn: {
                    from: { opacity: "0", transform: "scale(0.95)" },
                    to: { opacity: "1", transform: "scale(1)" },
                },
                glowPulse: {
                    "0%, 100%": { opacity: "0.4" },
                    "50%": { opacity: "0.8" },
                },
                shimmer: {
                    "0%": { backgroundPosition: "-200% 0" },
                    "100%": { backgroundPosition: "200% 0" },
                },
                float: {
                    "0%, 100%": { transform: "translateY(0)" },
                    "50%": { transform: "translateY(-8px)" },
                },
            },
            boxShadow: {
                "glow-sm": "0 0 12px -3px rgba(220, 38, 38, 0.3)",
                "glow": "0 0 24px -4px rgba(220, 38, 38, 0.4)",
                "glow-lg": "0 0 48px -8px rgba(220, 38, 38, 0.5)",
                "glow-accent": "0 0 24px -4px rgba(249, 115, 22, 0.3)",
                "card": "0 1px 3px rgba(0,0,0,0.4), 0 8px 24px -4px rgba(0,0,0,0.3)",
                "card-hover": "0 4px 12px rgba(0,0,0,0.5), 0 16px 48px -8px rgba(0,0,0,0.4)",
            },
        },
    },
    plugins: [],
};
