"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import {
  Ticket,
  Calendar,
  MapPin,
  Clock,
  ChevronRight,
  Download,
  Eye,
  AlertCircle,
  CheckCircle2,
  XCircle,
  RefreshCw,
} from "lucide-react";
import { Button, Card, CardContent, Badge } from "@/components/ui";
import { useIsAuthenticated } from "@/store/auth";
import { bookingsApi } from "@/lib/api";
import { formatDate, formatTime, formatPrice } from "@/lib/utils";
import type { Booking, BookingStatus } from "@/types";

const STATUS_CONFIG: Record<
  string,
  { label: string; variant: "default" | "success" | "warning" | "error" }
> = {
  pending: { label: "Pending", variant: "warning" },
  confirmed: { label: "Confirmed", variant: "success" },
  cancelled: { label: "Cancelled", variant: "error" },
  refunded: { label: "Refunded", variant: "default" },
  failed: { label: "Failed", variant: "error" },
};

const DEFAULT_STATUS = { label: "Unknown", variant: "default" as const };

function BookingCard({ booking }: { booking: Booking }) {
  const router = useRouter();
  const status = STATUS_CONFIG[booking.status] || DEFAULT_STATUS;
  const eventDate = booking.event ? new Date(booking.event.eventDate) : new Date();
  const isPastEvent = eventDate < new Date();

  return (
    <Card className="overflow-hidden hover:border-border-hover transition-colors">
      <CardContent className="p-0">
        <div className="flex flex-col sm:flex-row">
          {/* Event Image */}
          <div className="relative w-full sm:w-48 h-32 sm:h-auto flex-shrink-0">
            {(booking.event?.thumbnailImageUrl || booking.event?.bannerImageUrl) ? (
              <Image
                src={booking.event?.thumbnailImageUrl || booking.event?.bannerImageUrl || ""}
                alt={booking.event?.title || "Event"}
                fill
                className="object-cover"
              />
            ) : (
              <div className="w-full h-full bg-background-elevated flex items-center justify-center">
                <Ticket className="h-8 w-8 text-foreground-muted" />
              </div>
            )}
            {isPastEvent && booking.status === "confirmed" && (
              <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                <span className="text-white text-sm font-medium">Event Ended</span>
              </div>
            )}
          </div>

          {/* Booking Details */}
          <div className="flex-1 p-4">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant={status.variant}>{status.label}</Badge>
                  <span className="text-xs text-foreground-muted">
                    #{booking.bookingNumber}
                  </span>
                </div>
                <Link
                  href={`/events/${booking.event?.slug || ''}`}
                  className="text-lg font-semibold text-foreground hover:text-primary transition-colors line-clamp-1"
                >
                  {booking.event?.title || "Event"}
                </Link>
              </div>
              <div className="text-right flex-shrink-0">
                <p className="text-lg font-bold text-primary">
                  {formatPrice(parseFloat(booking.totalAmount))}
                </p>
                <p className="text-xs text-foreground-muted">
                  {booking.ticketCount} {booking.ticketCount === 1 ? "ticket" : "tickets"}
                </p>
              </div>
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-foreground-muted">
              {booking.event && (
                <>
                  <div className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    <span>{formatDate(booking.event.eventDate)}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    <span>{formatTime(booking.event.eventDate)}</span>
                  </div>
                  {booking.event.venueName && (
                    <div className="flex items-center gap-1">
                      <MapPin className="h-4 w-4" />
                      <span>
                        {booking.event.venueName}
                        {booking.event.venueCity && `, ${booking.event.venueCity}`}
                      </span>
                    </div>
                  )}
                </>
              )}
            </div>

            {/* Actions */}
            <div className="mt-4 flex items-center gap-2">
              {booking.status === "confirmed" && !isPastEvent && (
                <>
                  <Button
                    size="sm"
                    variant="outline"
                    leftIcon={<Eye className="h-4 w-4" />}
                    onClick={() => router.push(`/my-tickets/${booking.id}`)}
                  >
                    View Tickets
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    leftIcon={<Download className="h-4 w-4" />}
                  >
                    Download
                  </Button>
                </>
              )}
              <Button
                size="sm"
                variant="ghost"
                className="ml-auto"
                rightIcon={<ChevronRight className="h-4 w-4" />}
                onClick={() => router.push(`/my-tickets/${booking.id}`)}
              >
                Details
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function BookingCardSkeleton() {
  return (
    <Card className="overflow-hidden">
      <CardContent className="p-0">
        <div className="flex flex-col sm:flex-row">
          <div className="w-full sm:w-48 h-32 bg-background-elevated animate-pulse" />
          <div className="flex-1 p-4">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="h-5 w-24 bg-background-elevated rounded animate-pulse mb-2" />
                <div className="h-6 w-48 bg-background-elevated rounded animate-pulse" />
              </div>
              <div className="h-6 w-20 bg-background-elevated rounded animate-pulse" />
            </div>
            <div className="mt-3 flex gap-4">
              <div className="h-4 w-32 bg-background-elevated rounded animate-pulse" />
              <div className="h-4 w-24 bg-background-elevated rounded animate-pulse" />
            </div>
            <div className="mt-4 flex gap-2">
              <div className="h-8 w-28 bg-background-elevated rounded animate-pulse" />
              <div className="h-8 w-24 bg-background-elevated rounded animate-pulse" />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function EmptyState() {
  return (
    <div className="text-center py-12">
      <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-background-elevated mb-4">
        <Ticket className="h-8 w-8 text-foreground-muted" />
      </div>
      <h3 className="text-lg font-semibold text-foreground mb-2">No tickets yet</h3>
      <p className="text-foreground-muted mb-6 max-w-md mx-auto">
        You haven&apos;t booked any tickets yet. Browse our events and book your first ticket!
      </p>
      <Button onClick={() => (window.location.href = "/events")}>
        Browse Events
      </Button>
    </div>
  );
}

type TabType = "all" | "upcoming" | "past";

export default function MyTicketsPage() {
  const router = useRouter();
  const isAuthenticated = useIsAuthenticated();

  const [bookings, setBookings] = useState<Booking[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>("upcoming");

  const fetchBookings = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await bookingsApi.list(1, 50);
      setBookings(response.bookings);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load bookings");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login?redirect=/my-tickets");
      return;
    }
    fetchBookings();
  }, [isAuthenticated, router, fetchBookings]);

  const now = new Date();
  const filteredBookings = bookings.filter((booking) => {
    const eventDate = booking.event ? new Date(booking.event.eventDate) : new Date();
    if (activeTab === "upcoming") {
      return eventDate >= now && booking.status !== "cancelled";
    }
    if (activeTab === "past") {
      return eventDate < now || booking.status === "cancelled";
    }
    return true;
  });

  const upcomingCount = bookings.filter(
    (b) => (b.event ? new Date(b.event.eventDate) >= now : false) && b.status !== "cancelled"
  ).length;
  const pastCount = bookings.filter(
    (b) => (b.event ? new Date(b.event.eventDate) < now : true) || b.status === "cancelled"
  ).length;

  const tabs: { id: TabType; label: string; count: number }[] = [
    { id: "upcoming", label: "Upcoming", count: upcomingCount },
    { id: "past", label: "Past", count: pastCount },
    { id: "all", label: "All", count: bookings.length },
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-foreground">My Tickets</h1>
            <p className="text-foreground-muted mt-1">
              View and manage your event bookings
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchBookings}
            leftIcon={<RefreshCw className="h-4 w-4" />}
          >
            Refresh
          </Button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 p-1 bg-background-soft rounded-lg mb-6">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === tab.id
                  ? "bg-background-card text-foreground shadow-sm"
                  : "text-foreground-muted hover:text-foreground"
                }`}
            >
              {tab.label}
              {tab.count > 0 && (
                <span
                  className={`ml-2 px-1.5 py-0.5 rounded-full text-xs ${activeTab === tab.id
                      ? "bg-primary/20 text-primary"
                      : "bg-background-elevated text-foreground-muted"
                    }`}
                >
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Error State */}
        {error && (
          <div className="mb-6 p-4 rounded-lg bg-error/10 text-error flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            {error}
            <Button
              variant="ghost"
              size="sm"
              className="ml-auto"
              onClick={fetchBookings}
            >
              Retry
            </Button>
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="space-y-4">
            <BookingCardSkeleton />
            <BookingCardSkeleton />
            <BookingCardSkeleton />
          </div>
        )}

        {/* Bookings List */}
        {!isLoading && !error && (
          <>
            {filteredBookings.length === 0 ? (
              <EmptyState />
            ) : (
              <div className="space-y-4">
                {filteredBookings.map((booking) => (
                  <BookingCard key={booking.id} booking={booking} />
                ))}
              </div>
            )}
          </>
        )}

        {/* Status Legend */}
        {!isLoading && bookings.length > 0 && (
          <div className="mt-8 p-4 bg-background-soft rounded-lg">
            <h4 className="text-sm font-medium text-foreground mb-3">Booking Status</h4>
            <div className="flex flex-wrap gap-4 text-sm">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-success" />
                <span className="text-foreground-muted">Confirmed - Ready to use</span>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-warning" />
                <span className="text-foreground-muted">Pending - Awaiting payment</span>
              </div>
              <div className="flex items-center gap-2">
                <XCircle className="h-4 w-4 text-error" />
                <span className="text-foreground-muted">Cancelled - No longer valid</span>
              </div>
              <div className="flex items-center gap-2">
                <RefreshCw className="h-4 w-4 text-foreground-muted" />
                <span className="text-foreground-muted">Refunded - Amount returned</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
