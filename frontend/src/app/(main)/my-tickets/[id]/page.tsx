"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import {
  ArrowLeft,
  Calendar,
  MapPin,
  Clock,
  Ticket,
  Download,
  AlertCircle,
  CheckCircle2,
  Copy,
  Check,
  ExternalLink,
  Loader2,
} from "lucide-react";
import { Button, Card, CardContent, CardHeader, CardTitle, Badge } from "@/components/ui";
import { useIsAuthenticated } from "@/store/auth";
import { bookingsApi, ticketsApi } from "@/lib/api";
import { formatDate, formatTime, formatPrice } from "@/lib/utils";
import type { BookingDetail, BookingStatus, BookingItem } from "@/types";

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

interface TicketCardProps {
  item: BookingItem;
  eventDate: Date;
  bookingStatus: BookingStatus;
}

function TicketCard({ item, eventDate, bookingStatus }: TicketCardProps) {
  const [copied, setCopied] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);

  const isPastEvent = eventDate < new Date();
  const isUsed = item.isUsed;
  const canDownload = bookingStatus === "confirmed" && !isPastEvent && !isUsed;

  const handleCopyTicketNumber = async () => {
    await navigator.clipboard.writeText(item.ticketNumber);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadPDF = async () => {
    setIsDownloading(true);
    try {
      const blob = await ticketsApi.downloadPDF(item.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `ticket-${item.ticketNumber}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error("Failed to download PDF:", error);
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <Card className={`relative overflow-hidden ${isUsed || isPastEvent ? "opacity-60" : ""}`}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-sm font-medium text-primary">{item.categoryName}</span>
              {item.seatLabel && (
                <span className="text-sm text-foreground-muted">
                  Seat: {item.seatLabel}
                </span>
              )}
            </div>
            <div className="flex items-center gap-2 text-sm text-foreground-muted">
              <span>Ticket: {item.ticketNumber}</span>
              <button
                onClick={handleCopyTicketNumber}
                className="p-1 hover:bg-background-elevated rounded transition-colors"
                title="Copy ticket number"
              >
                {copied ? (
                  <Check className="h-3 w-3 text-success" />
                ) : (
                  <Copy className="h-3 w-3" />
                )}
              </button>
            </div>
            <p className="mt-2 text-lg font-semibold text-foreground">
              {formatPrice(parseFloat(item.price))}
            </p>

            {/* Action Buttons */}
            <div className="flex items-center gap-2 mt-3">
              {canDownload && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleDownloadPDF}
                  disabled={isDownloading}
                  leftIcon={
                    isDownloading ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <Download className="h-3.5 w-3.5" />
                    )
                  }
                >
                  {isDownloading ? "Downloading..." : "Download PDF"}
                </Button>
              )}
            </div>
          </div>

          {/* Status Badge */}
          <div className="flex flex-col items-end gap-2">
            <div className="w-16 h-16 bg-primary/10 rounded-lg flex items-center justify-center">
              <Ticket className="h-8 w-8 text-primary" />
            </div>
            {isUsed && (
              <Badge variant="default" className="text-xs">
                Used
              </Badge>
            )}
          </div>
        </div>

        {/* Used/Past Overlay */}
        {(isUsed || isPastEvent) && (
          <div className="absolute top-2 right-2">
            <span
              className={`text-xs px-2 py-1 rounded-full ${
                isUsed
                  ? "bg-foreground-muted/20 text-foreground-muted"
                  : "bg-warning/20 text-warning"
              }`}
            >
              {isUsed ? "Used" : "Event Ended"}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function TicketDetailPage() {
  const router = useRouter();
  const params = useParams();
  const isAuthenticated = useIsAuthenticated();
  const bookingId = params.id as string;

  const [booking, setBooking] = useState<BookingDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchBooking = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await bookingsApi.get(parseInt(bookingId));
      setBooking(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load booking");
    } finally {
      setIsLoading(false);
    }
  }, [bookingId]);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login?redirect=/my-tickets");
      return;
    }
    if (bookingId) {
      fetchBooking();
    }
  }, [isAuthenticated, router, bookingId, fetchBooking]);

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-3xl mx-auto">
          <div className="animate-pulse space-y-6">
            <div className="h-8 w-48 bg-background-elevated rounded" />
            <div className="h-64 bg-background-elevated rounded-lg" />
            <div className="h-32 bg-background-elevated rounded-lg" />
          </div>
        </div>
      </div>
    );
  }

  if (error || !booking) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-3xl mx-auto">
          <Button
            variant="ghost"
            onClick={() => router.back()}
            leftIcon={<ArrowLeft className="h-4 w-4" />}
            className="mb-6"
          >
            Back
          </Button>
          <div className="text-center py-12">
            <AlertCircle className="h-12 w-12 text-error mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-foreground mb-2">
              Booking Not Found
            </h2>
            <p className="text-foreground-muted mb-6">
              {error || "The booking you're looking for doesn't exist."}
            </p>
            <Button onClick={() => router.push("/my-tickets")}>
              View All Tickets
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const status = STATUS_CONFIG[booking.status] || DEFAULT_STATUS;
  const eventDate = booking.event ? new Date(booking.event.eventDate) : new Date();
  const isPastEvent = eventDate < new Date();

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-3xl mx-auto">
        {/* Back Button */}
        <Button
          variant="ghost"
          onClick={() => router.push("/my-tickets")}
          leftIcon={<ArrowLeft className="h-4 w-4" />}
          className="mb-6"
        >
          Back to My Tickets
        </Button>

        {/* Event Header */}
        <Card className="overflow-hidden mb-6">
          <div className="relative h-48 w-full">
            {booking.event?.bannerImageUrl ? (
              <Image
                src={booking.event.bannerImageUrl}
                alt={booking.event?.title || "Event"}
                fill
                className="object-cover"
              />
            ) : (
              <div className="w-full h-full bg-background-elevated flex items-center justify-center">
                <Ticket className="h-12 w-12 text-foreground-muted" />
              </div>
            )}
            {isPastEvent && booking.status === "confirmed" && (
              <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                <span className="text-white text-lg font-medium">Event Ended</span>
              </div>
            )}
          </div>
          <CardContent className="p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <Badge variant={status.variant} className="mb-2">
                  {status.label}
                </Badge>
                <h1 className="text-2xl font-bold text-foreground mb-2">
                  {booking.event?.title || "Event"}
                </h1>
                <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-foreground-muted">
                  {booking.event && (
                    <>
                      <div className="flex items-center gap-1.5">
                        <Calendar className="h-4 w-4" />
                        <span>{formatDate(booking.event.eventDate)}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Clock className="h-4 w-4" />
                        <span>{formatTime(booking.event.eventDate)}</span>
                      </div>
                      {booking.event.venueName && (
                        <div className="flex items-center gap-1.5">
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
              </div>
              {booking.event && (
                <Link
                  href={`/events/${booking.event.slug}`}
                  className="flex items-center gap-1 text-sm text-primary hover:underline"
                >
                  View Event <ExternalLink className="h-3 w-3" />
                </Link>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Booking Details */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Ticket className="h-5 w-5" />
              Booking Details
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <span className="text-sm text-foreground-muted">Booking Number</span>
                <p className="font-mono font-medium text-foreground">
                  #{booking.bookingNumber}
                </p>
              </div>
              <div>
                <span className="text-sm text-foreground-muted">Booked On</span>
                <p className="font-medium text-foreground">
                  {formatDate(booking.createdAt)}
                </p>
              </div>
              <div>
                <span className="text-sm text-foreground-muted">Total Tickets</span>
                <p className="font-medium text-foreground">{booking.ticketCount}</p>
              </div>
              <div>
                <span className="text-sm text-foreground-muted">Total Amount</span>
                <p className="text-lg font-bold text-primary">
                  {formatPrice(parseFloat(booking.totalAmount))}
                </p>
              </div>
            </div>

            {/* Payment Status */}
            <div className="mt-4 pt-4 border-t border-border">
              <div className="flex items-center justify-between">
                <span className="text-sm text-foreground-muted">Payment Status</span>
                <span
                  className={`flex items-center gap-1.5 text-sm font-medium ${booking.paymentStatus === "success"
                      ? "text-success"
                      : booking.paymentStatus === "failed"
                        ? "text-error"
                        : "text-warning"
                    }`}
                >
                  {booking.paymentStatus === "success" && (
                    <CheckCircle2 className="h-4 w-4" />
                  )}
                  {booking.paymentStatus.charAt(0).toUpperCase() +
                    booking.paymentStatus.slice(1)}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Tickets */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-foreground">
              Your Tickets ({booking.items.length})
            </h2>
            {booking.status === "confirmed" && !isPastEvent && (
              <Button
                variant="outline"
                size="sm"
                leftIcon={<Download className="h-4 w-4" />}
              >
                Download All
              </Button>
            )}
          </div>
          <div className="grid gap-4">
            {booking.items.map((item) => (
              <TicketCard
                key={item.id}
                item={item}
                eventDate={eventDate}
                bookingStatus={booking.status}
              />
            ))}
          </div>
        </div>

        {/* Actions */}
        {booking.status === "confirmed" && !isPastEvent && (
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-foreground">Need help?</h3>
                  <p className="text-sm text-foreground-muted">
                    Contact support for any issues with your booking
                  </p>
                </div>
                <Button variant="outline" size="sm">
                  Contact Support
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
