/* Auth layout: wraps login and signup pages.
 * Redirects already-authenticated users to the home page.
 * Provides a centered card layout with a header (logo), main content area,
 * and a footer, along with decorative background glow effects.
 */

"use client";

import Link from "next/link";
import Image from "next/image";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useIsAuthenticated } from "@/store/auth";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  // Check if the user is already authenticated via the auth store
  const isAuthenticated = useIsAuthenticated();

  // If already logged in, redirect to the home page immediately
  useEffect(() => {
    if (isAuthenticated) {
      router.replace("/");
    }
  }, [isAuthenticated, router]);

  // Render nothing while redirecting to prevent flash of auth UI
  if (isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen flex flex-col bg-background relative overflow-hidden">
      {/* Atmospheric background elements */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-primary/[0.04] rounded-full blur-[120px] -translate-y-1/2 translate-x-1/4" />
        <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-accent/[0.03] rounded-full blur-[100px] translate-y-1/2 -translate-x-1/4" />
      </div>

      {/* Header with ZONIQ logo linking back to home */}
      <header className="relative z-10 border-b border-border/30">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <Link href="/" className="flex items-center group">
            <Image src="/zoniq-logo.png" alt="ZONIQ" width={120} height={40} className="h-8 w-auto transition-transform duration-300 group-hover:scale-105" priority />
          </Link>
        </div>
      </header>

      {/* Main content area: vertically and horizontally centered, max width for the auth card */}
      <main className="relative z-10 flex-1 flex items-center justify-center p-4 py-12">
        <div className="w-full max-w-md">{children}</div>
      </main>

      {/* Simple footer with copyright */}
      <footer className="relative z-10 border-t border-border/30 py-4">
        <div className="container mx-auto px-4 text-center text-xs text-foreground-subtle">
          &copy; {new Date().getFullYear()} ZONIQ. All rights reserved.
        </div>
      </footer>
    </div>
  );
}
