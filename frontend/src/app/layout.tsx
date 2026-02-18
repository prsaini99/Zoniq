import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

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

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased min-h-screen bg-background text-foreground`}
      >
        {children}
      </body>
    </html>
  );
}
