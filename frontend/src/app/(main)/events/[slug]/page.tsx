"use client";

import { useEffect, useState } from "react";
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

export default function EventDetailPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const slug = params.slug as string;
  const isAuthenticated = useIsAuthenticated();
  const fromQueue = searchParams.get("fromQueue") === "true";

  const [event, setEvent] = useState<EventDetail | null>(null);
  const [categories, setCategories] = useState<SeatCategory[]>([]);
  const [seatsData, setSeatsData] = useState<EventSeatsResponse | null>(null);
  const [queueStatus, setQueueStatus] = useState<QueueStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isJoiningQueue, setIsJoiningQueue] = useState(false);
  const [isTicketModalOpen, setIsTicketModalOpen] = useState(false);
  const [hasOpenedFromQueue, setHasOpenedFromQueue] = useState(false);

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

  // Auto-open ticket modal if user came from queue
  useEffect(() => {
    if (fromQueue && !isLoading && event && categories.length > 0 && !hasOpenedFromQueue) {
      setIsTicketModalOpen(true);
      setHasOpenedFromQueue(true);
    }
  }, [fromQueue, isLoading, event, categories, hasOpenedFromQueue]);

  const handleBookClick = () => {
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

  if (isLoading) {
    return <PageSpinner />;
  }

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

  const isSoldOut = event.availableSeats === 0;
  const isBookingOpen = event.isBookingOpen;
  const canBook = isBookingOpen && !isSoldOut;

  const lowestPrice = categories.length > 0
    ? Math.min(...categories.filter(c => c.isActive).map((c) => parseFloat(c.price)))
    : 0;
  const highestPrice = categories.length > 0
    ? Math.max(...categories.filter(c => c.isActive).map((c) => parseFloat(c.price)))
    : 0;

  return (
    <div className="min-h-screen">
      {/* Hero Banner */}
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

        {/* Action Buttons */}
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
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Event Header */}
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

                {/* Event Details */}
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

            {/* Description */}
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

            {/* Terms & Conditions */}
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

          {/* Sidebar - Booking */}
          <div className="space-y-6">
            <Card className="sticky top-24">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Ticket className="h-5 w-5 text-primary" />
                  Book Tickets
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Price Range */}
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

                {/* Ticket Categories Preview */}
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

                {/* Availability */}
                <div className="flex items-center justify-between py-3 border-t border-border">
                  <div className="flex items-center gap-2 text-sm text-foreground-muted">
                    <Users className="h-4 w-4" />
                    <span>Available Seats</span>
                  </div>
                  <span className="font-medium text-foreground">
                    {event.availableSeats} / {event.totalSeats}
                  </span>
                </div>

                {/* Booking Window */}
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

                {/* Queue Info (if enabled) */}
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

                {/* Book Button */}
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

                {/* Info */}
                <div className="text-xs text-foreground-subtle text-center">
                  Max {event.maxTicketsPerBooking} tickets per booking
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Ticket Selection Modal */}
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
