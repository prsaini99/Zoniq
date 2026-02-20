/*
 * Order Confirmation page: displayed after a successful payment.
 * Shows a success animation, booking number (with copy-to-clipboard),
 * event details, ticket list with individual prices, price summary
 * (subtotal, discount, total), and navigation links to "My Tickets"
 * and "Browse Events".
 *
 * Fetches booking details by ID from the bookings API on mount.
 * Requires authentication; redirects to /login if not authenticated.
 */

"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
    CheckCircle2,
    Download,
    Calendar,
    MapPin,
    Ticket,
    ArrowLeft,
    Copy,
    ExternalLink,
    Loader2,
    PartyPopper,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { bookingsApi } from "@/lib/api";
import { useIsAuthenticated } from "@/store/auth";
import type { BookingDetail } from "@/types";

export default function OrderConfirmationPage() {
    const params = useParams();
    const router = useRouter();
    const isAuthenticated = useIsAuthenticated();
    const [booking, setBooking] = useState<BookingDetail | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState("");
    // Tracks whether the booking number was just copied to clipboard
    const [copied, setCopied] = useState(false);

    // Extract the booking ID from the dynamic route segment
    const bookingId = Number(params.id);

    // Redirect if not authenticated, otherwise fetch booking details
    useEffect(() => {
        if (!isAuthenticated) {
            router.push("/login?redirect=/");
            return;
        }

        const fetchBooking = async () => {
            try {
                const data = await bookingsApi.get(bookingId);
                setBooking(data);
            } catch (err: any) {
                setError(err.response?.data?.detail || "Booking not found");
            } finally {
                setIsLoading(false);
            }
        };

        if (bookingId) fetchBooking();
    }, [bookingId, isAuthenticated, router]);

    // Copy the booking number to clipboard and show brief confirmation
    const copyBookingNumber = () => {
        if (booking?.bookingNumber) {
            navigator.clipboard.writeText(booking.bookingNumber);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    // Loading spinner
    if (isLoading) {
        return (
            <div className="container mx-auto px-4 py-20 flex items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    // Error / not found state
    if (error || !booking) {
        return (
            <div className="container mx-auto px-4 py-20 text-center">
                <h1 className="text-2xl font-bold text-foreground mb-3">Booking Not Found</h1>
                <p className="text-foreground-muted mb-8">{error || "Could not find this booking"}</p>
                <Link href="/my-tickets" className="text-primary hover:underline">
                    View My Tickets
                </Link>
            </div>
        );
    }

    return (
        <div className="container mx-auto px-4 py-8">
            {/* Success header with checkmark icon and confirmation message */}
            <div className="mb-8 text-center">
                <div className="mb-6 inline-flex h-20 w-20 items-center justify-center rounded-full bg-green-500/10">
                    <CheckCircle2 className="h-10 w-10 text-green-500" />
                </div>
                <h1 className="text-3xl font-bold text-foreground mb-2">
                    Booking Confirmed! <PartyPopper className="inline h-7 w-7 text-amber-500" />
                </h1>
                <p className="text-foreground-muted max-w-lg mx-auto">
                    Your tickets have been booked successfully. A confirmation email will be sent to{" "}
                    <span className="font-medium text-foreground">{booking.contactEmail}</span>
                </p>
            </div>

            <div className="mx-auto max-w-3xl space-y-6">
                {/* Booking Number Card: prominent display with copy button */}
                <div className="rounded-2xl bg-gradient-to-br from-primary/10 via-primary/5 to-transparent border border-primary/20 p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-foreground-muted mb-1">Booking Number</p>
                            <p className="text-2xl font-mono font-bold text-primary tracking-wider">
                                {booking.bookingNumber}
                            </p>
                        </div>
                        <button
                            onClick={copyBookingNumber}
                            className="flex items-center gap-2 rounded-xl bg-primary/10 px-4 py-2.5 text-sm font-medium text-primary hover:bg-primary/20 transition-colors"
                        >
                            {copied ? (
                                <>
                                    <CheckCircle2 className="h-4 w-4" />
                                    Copied!
                                </>
                            ) : (
                                <>
                                    <Copy className="h-4 w-4" />
                                    Copy
                                </>
                            )}
                        </button>
                    </div>
                </div>

                {/* Event Details: banner image, title, date/time, and venue */}
                <div className="rounded-2xl border border-border bg-background-soft p-6">
                    <h2 className="text-lg font-bold text-foreground mb-4">Event Details</h2>
                    <div className="flex gap-4">
                        {booking.event?.bannerImageUrl && (
                            <img
                                src={booking.event.bannerImageUrl}
                                alt={booking.event?.title || "Event"}
                                className="h-24 w-36 rounded-xl object-cover"
                            />
                        )}
                        <div className="flex-1">
                            <h3 className="font-semibold text-foreground text-lg">{booking.event?.title}</h3>
                            {booking.event?.eventDate && (
                                <div className="mt-2 flex items-center gap-2 text-sm text-foreground-muted">
                                    <Calendar className="h-4 w-4" />
                                    {new Date(booking.event.eventDate).toLocaleDateString("en-IN", {
                                        weekday: "long",
                                        year: "numeric",
                                        month: "long",
                                        day: "numeric",
                                        hour: "2-digit",
                                        minute: "2-digit",
                                    })}
                                </div>
                            )}
                            {booking.event?.venueName && (
                                <div className="mt-1 flex items-center gap-2 text-sm text-foreground-muted">
                                    <MapPin className="h-4 w-4" />
                                    {booking.event.venueName}
                                    {booking.event.venueCity && `, ${booking.event.venueCity}`}
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Ticket List: numbered list of each booked ticket with category, seat, and price */}
                <div className="rounded-2xl border border-border bg-background-soft p-6">
                    <h2 className="text-lg font-bold text-foreground mb-4 flex items-center gap-2">
                        <Ticket className="h-5 w-5 text-primary" />
                        Your Tickets ({booking.ticketCount})
                    </h2>
                    <div className="space-y-3">
                        {booking.items.map((item, idx) => (
                            <div
                                key={item.id}
                                className="flex items-center justify-between rounded-xl bg-background p-4"
                            >
                                <div className="flex items-center gap-3">
                                    {/* Ticket index number */}
                                    <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-xs font-bold text-primary">
                                        {idx + 1}
                                    </span>
                                    <div>
                                        <p className="font-medium text-foreground">{item.categoryName}</p>
                                        {item.seatLabel && (
                                            <p className="text-xs text-foreground-muted">Seat: {item.seatLabel}</p>
                                        )}
                                        <p className="text-xs text-foreground-muted font-mono mt-0.5">
                                            {item.ticketNumber}
                                        </p>
                                    </div>
                                </div>
                                <span className="font-semibold text-foreground">₹{parseFloat(item.price).toLocaleString()}</span>
                            </div>
                        ))}
                    </div>

                    {/* Price Summary: subtotal, discount (if any), and total paid */}
                    <div className="mt-4 space-y-2 border-t border-border pt-4">
                        <div className="flex justify-between text-sm">
                            <span className="text-foreground-muted">Subtotal</span>
                            <span className="text-foreground">₹{parseFloat(booking.totalAmount).toLocaleString()}</span>
                        </div>
                        {parseFloat(booking.discountAmount) > 0 && (
                            <div className="flex justify-between text-sm">
                                <span className="text-green-500">
                                    Discount {booking.promoCodeUsed && `(${booking.promoCodeUsed})`}
                                </span>
                                <span className="text-green-500">-₹{parseFloat(booking.discountAmount).toLocaleString()}</span>
                            </div>
                        )}
                        <div className="flex justify-between text-lg font-bold border-t border-border pt-2">
                            <span className="text-foreground">Total Paid</span>
                            <span className="text-primary">₹{parseFloat(booking.finalAmount).toLocaleString()}</span>
                        </div>
                    </div>
                </div>

                {/* Navigation actions: "View My Tickets" and "Browse More Events" */}
                <div className="flex flex-col sm:flex-row gap-3">
                    <Link
                        href="/my-tickets"
                        className="flex-1 flex items-center justify-center gap-2 rounded-xl bg-primary px-6 py-3.5 text-sm font-semibold text-white hover:bg-primary/90 transition-colors"
                    >
                        <Ticket className="h-4 w-4" />
                        View My Tickets
                    </Link>
                    <Link
                        href="/events"
                        className="flex-1 flex items-center justify-center gap-2 rounded-xl border border-border px-6 py-3.5 text-sm font-medium text-foreground hover:bg-background-soft transition-colors"
                    >
                        Browse More Events
                    </Link>
                </div>

                {/* Info Note about e-ticket delivery */}
                <div className="rounded-xl bg-blue-500/5 border border-blue-500/10 p-4 text-sm text-foreground-muted">
                    <p>
                        <strong className="text-foreground">📩 E-ticket sent!</strong>{" "}
                        Check your email for your tickets. You can also view and download them from the{" "}
                        <Link href="/my-tickets" className="text-primary hover:underline">My Tickets</Link> page.
                    </p>
                </div>
            </div>
        </div>
    );
}
