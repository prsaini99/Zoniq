"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
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
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    // Wait for hydration before checking auth
    if (!hasHydrated) return;

    if (!isAuthenticated) {
      router.push("/login");
      return;
    }
    if (user && user.role !== "admin") {
      router.push("/");
    }
  }, [hasHydrated, isAuthenticated, user, router]);

  // Show loading while hydrating or if not authenticated
  if (!hasHydrated || !user || user.role !== "admin") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  const handleSignOut = async () => {
    await logout();
  };

  return (
    <div className="min-h-screen bg-background-soft">
      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 h-16 bg-background border-b border-border z-50 flex items-center justify-between px-4">
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-2 rounded-lg hover:bg-background-elevated"
        >
          <Menu className="h-6 w-6" />
        </button>
        <span className="text-lg font-bold text-primary">ZONIQ Admin</span>
        <div className="w-10" />
      </div>

      {/* Mobile Sidebar Overlay */}
      {mobileMenuOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 h-full bg-background border-r border-border z-50 transition-all duration-300 ${
          sidebarCollapsed ? "w-20" : "w-64"
        } ${mobileMenuOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="h-16 flex items-center justify-between px-4 border-b border-border">
            {!sidebarCollapsed && (
              <Link href="/admin" className="text-xl font-bold text-primary">
                ZONIQ Admin
              </Link>
            )}
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="hidden lg:flex p-2 rounded-lg hover:bg-background-elevated"
            >
              <ChevronLeft
                className={`h-5 w-5 transition-transform ${
                  sidebarCollapsed ? "rotate-180" : ""
                }`}
              />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
            {navItems.map((item) => {
              const isActive = pathname === item.href ||
                (item.href !== "/admin" && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                    isActive
                      ? "bg-primary text-white"
                      : "text-foreground-muted hover:bg-background-elevated hover:text-foreground"
                  }`}
                >
                  <item.icon className="h-5 w-5 flex-shrink-0" />
                  {!sidebarCollapsed && <span>{item.label}</span>}
                </Link>
              );
            })}
          </nav>

          {/* User Info & Logout */}
          <div className="p-4 border-t border-border">
            {!sidebarCollapsed && (
              <div className="mb-3 px-3">
                <p className="text-sm font-medium text-foreground truncate">
                  {user.fullName || user.username}
                </p>
                <p className="text-xs text-foreground-muted truncate">
                  {user.email}
                </p>
              </div>
            )}
            <button
              onClick={handleSignOut}
              className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-foreground-muted hover:bg-error/10 hover:text-error transition-colors"
            >
              <LogOut className="h-5 w-5 flex-shrink-0" />
              {!sidebarCollapsed && <span>Sign Out</span>}
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main
        className={`min-h-screen pt-16 lg:pt-0 transition-all duration-300 ${
          sidebarCollapsed ? "lg:pl-20" : "lg:pl-64"
        }`}
      >
        <div className="p-4 lg:p-8">{children}</div>
      </main>
    </div>
  );
}
