/*
 * tailwind.config.js — Tailwind CSS configuration for the Zoniq "Midnight Cinema" design system.
 * Extends the default theme with custom colors, fonts, background gradients,
 * animations, keyframes, and box shadows that define the dark, red-accented visual identity.
 */

/** @type {import('tailwindcss').Config} */
module.exports = {
    // Scan all pages, components, and app files for Tailwind class usage
    content: [
        "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            // Custom color palette: dark backgrounds with red primary and orange accent
            colors: {
                primary: {
                    DEFAULT: "#DC2626", // Main brand red
                    hover: "#B91C1C", // Darker red for hover states
                    light: "rgba(220, 38, 38, 0.12)", // Subtle red tint for backgrounds
                    glow: "rgba(220, 38, 38, 0.35)", // Red glow effect
                },
                accent: {
                    DEFAULT: "#F97316", // Orange accent color
                    light: "rgba(249, 115, 22, 0.12)", // Subtle orange tint
                    glow: "rgba(249, 115, 22, 0.3)", // Orange glow effect
                },
                background: {
                    DEFAULT: "#09090B", // Deepest background (near-black)
                    soft: "#111113", // Slightly lighter background
                    card: "#18181B", // Card/surface background
                    elevated: "#27272A", // Elevated surface (modals, dropdowns)
                },
                foreground: {
                    DEFAULT: "#FAFAFA", // Primary text (near-white)
                    muted: "#A1A1AA", // Secondary/muted text
                    subtle: "#52525B", // Tertiary/subtle text and icons
                },
                border: {
                    DEFAULT: "#27272A", // Default border color
                    hover: "#3F3F46", // Border color on hover
                },
                success: "#10B981", // Green for success states
                warning: "#F59E0B", // Amber for warning states
                error: "#EF4444", // Red for error states
                info: "#3B82F6", // Blue for informational states
            },
            // Font stacks using CSS custom properties set in the layout
            fontFamily: {
                sans: ["var(--font-sans)", "system-ui", "-apple-system", "sans-serif"],
                mono: ["var(--font-mono)", "monospace"],
            },
            // Custom background gradient utilities
            backgroundImage: {
                "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
                "gradient-conic": "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
                "shimmer": "linear-gradient(110deg, transparent 33%, rgba(255,255,255,0.03) 50%, transparent 67%)",
            },
            // Custom animation utilities with smooth cubic-bezier easing
            animation: {
                "fade-in": "fadeIn 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards",
                "fade-up": "fadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards",
                "slide-in": "slideIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards",
                "scale-in": "scaleIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards",
                "glow-pulse": "glowPulse 3s ease-in-out infinite", // Pulsing glow effect
                "shimmer": "shimmer 2.5s ease-in-out infinite", // Loading skeleton shimmer
                "float": "float 6s ease-in-out infinite", // Gentle floating motion
            },
            // Keyframe definitions for the custom animations above
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
            // Custom box shadow utilities for glow effects and card depth
            boxShadow: {
                "glow-sm": "0 0 12px -3px rgba(220, 38, 38, 0.3)", // Small red glow
                "glow": "0 0 24px -4px rgba(220, 38, 38, 0.4)", // Medium red glow
                "glow-lg": "0 0 48px -8px rgba(220, 38, 38, 0.5)", // Large red glow
                "glow-accent": "0 0 24px -4px rgba(249, 115, 22, 0.3)", // Orange accent glow
                "card": "0 1px 3px rgba(0,0,0,0.4), 0 8px 24px -4px rgba(0,0,0,0.3)", // Default card shadow
                "card-hover": "0 4px 12px rgba(0,0,0,0.5), 0 16px 48px -8px rgba(0,0,0,0.4)", // Elevated card shadow on hover
            },
        },
    },
    plugins: [],
};
