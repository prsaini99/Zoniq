/*
 * Event detail page: displays comprehensive information about a single event
 * and provides the booking interface.
 *
 * Data fetched on mount (by slug):
 *   - Event details (title, description, date, venue, images, organizer, terms).
 *   - Seat categories (ticket types with prices and colors).
 *   - Seat availability map.
 *   - Queue status (if the event has a virtual queue enabled).
 *
 * Booking flow:
 *   - If the user is not authenticated, clicking "Book Now" redirects to /login.
 *   - If a virtual queue is enabled and the user did NOT arrive from the queue page,
 *     they are redirected to /queue/[eventId] to wait their turn.
 *   - If the user arrived from the queue (fromQueue=true) or there is no queue,
 *     the TicketSelectionModal opens for choosing ticket categories and quantities.
 *
 * Wrapped in Suspense because it reads searchParams via useSearchParams().
 */

"use client";

import { Suspense, useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import {
  Calendar,
  Clock,
  MapPin,
  Users,
  ArrowLeft,
  Share2,
  Ticket,
  Info,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge, StatusBadge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageSpinner } from "@/components/ui/spinner";
import { WishlistButton } from "@/components/wishlist";
import { TicketSelectionModal } from "@/components/TicketSelectionModal";
import { eventsApi, queueApi } from "@/lib/api";
import { formatDate, formatTime, formatPrice, cn } from "@/lib/utils";
import type { EventDetail, SeatCategory, EventSeatsResponse, QueueStatusResponse } from "@/types";
import { CATEGORY_LABELS } from "@/types";
import { useIsAuthenticated } from "@/store/auth";

function EventDetailContent() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  // Extract the event slug from the dynamic route segment
  const slug = params.slug as string;
  const isAuthenticated = useIsAuthenticated();
  // Check if the user arrived from the queue waiting room
  const fromQueue = searchParams.get("fromQueue") === "true";

  // Core data state
  const [event, setEvent] = useState<EventDetail | null>(null);
  const [categories, setCategories] = useState<SeatCategory[]>([]);
  const [seatsData, setSeatsData] = useState<EventSeatsResponse | null>(null);
  const [queueStatus, setQueueStatus] = useState<QueueStatusResponse | null>(null);

  // UI state
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isJoiningQueue, setIsJoiningQueue] = useState(false);
  const [isTicketModalOpen, setIsTicketModalOpen] = useState(false);
  // Prevents auto-opening the ticket modal more than once from a queue redirect
  const [hasOpenedFromQueue, setHasOpenedFromQueue] = useState(false);

  // Fetch event data, seat categories, seat map, and (optionally) queue status on mount
  useEffect(() => {
    const fetchEventData = async () => {
      try {
        setIsLoading(true);
        const eventData = await eventsApi.getByIdOrSlug(slug);
        setEvent(eventData);

        // Fetch categories, seats, and queue status
        const fetchPromises: Promise<any>[] = [
          eventsApi.getSeatCategories(eventData.id),
          eventsApi.getSeats(eventData.id),
        ];

        // Only fetch queue status if queue is enabled
        if (eventData.queueEnabled) {
          fetchPromises.push(queueApi.getStatus(eventData.id));
        }

        const results = await Promise.all(fetchPromises);
        setCategories(results[0]);
        setSeatsData(results[1]);
        if (eventData.queueEnabled && results[2]) {
          setQueueStatus(results[2]);
        }
      } catch (err) {
        console.error("Failed to fetch event:", err);
        setError("Event not found");
      } finally {
        setIsLoading(false);
      }
    };

    fetchEventData();
  }, [slug]);

  // Auto-open ticket modal if user came from queue and data is ready
  useEffect(() => {
    if (fromQueue && !isLoading && event && categories.length > 0 && !hasOpenedFromQueue) {
      setIsTicketModalOpen(true);
      setHasOpenedFromQueue(true);
    }
  }, [fromQueue, isLoading, event, categories, hasOpenedFromQueue]);

  // Handle "Book Now" / "Join Queue" button click
  const handleBookClick = () => {
    // Redirect unauthenticated users to login with a return URL
    if (!isAuthenticated) {
      router.push(`/login?redirect=/events/${slug}`);
      return;
    }

    // If queue is enabled and user did NOT come from queue, redirect to queue page
    if (event?.queueEnabled && !fromQueue) {
      setIsJoiningQueue(true);
      router.push(`/queue/${event.id}`);
      return;
    }

    // Open ticket selection modal
    setIsTicketModalOpen(true);
  };

  // Loading state
  if (isLoading) {
    return <PageSpinner />;
  }

  // Error / not found state
  if (error || !event) {
    return (
      <div className="container mx-auto px-4 py-16 text-center">
        <AlertCircle className="h-16 w-16 text-error mx-auto mb-4" />
        <h1 className="text-2xl font-bold text-foreground mb-2">
          Event Not Found
        </h1>
        <p className="text-foreground-muted mb-6">
          The event you&apos;re looking for doesn&apos;t exist or has been removed.
        </p>
        <Link href="/events">
          <Button>Browse Events</Button>
        </Link>
      </div>
    );
  }

  // Derived booking availability flags
  const isSoldOut = event.availableSeats === 0;
  const isBookingOpen = event.isBookingOpen;
  const canBook = isBookingOpen && !isSoldOut;

  // Calculate the price range across all active seat categories
  const lowestPrice = categories.length > 0
    ? Math.min(...categories.filter(c => c.isActive).map((c) => parseFloat(c.price)))
    : 0;
  const highestPrice = categories.length > 0
    ? Math.max(...categories.filter(c => c.isActive).map((c) => parseFloat(c.price)))
    : 0;

  return (
    <div className="min-h-screen">
      {/* Hero Banner: event image with gradient overlay */}
      <div className="relative h-[300px] md:h-[400px] bg-background-elevated">
        {event.bannerImageUrl ? (
          <Image
            src={event.bannerImageUrl}
            alt={event.title}
            fill
            className="object-cover"
            priority
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-primary/20 to-transparent">
            <span className="text-8xl font-bold text-foreground-subtle">
              {event.title[0]}
            </span>
          </div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-background via-transparent to-transparent" />

        {/* Back Button */}
        <div className="absolute top-4 left-4">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => router.back()}
            leftIcon={<ArrowLeft className="h-4 w-4" />}
            className="glass"
          >
            Back
          </Button>
        </div>

        {/* Action Buttons: share and wishlist */}
        <div className="absolute top-4 right-4 flex gap-2">
          <Button variant="secondary" size="icon" className="glass">
            <Share2 className="h-4 w-4" />
          </Button>
          <WishlistButton
            event={event}
            size="md"
            className="glass"
          />
        </div>
      </div>

      <div className="container mx-auto px-4 -mt-20 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content (left 2/3) */}
          <div className="lg:col-span-2 space-y-6">
            {/* Event Header: category badge, status, title, short description, date/time/venue */}
            <Card>
              <CardContent className="p-6">
                <div className="flex flex-wrap items-center gap-2 mb-4">
                  <Badge>
                    {CATEGORY_LABELS[event.category] || event.category}
                  </Badge>
                  <StatusBadge status={event.status} />
                  {isSoldOut && <Badge variant="error">Sold Out</Badge>}
                </div>

                <h1 className="text-2xl md:text-3xl font-bold text-foreground mb-4">
                  {event.title}
                </h1>

                {event.shortDescription && (
                  <p className="text-foreground-muted mb-6">
                    {event.shortDescription}
                  </p>
                )}

                {/* Event Details: date, time, and venue */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="flex items-center gap-3 text-foreground-muted">
                    <div className="h-10 w-10 rounded-lg bg-primary-light flex items-center justify-center">
                      <Calendar className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <div className="text-sm text-foreground-subtle">
                        Date
                      </div>
                      <div className="font-medium text-foreground">
                        {formatDate(event.eventDate)}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 text-foreground-muted">
                    <div className="h-10 w-10 rounded-lg bg-primary-light flex items-center justify-center">
                      <Clock className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <div className="text-sm text-foreground-subtle">
                        Time
                      </div>
                      <div className="font-medium text-foreground">
                        {formatTime(event.eventDate)}
                      </div>
                    </div>
                  </div>

                  {event.venue && (
                    <div className="flex items-center gap-3 text-foreground-muted md:col-span-2">
                      <div className="h-10 w-10 rounded-lg bg-primary-light flex items-center justify-center">
                        <MapPin className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <div className="text-sm text-foreground-subtle">
                          Venue
                        </div>
                        <div className="font-medium text-foreground">
                          {event.venue.name}
                          {event.venue.city && `, ${event.venue.city}`}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Full event description */}
            {event.description && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Info className="h-5 w-5 text-primary" />
                    About This Event
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="prose prose-invert max-w-none text-foreground-muted">
                    {event.description}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Terms & Conditions (if provided by the event organizer) */}
            {event.termsAndConditions && (
              <Card>
                <CardHeader>
                  <CardTitle>Terms & Conditions</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-sm text-foreground-muted whitespace-pre-wrap">
                    {event.termsAndConditions}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Organizer Info */}
            {event.organizerName && (
              <Card>
                <CardContent className="p-6">
                  <div className="text-sm text-foreground-muted mb-1">
                    Organized by
                  </div>
                  <div className="font-medium text-foreground text-lg">
                    {event.organizerName}
                  </div>
                  {event.organizerContact && (
                    <div className="text-sm text-foreground-muted mt-1">
                      {event.organizerContact}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>

          {/* Sidebar - Booking card (right 1/3, sticky) */}
          <div className="space-y-6">
            <Card className="sticky top-24">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Ticket className="h-5 w-5 text-primary" />
                  Book Tickets
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Price Range display */}
                <div>
                  <div className="text-sm text-foreground-muted mb-1">
                    {lowestPrice === highestPrice ? "Price" : "Starting from"}
                  </div>
                  <div className="text-3xl font-bold text-foreground">
                    {lowestPrice > 0 ? formatPrice(lowestPrice) : "Free"}
                  </div>
                  {lowestPrice !== highestPrice && lowestPrice > 0 && (
                    <div className="text-sm text-foreground-muted mt-1">
                      up to {formatPrice(highestPrice)}
                    </div>
                  )}
                </div>

                {/* Ticket Categories Preview: color-coded chips for each active category */}
                {categories.length > 0 && (
                  <div className="space-y-2">
                    <div className="text-sm font-medium text-foreground">
                      {categories.filter(c => c.isActive).length} ticket {categories.filter(c => c.isActive).length === 1 ? "type" : "types"} available
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {categories.filter(c => c.isActive).map((category) => (
                        <div
                          key={category.id}
                          className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-background-soft text-xs"
                        >
                          <div
                            className="h-2 w-2 rounded-full"
                            style={{ backgroundColor: category.colorCode || "#3B82F6" }}
                          />
                          <span className="text-foreground-muted">{category.name}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Seat Availability: available vs total seats */}
                <div className="flex items-center justify-between py-3 border-t border-border">
                  <div className="flex items-center gap-2 text-sm text-foreground-muted">
                    <Users className="h-4 w-4" />
                    <span>Available Seats</span>
                  </div>
                  <span className="font-medium text-foreground">
                    {event.availableSeats} / {event.totalSeats}
                  </span>
                </div>

                {/* Booking Window: shows when booking opens and closes */}
                <div className="text-xs text-foreground-muted space-y-1">
                  <div>
                    Booking opens: {formatDate(event.bookingStartDate)} at{" "}
                    {formatTime(event.bookingStartDate)}
                  </div>
                  <div>
                    Booking closes: {formatDate(event.bookingEndDate)} at{" "}
                    {formatTime(event.bookingEndDate)}
                  </div>
                </div>

                {/* Queue Info card (shown only if virtual queue is enabled) */}
                {event.queueEnabled && queueStatus && (
                  <div className="rounded-lg bg-primary/5 border border-primary/20 p-4 space-y-2">
                    <div className="flex items-center gap-2 text-sm font-medium text-primary">
                      <Users className="h-4 w-4" />
                      Virtual Queue Active
                    </div>
                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div>
                        <span className="text-foreground-muted">In Queue:</span>{" "}
                        <span className="font-medium text-foreground">{queueStatus.totalInQueue}</span>
                      </div>
                      <div>
                        <span className="text-foreground-muted">Est. Wait:</span>{" "}
                        <span className="font-medium text-foreground">
                          {queueStatus.estimatedWaitMinutes
                            ? `~${queueStatus.estimatedWaitMinutes} min`
                            : "No wait"}
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Book / Join Queue button: label changes based on event state */}
                <Button
                  className="w-full"
                  size="lg"
                  disabled={!canBook || isJoiningQueue}
                  onClick={handleBookClick}
                  rightIcon={<ArrowLeft className="h-4 w-4 rotate-180" />}
                >
                  {isJoiningQueue
                    ? "Joining Queue..."
                    : isSoldOut
                    ? "Sold Out"
                    : !isBookingOpen
                    ? "Booking Not Open"
                    : event.queueEnabled
                    ? "Join Queue"
                    : "Book Now"}
                </Button>

                {/* Max tickets per booking info */}
                <div className="text-xs text-foreground-subtle text-center">
                  Max {event.maxTicketsPerBooking} tickets per booking
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Ticket Selection Modal: opened when user clicks "Book Now" or arrives from queue */}
      <TicketSelectionModal
        isOpen={isTicketModalOpen}
        onClose={() => setIsTicketModalOpen(false)}
        eventId={event.id}
        eventTitle={event.title}
        categories={categories}
        maxTicketsPerBooking={event.maxTicketsPerBooking}
      />
    </div>
  );
}

// Wrap in Suspense because EventDetailContent uses useSearchParams()
export default function EventDetailPage() {
  return (
    <Suspense>
      <EventDetailContent />
    </Suspense>
  );
}
