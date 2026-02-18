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

  useEffect(() => {
    // Fetch user profile on mount if we have a token
    fetchProfile();
  }, [fetchProfile]);

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1">{children}</main>
      <Footer />
    </div>
  );
}
