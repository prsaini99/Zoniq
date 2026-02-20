/*
 * Main layout: wraps all authenticated/public pages (home, events, cart, etc.).
 * Renders the site Header and Footer around the page content.
 * On mount, fetches the current user's profile (if a token exists)
 * so that auth state is available to all child pages.
 */

"use client";

import { useEffect } from "react";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
import { useAuthStore } from "@/store/auth";

export default function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { fetchProfile, isAuthenticated } = useAuthStore();

  // Fetch the user profile on mount if a session token exists
  useEffect(() => {
    // Fetch user profile on mount if we have a token
    fetchProfile();
  }, [fetchProfile]);

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      {/* Main content area grows to fill available space between header and footer */}
      <main className="flex-1">{children}</main>
      <Footer />
    </div>
  );
}
