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
  Star,
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
      <section className="relative overflow-hidden py-20 md:py-32">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-b from-primary/10 via-transparent to-transparent" />

        <div className="container mx-auto px-4 relative">
          <div className="max-w-4xl mx-auto text-center space-y-8">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-light text-primary text-sm font-medium">
              <Star className="h-4 w-4" />
              <span>India&apos;s Most Trusted Ticketing Platform</span>
            </div>

            <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold tracking-tight">
              <span className="text-foreground">Fair Access.</span>
              <br />
              <span className="text-foreground">Real Fans.</span>
              <br />
              <span className="gradient-text">Better Events.</span>
            </h1>

            <p className="text-lg md:text-xl text-foreground-muted max-w-2xl mx-auto">
              Experience the future of event ticketing. No bots, no scalpers,
              just fair access to the events you love.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
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
      <section className="py-16 bg-background-soft">
        <div className="container mx-auto px-4">
          <div className="text-center mb-10">
            <h2 className="text-2xl md:text-3xl font-bold text-foreground mb-4">
              Browse by Category
            </h2>
            <p className="text-foreground-muted">
              Find events that match your interests
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {categories.map((category) => (
              <Link
                key={category.value}
                href={`/events?category=${category.value}`}
                className="group p-6 rounded-xl bg-background-card border border-border hover:border-primary transition-all hover-lift text-center"
              >
                <div className="text-4xl mb-3">{category.emoji}</div>
                <div className="font-medium text-foreground group-hover:text-primary transition-colors">
                  {category.label}
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Upcoming Events Section */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-10">
            <div>
              <h2 className="text-2xl md:text-3xl font-bold text-foreground mb-2">
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
            <div className="text-center py-12">
              <Calendar className="h-12 w-12 text-foreground-muted mx-auto mb-4" />
              <h3 className="text-lg font-medium text-foreground mb-2">
                No upcoming events
              </h3>
              <p className="text-foreground-muted">
                Check back later for new events
              </p>
            </div>
          )}
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 bg-background-soft">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-bold text-foreground mb-4">
              Why Choose ZONIQ?
            </h2>
            <p className="text-foreground-muted max-w-2xl mx-auto">
              We&apos;re building the most fair and transparent ticketing platform in
              India
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="p-6 rounded-xl bg-background-card border border-border hover:border-primary transition-colors"
              >
                <div className="h-12 w-12 rounded-lg bg-primary-light flex items-center justify-center mb-4">
                  <feature.icon className="h-6 w-6 text-primary" />
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">
                  {feature.title}
                </h3>
                <p className="text-sm text-foreground-muted">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-primary to-[#FF6B6B] p-8 md:p-12 text-center">
            <div className="relative z-10">
              <h2 className="text-2xl md:text-4xl font-bold text-white mb-4">
                Ready to Experience Fair Ticketing?
              </h2>
              <p className="text-white/80 max-w-xl mx-auto mb-8">
                Join thousands of fans who trust ZONIQ for their event tickets.
                Sign up today and never miss an event again.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <Link href="/signup">
                  <Button
                    size="lg"
                    className="bg-white text-primary hover:bg-white/90 border-0"
                  >
                    Get Started Free
                  </Button>
                </Link>
                <Link href="/events">
                  <Button
                    size="lg"
                    className="bg-transparent border-2 border-white text-white hover:bg-white/10"
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
