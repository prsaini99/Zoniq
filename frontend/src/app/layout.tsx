/* Root layout for the entire ZONIQ application.
 * Sets up custom fonts (Space Grotesk for sans-serif, JetBrains Mono for monospace),
 * defines global SEO metadata (Open Graph, Twitter cards, robots directives),
 * and wraps all pages in a dark-themed HTML shell with antialiased text rendering.
 */

import type { Metadata } from "next";
import localFont from "next/font/local";
import { JetBrains_Mono } from "next/font/google";
import "./globals.css";

// Load Space Grotesk as the primary sans-serif font from a local variable font file
const spaceGrotesk = localFont({
  src: "../fonts/SpaceGrotesk-Variable.ttf",
  variable: "--font-sans",
  display: "swap",
  weight: "300 700",
});

// Load JetBrains Mono from Google Fonts for monospace/code contexts
const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  display: "swap",
});

// Global SEO metadata: title template, description, keywords, OpenGraph, and Twitter cards
export const metadata: Metadata = {
  title: {
    default: "ZONIQ - Event Ticket Booking",
    template: "%s | ZONIQ",
  },
  description:
    "Fair Access. Real Fans. Better Events. Experience the future of event ticketing with ZONIQ.",
  keywords: ["events", "tickets", "booking", "concerts", "sports", "theater"],
  authors: [{ name: "ZONIQ" }],
  creator: "ZONIQ",
  openGraph: {
    type: "website",
    locale: "en_IN",
    url: "https://zoniq.in",
    siteName: "ZONIQ",
    title: "ZONIQ - Event Ticket Booking",
    description:
      "Fair Access. Real Fans. Better Events. Experience the future of event ticketing with ZONIQ.",
  },
  twitter: {
    card: "summary_large_image",
    title: "ZONIQ - Event Ticket Booking",
    description:
      "Fair Access. Real Fans. Better Events. Experience the future of event ticketing with ZONIQ.",
    creator: "@zoniq",
  },
  robots: {
    index: true,
    follow: true,
  },
};

// Root layout component: applies font CSS variables and dark theme to the HTML element
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${spaceGrotesk.variable} ${jetbrainsMono.variable} antialiased min-h-screen bg-background text-foreground`}
      >
        {children}
      </body>
    </html>
  );
}
