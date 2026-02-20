/**
 * AdminLayout - Root layout wrapper for all admin pages.
 *
 * Responsibilities:
 * - Enforces authentication and admin role access control.
 * - Renders a responsive sidebar navigation with collapsible state.
 * - Provides a mobile hamburger menu with an overlay.
 * - Displays the current admin user info and a sign-out button.
 * - Wraps all admin child pages via the {children} slot.
 */
"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import {
  LayoutDashboard,
  Calendar,
  Users,
  Ticket,
  MapPin,
  BarChart3,
  Settings,
  LogOut,
  ChevronLeft,
  Menu,
} from "lucide-react";
import { useUser, useIsAuthenticated, useAuthStore, useHasHydrated } from "@/store/auth";
import { useState } from "react";
import { cn } from "@/lib/utils";

// Sidebar navigation items: each maps an icon + label to an admin route
const navItems = [
  { href: "/admin", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/admin/events", icon: Calendar, label: "Events" },
  { href: "/admin/bookings", icon: Ticket, label: "Bookings" },
  { href: "/admin/users", icon: Users, label: "Users" },
  { href: "/admin/venues", icon: MapPin, label: "Venues" },
  { href: "/admin/analytics", icon: BarChart3, label: "Analytics" },
  { href: "/admin/settings", icon: Settings, label: "Settings" },
];

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const user = useUser();
  const isAuthenticated = useIsAuthenticated();
  const hasHydrated = useHasHydrated();
  const { logout } = useAuthStore();
  // Controls whether the desktop sidebar is collapsed to icon-only mode
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  // Controls whether the mobile slide-out menu is visible
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Auth guard: redirect unauthenticated users to login, non-admins to home
  useEffect(() => {
    if (!hasHydrated) return;

    if (!isAuthenticated) {
      router.push("/login");
      return;
    }
    if (user && user.role !== "admin") {
      router.push("/");
    }
  }, [hasHydrated, isAuthenticated, user, router]);

  // Show a loading spinner while the auth store is hydrating or if the user is not an admin
  if (!hasHydrated || !user || user.role !== "admin") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  // Calls the auth store logout action to clear tokens and user state
  const handleSignOut = async () => {
    await logout();
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile Header - fixed top bar visible only on small screens */}
      <div className="lg:hidden fixed top-0 left-0 right-0 h-14 glass-strong z-50 flex items-center justify-between px-4">
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-2 rounded-lg hover:bg-foreground/5 transition-colors"
        >
          <Menu className="h-5 w-5" />
        </button>
        <Link href="/admin" className="flex items-center gap-2">
          <Image src="/zoniq-logo.png" alt="ZONIQ" width={100} height={32} className="h-6 w-auto" />
          <span className="text-[10px] font-bold text-foreground-subtle uppercase tracking-widest">Admin</span>
        </Link>
        {/* Spacer to center the logo */}
        <div className="w-9" />
      </div>

      {/* Mobile Sidebar Overlay - semi-transparent backdrop that closes the menu on click */}
      {mobileMenuOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar - slides in on mobile, always visible on desktop (collapsible) */}
      <aside
        className={cn(
          "fixed top-0 left-0 h-full bg-background-soft border-r border-border/50 z-50 transition-all duration-300",
          sidebarCollapsed ? "w-[72px]" : "w-60",
          mobileMenuOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        <div className="flex flex-col h-full">
          {/* Logo area with collapse toggle */}
          <div className="h-14 flex items-center justify-between px-4 border-b border-border/50">
            {!sidebarCollapsed && (
              <Link href="/admin" className="flex items-center gap-2">
                <Image src="/zoniq-logo.png" alt="ZONIQ" width={100} height={32} className="h-6 w-auto" />
                <span className="text-[10px] font-bold text-foreground-subtle uppercase tracking-widest">Admin</span>
              </Link>
            )}
            {/* Collapse/expand toggle button, visible only on desktop */}
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="hidden lg:flex p-1.5 rounded-lg hover:bg-foreground/5 transition-colors"
            >
              <ChevronLeft
                className={cn(
                  "h-4 w-4 text-foreground-subtle transition-transform duration-300",
                  sidebarCollapsed && "rotate-180"
                )}
              />
            </button>
          </div>

          {/* Navigation links - active item is determined by matching the current pathname */}
          <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
            {navItems.map((item) => {
              const isActive = pathname === item.href ||
                (item.href !== "/admin" && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                    isActive
                      ? "bg-primary text-white shadow-glow-sm"
                      : "text-foreground-muted hover:text-foreground hover:bg-foreground/5"
                  )}
                >
                  <item.icon className={cn("h-[18px] w-[18px] flex-shrink-0", isActive && "drop-shadow-sm")} />
                  {!sidebarCollapsed && <span>{item.label}</span>}
                </Link>
              );
            })}
          </nav>

          {/* User Info & Logout section at the bottom of the sidebar */}
          <div className="p-3 border-t border-border/50">
            {!sidebarCollapsed && (
              <div className="mb-2 px-3 py-2">
                <p className="text-sm font-semibold text-foreground truncate">
                  {user.fullName || user.username}
                </p>
                <p className="text-[11px] text-foreground-subtle truncate">
                  {user.email}
                </p>
              </div>
            )}
            <button
              onClick={handleSignOut}
              className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm text-foreground-subtle hover:bg-error/5 hover:text-error transition-all duration-200"
            >
              <LogOut className="h-[18px] w-[18px] flex-shrink-0" />
              {!sidebarCollapsed && <span>Sign Out</span>}
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content area - adjusts left padding based on sidebar collapse state */}
      <main
        className={cn(
          "min-h-screen pt-14 lg:pt-0 transition-all duration-300",
          sidebarCollapsed ? "lg:pl-[72px]" : "lg:pl-60"
        )}
      >
        <div className="p-4 lg:p-8">{children}</div>
      </main>
    </div>
  );
}
