"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  Calendar,
  Shield,
  Zap,
  Users,
  Ticket,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { EventCard, EventCardSkeleton } from "@/components/events/event-card";
import { eventsApi } from "@/lib/api";
import { useIsAdmin, useIsAuthenticated } from "@/store/auth";
import type { Event } from "@/types";

const features = [
  {
    icon: Shield,
    title: "Fair Access",
    description:
      "Queue-based ticketing ensures everyone gets a fair chance at securing tickets.",
  },
  {
    icon: Zap,
    title: "Instant Booking",
    description:
      "Secure your seats in seconds with our lightning-fast booking system.",
  },
  {
    icon: Users,
    title: "Real Fans",
    description:
      "Verification systems to prevent scalpers and bots from buying tickets.",
  },
  {
    icon: Ticket,
    title: "Digital Tickets",
    description:
      "Secure digital tickets with QR codes for seamless entry at events.",
  },
];

const categories = [
  { value: "concert", label: "Concerts", emoji: "🎵" },
  { value: "sports", label: "Sports", emoji: "⚽" },
  { value: "theater", label: "Theater", emoji: "🎭" },
  { value: "comedy", label: "Comedy", emoji: "😂" },
  { value: "festival", label: "Festivals", emoji: "🎪" },
  { value: "conference", label: "Conferences", emoji: "💼" },
];

