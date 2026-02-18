"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
  Menu,
  X,
  User,
  LogOut,
  Settings,
  LayoutDashboard,
  Ticket,
  Search,
  Heart,
  ChevronDown,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useAuthStore, useIsAuthenticated, useIsAdmin } from "@/store/auth";

const navLinks = [
  { href: "/events", label: "Events" },
  { href: "/about", label: "About" },
  { href: "/contact", label: "Contact" },
];

export function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const pathname = usePathname();
  const isAuthenticated = useIsAuthenticated();
  const isAdmin = useIsAdmin();
  const { user, logout } = useAuthStore();

  const handleLogout = async () => {
    await logout();
    setIsProfileOpen(false);
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-background/80 backdrop-blur-lg">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
            <span className="text-lg font-bold text-white">Z</span>
          </div>
          <span className="text-xl font-bold text-foreground">ZONIQ</span>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-1">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "px-4 py-2 text-sm font-medium rounded-lg transition-colors",
                pathname === link.href
                  ? "text-primary bg-primary-light"
                  : "text-foreground-muted hover:text-foreground hover:bg-background-soft"
              )}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        {/* Desktop Actions */}
        <div className="hidden md:flex items-center gap-2">
          {isAuthenticated ? (
            <>
              {/* Admin Quick Actions */}
              {isAdmin && (
                <div className="flex items-center gap-1 mr-2">
                  <Link
                    href="/admin"
                    className={cn(
                      "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors",
                      pathname.startsWith("/admin")
                        ? "bg-primary text-white"
                        : "bg-primary/10 text-primary hover:bg-primary/20"
                    )}
                    title="Admin Dashboard"
                  >
                    <LayoutDashboard className="h-4 w-4" />
                    <span className="hidden lg:inline">Admin</span>
                  </Link>
                </div>
              )}

              {/* Quick Action Icons */}
              <div className="flex items-center gap-1 mr-2">
                <Link
                  href="/my-tickets"
                  className={cn(
                    "p-2 rounded-lg transition-colors",
                    pathname === "/my-tickets"
                      ? "text-primary bg-primary-light"
                      : "text-foreground-muted hover:text-foreground hover:bg-background-soft"
                  )}
                  title="My Tickets"
                >
                  <Ticket className="h-5 w-5" />
                </Link>
                <Link
                  href="/wishlist"
                  className={cn(
                    "p-2 rounded-lg transition-colors",
                    pathname === "/wishlist"
                      ? "text-primary bg-primary-light"
                      : "text-foreground-muted hover:text-foreground hover:bg-background-soft"
                  )}
                  title="Wishlist"
                >
                  <Heart className="h-5 w-5" />
                </Link>
              </div>

              {/* Divider */}
              <div className="h-8 w-px bg-border" />

              {/* Profile Dropdown */}
              <div className="relative ml-2">
                <button
                  onClick={() => setIsProfileOpen(!isProfileOpen)}
                  className={cn(
                    "flex items-center gap-2 rounded-lg px-2 py-1.5 text-sm font-medium transition-colors",
                    isProfileOpen
                      ? "bg-background-soft text-foreground"
                      : "text-foreground-muted hover:text-foreground hover:bg-background-soft"
                  )}
                >
                  <div className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-full font-semibold",
                    isAdmin ? "bg-amber-500 text-white" : "bg-primary text-white"
                  )}>
                    {user?.fullName?.[0]?.toUpperCase() ||
                      user?.username?.[0]?.toUpperCase() ||
                      "U"}
                  </div>
                  <div className="hidden lg:block text-left">
                    <p className="text-sm font-medium text-foreground leading-tight">
                      {user?.fullName || user?.username}
                    </p>
                    {isAdmin ? (
                      <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-amber-600 bg-amber-100 px-1.5 py-0.5 rounded">
                        <LayoutDashboard className="h-2.5 w-2.5" />
                        ADMIN
                      </span>
                    ) : (
                      <p className="text-xs text-foreground-muted leading-tight">Customer</p>
                    )}
                  </div>
                  <ChevronDown
                    className={cn(
                      "h-4 w-4 transition-transform",
                      isProfileOpen && "rotate-180"
                    )}
                  />
                </button>

                {/* Dropdown Menu */}
                {isProfileOpen && (
                  <>
                    <div
                      className="fixed inset-0 z-10"
                      onClick={() => setIsProfileOpen(false)}
                    />
                    <div className="absolute right-0 top-full mt-2 w-64 rounded-xl border border-border bg-background-card py-2 shadow-xl z-20">
                      {/* User Info */}
                      <div className={cn(
                        "px-4 py-3 border-b border-border",
                        isAdmin && "bg-amber-50"
                      )}>
                        <div className="flex items-center gap-3">
                          <div className={cn(
                            "flex h-10 w-10 items-center justify-center rounded-full font-semibold",
                            isAdmin ? "bg-amber-500 text-white" : "bg-primary text-white"
                          )}>
                            {user?.fullName?.[0]?.toUpperCase() ||
                              user?.username?.[0]?.toUpperCase() ||
                              "U"}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <p className="text-sm font-semibold text-foreground truncate">
                                {user?.fullName || user?.username}
                              </p>
                              {isAdmin && (
                                <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-amber-600 bg-amber-100 px-1.5 py-0.5 rounded">
                                  ADMIN
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-foreground-muted truncate">
                              {user?.email}
                            </p>
                          </div>
                        </div>
                      </div>

                      {/* Menu Items */}
                      <div className="py-2">
                        <Link
                          href="/profile"
                          className={cn(
                            "flex items-center gap-3 px-4 py-2.5 text-sm transition-colors",
                            pathname === "/profile"
                              ? "text-primary bg-primary-light"
                              : "text-foreground-muted hover:text-foreground hover:bg-background-soft"
                          )}
                          onClick={() => setIsProfileOpen(false)}
                        >
                          <User className="h-4 w-4" />
                          My Profile
                        </Link>
                        <Link
                          href="/my-tickets"
                          className={cn(
                            "flex items-center gap-3 px-4 py-2.5 text-sm transition-colors",
                            pathname === "/my-tickets"
                              ? "text-primary bg-primary-light"
                              : "text-foreground-muted hover:text-foreground hover:bg-background-soft"
                          )}
                          onClick={() => setIsProfileOpen(false)}
                        >
                          <Ticket className="h-4 w-4" />
                          My Tickets
                        </Link>
                        <Link
                          href="/wishlist"
                          className={cn(
                            "flex items-center gap-3 px-4 py-2.5 text-sm transition-colors",
                            pathname === "/wishlist"
                              ? "text-primary bg-primary-light"
                              : "text-foreground-muted hover:text-foreground hover:bg-background-soft"
                          )}
                          onClick={() => setIsProfileOpen(false)}
                        >
                          <Heart className="h-4 w-4" />
                          Wishlist
                        </Link>
                        <Link
                          href="/settings"
                          className={cn(
                            "flex items-center gap-3 px-4 py-2.5 text-sm transition-colors",
                            pathname === "/settings"
                              ? "text-primary bg-primary-light"
                              : "text-foreground-muted hover:text-foreground hover:bg-background-soft"
                          )}
                          onClick={() => setIsProfileOpen(false)}
                        >
                          <Settings className="h-4 w-4" />
                          Settings
                        </Link>
                      </div>

                      {/* Admin Section */}
                      {isAdmin && (
                        <div className="border-t border-border py-2">
                          <Link
                            href="/admin"
                            className="flex items-center gap-3 px-4 py-2.5 text-sm text-primary hover:bg-primary-light transition-colors"
                            onClick={() => setIsProfileOpen(false)}
                          >
                            <LayoutDashboard className="h-4 w-4" />
                            Admin Dashboard
                          </Link>
                        </div>
                      )}

                      {/* Logout */}
                      <div className="border-t border-border py-2">
                        <button
                          onClick={handleLogout}
                          className="flex w-full items-center gap-3 px-4 py-2.5 text-sm text-error hover:bg-error/10 transition-colors"
                        >
                          <LogOut className="h-4 w-4" />
                          Sign Out
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </>
          ) : (
            <div className="flex items-center gap-2">
              <Link href="/login">
                <Button variant="ghost">Sign In</Button>
              </Link>
              <Link href="/signup">
                <Button>Get Started</Button>
              </Link>
            </div>
          )}
        </div>

        {/* Mobile Menu Button */}
        <button
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          className="md:hidden p-2 rounded-lg text-foreground-muted hover:text-foreground hover:bg-background-soft"
        >
          {isMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      {/* Mobile Menu */}
      {isMenuOpen && (
        <div className="md:hidden border-t border-border bg-background">
          <nav className="container mx-auto px-4 py-4 space-y-1">
            {/* User Info (if authenticated) */}
            {isAuthenticated && (
              <div className={cn(
                "flex items-center gap-3 px-4 py-3 mb-3 rounded-lg",
                isAdmin ? "bg-amber-50 border border-amber-200" : "bg-background-soft"
              )}>
                <div className={cn(
                  "flex h-10 w-10 items-center justify-center rounded-full font-semibold",
                  isAdmin ? "bg-amber-500 text-white" : "bg-primary text-white"
                )}>
                  {user?.fullName?.[0]?.toUpperCase() ||
                    user?.username?.[0]?.toUpperCase() ||
                    "U"}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-semibold text-foreground truncate">
                      {user?.fullName || user?.username}
                    </p>
                    {isAdmin && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-amber-600 bg-amber-100 px-1.5 py-0.5 rounded">
                        ADMIN
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-foreground-muted truncate">
                    {user?.email}
                  </p>
                </div>
              </div>
            )}

            {/* Navigation Links */}
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setIsMenuOpen(false)}
                className={cn(
                  "flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors",
                  pathname === link.href
                    ? "text-primary bg-primary-light"
                    : "text-foreground-muted hover:text-foreground hover:bg-background-soft"
                )}
              >
                {link.label}
              </Link>
            ))}

            {/* Authenticated User Menu */}
            {isAuthenticated && (
              <>
                <div className="my-3 border-t border-border" />
                <Link
                  href="/profile"
                  onClick={() => setIsMenuOpen(false)}
                  className={cn(
                    "flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors",
                    pathname === "/profile"
                      ? "text-primary bg-primary-light"
                      : "text-foreground-muted hover:text-foreground hover:bg-background-soft"
                  )}
                >
                  <User className="h-4 w-4" />
                  My Profile
                </Link>
                <Link
                  href="/my-tickets"
                  onClick={() => setIsMenuOpen(false)}
                  className={cn(
                    "flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors",
                    pathname === "/my-tickets"
                      ? "text-primary bg-primary-light"
                      : "text-foreground-muted hover:text-foreground hover:bg-background-soft"
                  )}
                >
                  <Ticket className="h-4 w-4" />
                  My Tickets
                </Link>
                <Link
                  href="/wishlist"
                  onClick={() => setIsMenuOpen(false)}
                  className={cn(
                    "flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors",
                    pathname === "/wishlist"
                      ? "text-primary bg-primary-light"
                      : "text-foreground-muted hover:text-foreground hover:bg-background-soft"
                  )}
                >
                  <Heart className="h-4 w-4" />
                  Wishlist
                </Link>
                <Link
                  href="/settings"
                  onClick={() => setIsMenuOpen(false)}
                  className={cn(
                    "flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors",
                    pathname === "/settings"
                      ? "text-primary bg-primary-light"
                      : "text-foreground-muted hover:text-foreground hover:bg-background-soft"
                  )}
                >
                  <Settings className="h-4 w-4" />
                  Settings
                </Link>

                {isAdmin && (
                  <>
                    <div className="my-3 border-t border-border" />
                    <div className="px-4 py-2">
                      <p className="text-xs font-semibold text-amber-600 uppercase tracking-wider mb-2">Admin Controls</p>
                    </div>
                    <Link
                      href="/admin"
                      onClick={() => setIsMenuOpen(false)}
                      className="flex items-center gap-3 px-4 py-3 text-sm font-medium text-amber-700 bg-amber-50 hover:bg-amber-100 rounded-lg transition-colors mx-2"
                    >
                      <LayoutDashboard className="h-4 w-4" />
                      Admin Dashboard
                    </Link>
                  </>
                )}

                <div className="my-3 border-t border-border" />
                <button
                  onClick={() => {
                    handleLogout();
                    setIsMenuOpen(false);
                  }}
                  className="flex w-full items-center gap-3 px-4 py-3 text-sm font-medium text-error hover:bg-error/10 rounded-lg transition-colors"
                >
                  <LogOut className="h-4 w-4" />
                  Sign Out
                </button>
              </>
            )}

            {/* Guest User Menu */}
            {!isAuthenticated && (
              <div className="pt-4 border-t border-border space-y-2">
                <Link href="/login" onClick={() => setIsMenuOpen(false)}>
                  <Button variant="outline" className="w-full">
                    Sign In
                  </Button>
                </Link>
                <Link href="/signup" onClick={() => setIsMenuOpen(false)}>
                  <Button className="w-full">Get Started</Button>
                </Link>
              </div>
            )}
          </nav>
        </div>
      )}
    </header>
  );
}
