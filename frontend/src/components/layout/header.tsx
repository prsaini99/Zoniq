"use client";

import Link from "next/link";
import Image from "next/image";
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
    <header className="sticky top-0 z-50 w-full glass-strong">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        {/* Logo */}
        <Link href="/" className="flex items-center group">
          <Image src="/zoniq-logo.png" alt="ZONIQ" width={120} height={40} className="h-8 w-auto transition-transform duration-300 group-hover:scale-105" priority />
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-1">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "relative px-4 py-2 text-sm font-medium rounded-lg transition-all duration-300",
                pathname === link.href
                  ? "text-foreground"
                  : "text-foreground-muted hover:text-foreground"
              )}
            >
              {link.label}
              {pathname === link.href && (
                <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-4 h-0.5 bg-primary rounded-full" />
              )}
            </Link>
          ))}
        </nav>

        {/* Desktop Actions */}
        <div className="hidden md:flex items-center gap-3">
          {isAuthenticated ? (
            <>
              {/* Admin Quick Actions */}
              {isAdmin && (
                <Link
                  href="/admin"
                  className={cn(
                    "flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-sm font-semibold transition-all duration-300",
                    pathname.startsWith("/admin")
                      ? "bg-primary text-white shadow-glow-sm"
                      : "bg-primary/10 text-primary hover:bg-primary/20"
                  )}
                  title="Admin Dashboard"
                >
                  <LayoutDashboard className="h-4 w-4" />
                  <span className="hidden lg:inline">Admin</span>
                </Link>
              )}

              {/* Quick Action Icons */}
              <div className="flex items-center gap-0.5">
                <Link
                  href="/my-tickets"
                  className={cn(
                    "p-2.5 rounded-lg transition-all duration-300",
                    pathname === "/my-tickets"
                      ? "text-primary bg-primary/10"
                      : "text-foreground-subtle hover:text-foreground hover:bg-foreground/5"
                  )}
                  title="My Tickets"
                >
                  <Ticket className="h-[18px] w-[18px]" />
                </Link>
                <Link
                  href="/wishlist"
                  className={cn(
                    "p-2.5 rounded-lg transition-all duration-300",
                    pathname === "/wishlist"
                      ? "text-primary bg-primary/10"
                      : "text-foreground-subtle hover:text-foreground hover:bg-foreground/5"
                  )}
                  title="Wishlist"
                >
                  <Heart className="h-[18px] w-[18px]" />
                </Link>
              </div>

              {/* Divider */}
              <div className="h-6 w-px bg-border" />

              {/* Profile Dropdown */}
              <div className="relative">
                <button
                  onClick={() => setIsProfileOpen(!isProfileOpen)}
                  className={cn(
                    "flex items-center gap-2.5 rounded-xl px-2 py-1.5 text-sm font-medium transition-all duration-300",
                    isProfileOpen
                      ? "bg-foreground/5"
                      : "hover:bg-foreground/5"
                  )}
                >
                  <div className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-lg font-bold text-sm",
                    isAdmin
                      ? "bg-gradient-to-br from-amber-500 to-amber-600 text-white"
                      : "bg-gradient-to-br from-primary to-primary-hover text-white"
                  )}>
                    {user?.fullName?.[0]?.toUpperCase() ||
                      user?.username?.[0]?.toUpperCase() ||
                      "U"}
                  </div>
                  <div className="hidden lg:block text-left">
                    <p className="text-sm font-semibold text-foreground leading-tight">
                      {user?.fullName || user?.username}
                    </p>
                    {isAdmin ? (
                      <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider">
                        Admin
                      </span>
                    ) : (
                      <p className="text-[11px] text-foreground-muted leading-tight">Customer</p>
                    )}
                  </div>
                  <ChevronDown
                    className={cn(
                      "h-3.5 w-3.5 text-foreground-subtle transition-transform duration-300",
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
                    <div className="absolute right-0 top-full mt-2 w-64 rounded-xl border border-border bg-background-card py-1.5 shadow-card-hover z-20 animate-scale-in origin-top-right">
                      {/* User Info */}
                      <div className="px-4 py-3 border-b border-border">
                        <div className="flex items-center gap-3">
                          <div className={cn(
                            "flex h-10 w-10 items-center justify-center rounded-lg font-bold",
                            isAdmin
                              ? "bg-gradient-to-br from-amber-500 to-amber-600 text-white"
                              : "bg-gradient-to-br from-primary to-primary-hover text-white"
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
                                <span className="text-[9px] font-bold text-amber-400 bg-amber-400/10 px-1.5 py-0.5 rounded uppercase tracking-wider">
                                  Admin
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
                      <div className="py-1">
                        {[
                          { href: "/profile", icon: User, label: "My Profile" },
                          { href: "/my-tickets", icon: Ticket, label: "My Tickets" },
                          { href: "/wishlist", icon: Heart, label: "Wishlist" },
                          { href: "/settings", icon: Settings, label: "Settings" },
                        ].map((item) => (
                          <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                              "flex items-center gap-3 px-4 py-2.5 text-sm transition-all duration-200",
                              pathname === item.href
                                ? "text-primary bg-primary/5"
                                : "text-foreground-muted hover:text-foreground hover:bg-foreground/5"
                            )}
                            onClick={() => setIsProfileOpen(false)}
                          >
                            <item.icon className="h-4 w-4" />
                            {item.label}
                          </Link>
                        ))}
                      </div>

                      {/* Admin Section */}
                      {isAdmin && (
                        <div className="border-t border-border py-1">
                          <Link
                            href="/admin"
                            className="flex items-center gap-3 px-4 py-2.5 text-sm text-amber-400 hover:bg-amber-400/5 transition-all duration-200"
                            onClick={() => setIsProfileOpen(false)}
                          >
                            <LayoutDashboard className="h-4 w-4" />
                            Admin Dashboard
                          </Link>
                        </div>
                      )}

                      {/* Logout */}
                      <div className="border-t border-border py-1">
                        <button
                          onClick={handleLogout}
                          className="flex w-full items-center gap-3 px-4 py-2.5 text-sm text-error hover:bg-error/5 transition-all duration-200"
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
                <Button variant="ghost" className="text-foreground-muted">Sign In</Button>
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
          className="md:hidden p-2 rounded-lg text-foreground-muted hover:text-foreground hover:bg-foreground/5 transition-all duration-200"
        >
          {isMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile Menu */}
      {isMenuOpen && (
        <div className="md:hidden border-t border-border/50 bg-background-soft animate-fade-in">
          <nav className="container mx-auto px-4 py-4 space-y-1">
            {/* User Info (if authenticated) */}
            {isAuthenticated && (
              <div className={cn(
                "flex items-center gap-3 px-4 py-3 mb-3 rounded-xl",
                isAdmin
                  ? "bg-amber-400/5 border border-amber-400/10"
                  : "bg-foreground/5"
              )}>
                <div className={cn(
                  "flex h-10 w-10 items-center justify-center rounded-lg font-bold",
                  isAdmin
                    ? "bg-gradient-to-br from-amber-500 to-amber-600 text-white"
                    : "bg-gradient-to-br from-primary to-primary-hover text-white"
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
                      <span className="text-[9px] font-bold text-amber-400 bg-amber-400/10 px-1.5 py-0.5 rounded uppercase tracking-wider">
                        Admin
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
                  "flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200",
                  pathname === link.href
                    ? "text-primary bg-primary/5"
                    : "text-foreground-muted hover:text-foreground hover:bg-foreground/5"
                )}
              >
                {link.label}
              </Link>
            ))}

            {/* Authenticated User Menu */}
            {isAuthenticated && (
              <>
                <div className="my-3 border-t border-border/50" />
                {[
                  { href: "/profile", icon: User, label: "My Profile" },
                  { href: "/my-tickets", icon: Ticket, label: "My Tickets" },
                  { href: "/wishlist", icon: Heart, label: "Wishlist" },
                  { href: "/settings", icon: Settings, label: "Settings" },
                ].map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setIsMenuOpen(false)}
                    className={cn(
                      "flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200",
                      pathname === item.href
                        ? "text-primary bg-primary/5"
                        : "text-foreground-muted hover:text-foreground hover:bg-foreground/5"
                    )}
                  >
                    <item.icon className="h-4 w-4" />
                    {item.label}
                  </Link>
                ))}

                {isAdmin && (
                  <>
                    <div className="my-3 border-t border-border/50" />
                    <div className="px-4 py-2">
                      <p className="text-[10px] font-bold text-amber-400 uppercase tracking-widest">Admin</p>
                    </div>
                    <Link
                      href="/admin"
                      onClick={() => setIsMenuOpen(false)}
                      className="flex items-center gap-3 px-4 py-3 text-sm font-medium text-amber-400 bg-amber-400/5 hover:bg-amber-400/10 rounded-lg transition-all duration-200"
                    >
                      <LayoutDashboard className="h-4 w-4" />
                      Admin Dashboard
                    </Link>
                  </>
                )}

                <div className="my-3 border-t border-border/50" />
                <button
                  onClick={() => {
                    handleLogout();
                    setIsMenuOpen(false);
                  }}
                  className="flex w-full items-center gap-3 px-4 py-3 text-sm font-medium text-error hover:bg-error/5 rounded-lg transition-all duration-200"
                >
                  <LogOut className="h-4 w-4" />
                  Sign Out
                </button>
              </>
            )}

            {/* Guest User Menu */}
            {!isAuthenticated && (
              <div className="pt-4 border-t border-border/50 space-y-2">
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