export default function HomePage() {
  const router = useRouter();
  const isAuthenticated = useIsAuthenticated();
  const isAdmin = useIsAdmin();
  const [upcomingEvents, setUpcomingEvents] = useState<Event[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Redirect admin users to admin dashboard
  useEffect(() => {
    if (isAuthenticated && isAdmin) {
      router.replace("/admin");
    }
  }, [isAuthenticated, isAdmin, router]);

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const events = await eventsApi.getUpcoming(6);
        setUpcomingEvents(events);
      } catch (error) {
        console.error("Failed to fetch events:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchEvents();
  }, []);

  // Don't render homepage for admin users - show loading while redirecting
  if (isAuthenticated && isAdmin) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-foreground-muted">Redirecting to Admin Dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col">
      {/* Hero Section */}
      <section className="relative overflow-hidden py-24 md:py-36 lg:py-44">
        {/* Atmospheric background */}
        <div className="absolute inset-0 pointer-events-none">
          {/* Primary glow — top center */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-primary/[0.06] rounded-full blur-[140px] -translate-y-1/2" />
          {/* Accent glow — bottom right */}
          <div className="absolute bottom-0 right-0 w-[500px] h-[400px] bg-accent/[0.04] rounded-full blur-[120px] translate-y-1/3 translate-x-1/4" />
          {/* Grid lines */}
          <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.015)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.015)_1px,transparent_1px)] bg-[size:64px_64px] [mask-image:radial-gradient(ellipse_at_center,black_30%,transparent_70%)]" />
        </div>

        <div className="container mx-auto px-4 relative">
          <div className="max-w-4xl mx-auto text-center">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-semibold uppercase tracking-wider mb-8 animate-fade-up opacity-0">
              <Sparkles className="h-3.5 w-3.5" />
              <span>India&apos;s Most Trusted Ticketing Platform</span>
            </div>

            {/* Headline */}
            <h1 className="text-5xl md:text-7xl lg:text-8xl font-bold tracking-tight leading-[0.9] mb-8 animate-fade-up opacity-0 stagger-1">
              <span className="block text-foreground">Fair Access.</span>
              <span className="block text-foreground mt-1">Real Fans.</span>
              <span className="block gradient-text mt-1">Better Events.</span>
            </h1>

            {/* Subtext */}
            <p className="text-lg md:text-xl text-foreground-muted max-w-xl mx-auto mb-10 leading-relaxed animate-fade-up opacity-0 stagger-3">
              Experience the future of event ticketing. No bots, no scalpers,
              just fair access to the events you love.
            </p>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-fade-up opacity-0 stagger-4">
              <Link href="/events">
                <Button size="xl" rightIcon={<ArrowRight className="h-5 w-5" />}>
                  Explore Events
                </Button>
              </Link>
              <Link href="/about">
                <Button variant="outline" size="xl">
                  Learn More
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Categories Section */}
      <section className="py-20 relative">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4 tracking-tight">
              Browse by Category
            </h2>
            <p className="text-foreground-muted max-w-md mx-auto">
              Find events that match your interests
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {categories.map((category, i) => (
              <Link
                key={category.value}
                href={`/events?category=${category.value}`}
                className="group relative p-6 rounded-xl bg-background-card border border-border hover:border-primary/30 transition-all duration-400 text-center gradient-border"
                style={{ animationDelay: `${i * 0.05}s` }}
              >
                <div className="text-4xl mb-3 transition-transform duration-300 group-hover:scale-110 group-hover:-translate-y-1">
                  {category.emoji}
                </div>
                <div className="font-semibold text-sm text-foreground-muted group-hover:text-foreground transition-colors duration-300">
                  {category.label}
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Upcoming Events Section */}
      <section className="py-20 relative">
        {/* Subtle divider glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-64 h-px bg-gradient-to-r from-transparent via-border-hover to-transparent" />

        <div className="container mx-auto px-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-end justify-between gap-4 mb-12">
            <div>
              <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-2 tracking-tight">
                Upcoming Events
              </h2>
              <p className="text-foreground-muted">
                Don&apos;t miss out on these exciting events
              </p>
            </div>
            <Link href="/events">
              <Button variant="outline" rightIcon={<ArrowRight className="h-4 w-4" />}>
                View All
              </Button>
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {isLoading
              ? Array.from({ length: 6 }).map((_, i) => (
                  <EventCardSkeleton key={i} />
                ))
              : upcomingEvents.map((event) => (
                  <EventCard key={event.id} event={event} />
                ))}
          </div>

          {!isLoading && upcomingEvents.length === 0 && (
            <div className="text-center py-16">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-foreground/5 mb-6">
                <Calendar className="h-7 w-7 text-foreground-subtle" />
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">
                No upcoming events
              </h3>
              <p className="text-foreground-muted text-sm">
                Check back later for new events
              </p>
            </div>
          )}
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 relative">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-64 h-px bg-gradient-to-r from-transparent via-border-hover to-transparent" />

        <div className="container mx-auto px-4">
          <div className="text-center mb-14">
            <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4 tracking-tight">
              Why Choose ZONIQ?
            </h2>
            <p className="text-foreground-muted max-w-lg mx-auto">
              We&apos;re building the most fair and transparent ticketing platform in
              India
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            {features.map((feature, i) => (
              <div
                key={feature.title}
                className="group p-6 rounded-xl bg-background-card border border-border hover:border-border-hover transition-all duration-400 gradient-border"
                style={{ animationDelay: `${i * 0.1}s` }}
              >
                <div className="h-11 w-11 rounded-xl bg-primary/10 flex items-center justify-center mb-5 group-hover:bg-primary/15 transition-colors duration-300">
                  <feature.icon className="h-5 w-5 text-primary" />
                </div>
                <h3 className="text-base font-semibold text-foreground mb-2">
                  {feature.title}
                </h3>
                <p className="text-sm text-foreground-muted leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24">
        <div className="container mx-auto px-4">
          <div className="relative overflow-hidden rounded-2xl p-10 md:p-16 text-center">
            {/* Gradient background */}
            <div className="absolute inset-0 bg-gradient-to-br from-primary via-primary-hover to-primary" />
            {/* Atmospheric overlay */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(255,255,255,0.12),transparent_50%)]" />
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_80%,rgba(0,0,0,0.2),transparent_50%)]" />

            <div className="relative z-10">
              <h2 className="text-3xl md:text-5xl font-bold text-white mb-5 tracking-tight">
                Ready to Experience<br className="hidden md:block" /> Fair Ticketing?
              </h2>
              <p className="text-white/70 max-w-lg mx-auto mb-10 text-lg">
                Join thousands of fans who trust ZONIQ for their event tickets.
                Sign up today and never miss an event again.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <Link href="/signup">
                  <Button
                    size="lg"
                    className="bg-white text-primary hover:bg-white/90 border-0 shadow-lg"
                  >
                    Get Started Free
                  </Button>
                </Link>
                <Link href="/events">
                  <Button
                    size="lg"
                    className="bg-transparent border border-white/30 text-white hover:bg-white/10"
                  >
                    Browse Events
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
