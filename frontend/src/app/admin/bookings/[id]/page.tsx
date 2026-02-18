"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Ticket,
  User,
  Calendar,
  Mail,
  Phone,
  CreditCard,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { Button, Card, CardContent, CardHeader, CardTitle } from "@/components/ui";
import { formatDate, formatPrice } from "@/lib/utils";
import api from "@/lib/api";

interface BookingDetail {
  id: number;
  booking_number: string;
  user: {
    id: number;
    username: string;
    email: string;
    full_name: string | null;
  };
  event: {
    id: number;
    title: string;
    event_date: string;
  };
  status: string;
  total_amount: number;
  discount_amount: number;
  final_amount: number;
  payment_status: string;
  promo_code_used: string | null;
  ticket_count: number;
  contact_email: string | null;
  contact_phone: string | null;
  created_at: string;
}

interface TicketItem {
  id: number;
  ticket_number: string;
  category_name: string;
  seat_label: string | null;
  price: number;
  is_used: boolean;
  used_at: string | null;
}

const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  pending: { bg: "bg-warning/20", text: "text-warning" },
  confirmed: { bg: "bg-success/20", text: "text-success" },
  cancelled: { bg: "bg-error/20", text: "text-error" },
};

const PAYMENT_STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  pending: { bg: "bg-warning/20", text: "text-warning" },
  success: { bg: "bg-success/20", text: "text-success" },
  failed: { bg: "bg-error/20", text: "text-error" },
};

export default function BookingDetailPage() {
  const params = useParams();
  const router = useRouter();
  const bookingId = params.id as string;

  const [booking, setBooking] = useState<BookingDetail | null>(null);
  const [tickets, setTickets] = useState<TicketItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchBookingDetails = async () => {
      try {
        setIsLoading(true);
        const [bookingRes, ticketsRes] = await Promise.all([
          api.get(`/admin/bookings/${bookingId}`),
          api.get(`/tickets/booking/${bookingId}`).catch(() => ({ data: [] })),
        ]);

        setBooking(bookingRes.data);
        // tickets endpoint returns array directly, not { tickets: [] }
        setTickets(Array.isArray(ticketsRes.data) ? ticketsRes.data : []);
      } catch (err) {
        console.error("Failed to fetch booking:", err);
        setError("Booking not found");
      } finally {
        setIsLoading(false);
      }
    };

    fetchBookingDetails();
  }, [bookingId]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !booking) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 text-error mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-foreground mb-2">
          Booking Not Found
        </h2>
        <p className="text-foreground-muted mb-4">
          The booking you&apos;re looking for doesn&apos;t exist.
        </p>
        <Link href="/admin/bookings">
          <Button>Back to Bookings</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.back()}
          leftIcon={<ArrowLeft className="h-4 w-4" />}
        >
          Back
        </Button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-foreground">
            Booking #{booking.booking_number}
          </h1>
          <p className="text-foreground-muted">
            Created on {formatDate(booking.created_at)}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`inline-flex px-3 py-1 rounded-full text-sm font-medium ${
              STATUS_COLORS[booking.status]?.bg || "bg-gray-100"
            } ${STATUS_COLORS[booking.status]?.text || "text-gray-800"}`}
          >
            {booking.status}
          </span>
          <span
            className={`inline-flex px-3 py-1 rounded-full text-sm font-medium ${
              PAYMENT_STATUS_COLORS[booking.payment_status]?.bg || "bg-gray-100"
            } ${PAYMENT_STATUS_COLORS[booking.payment_status]?.text || "text-gray-800"}`}
          >
            Payment: {booking.payment_status}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Main Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Event Info */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5 text-primary" />
                Event Details
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-foreground-muted">Event</p>
                  <Link
                    href={`/admin/events/${booking.event.id}`}
                    className="text-lg font-medium text-foreground hover:text-primary"
                  >
                    {booking.event.title}
                  </Link>
                </div>
                <div>
                  <p className="text-sm text-foreground-muted">Event Date</p>
                  <p className="font-medium text-foreground">
                    {formatDate(booking.event.event_date)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Customer Info */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5 text-primary" />
                Customer Details
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-foreground-muted">Name</p>
                  <p className="font-medium text-foreground">
                    {booking.user.full_name || booking.user.username}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-foreground-muted">Username</p>
                  <p className="font-medium text-foreground">
                    @{booking.user.username}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Mail className="h-4 w-4 text-foreground-muted" />
                  <div>
                    <p className="text-sm text-foreground-muted">Email</p>
                    <p className="font-medium text-foreground">
                      {booking.user.email}
                    </p>
                  </div>
                </div>
                {booking.contact_phone && (
                  <div className="flex items-center gap-2">
                    <Phone className="h-4 w-4 text-foreground-muted" />
                    <div>
                      <p className="text-sm text-foreground-muted">Phone</p>
                      <p className="font-medium text-foreground">
                        {booking.contact_phone}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Tickets */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Ticket className="h-5 w-5 text-primary" />
                Tickets ({booking.ticket_count})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {tickets.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-border">
                        <th className="text-left p-3 text-sm font-medium text-foreground-muted">
                          Ticket #
                        </th>
                        <th className="text-left p-3 text-sm font-medium text-foreground-muted">
                          Category
                        </th>
                        <th className="text-left p-3 text-sm font-medium text-foreground-muted">
                          Seat
                        </th>
                        <th className="text-left p-3 text-sm font-medium text-foreground-muted">
                          Price
                        </th>
                        <th className="text-left p-3 text-sm font-medium text-foreground-muted">
                          Status
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {tickets.map((ticket) => (
                        <tr
                          key={ticket.id}
                          className="border-b border-border last:border-0"
                        >
                          <td className="p-3 font-mono text-sm text-foreground">
                            {ticket.ticket_number}
                          </td>
                          <td className="p-3 text-foreground">
                            {ticket.category_name}
                          </td>
                          <td className="p-3 text-foreground">
                            {ticket.seat_label || "-"}
                          </td>
                          <td className="p-3 text-foreground">
                            {formatPrice(ticket.price)}
                          </td>
                          <td className="p-3">
                            {ticket.is_used ? (
                              <span className="inline-flex px-2 py-1 rounded-full text-xs font-medium bg-success/20 text-success">
                                Used
                              </span>
                            ) : (
                              <span className="inline-flex px-2 py-1 rounded-full text-xs font-medium bg-foreground-muted/20 text-foreground-muted">
                                Not Used
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-foreground-muted text-center py-4">
                  No ticket details available
                </p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Payment Summary */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CreditCard className="h-5 w-5 text-primary" />
                Payment Summary
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between">
                <span className="text-foreground-muted">Subtotal</span>
                <span className="text-foreground">
                  {formatPrice(booking.total_amount)}
                </span>
              </div>
              {booking.discount_amount > 0 && (
                <div className="flex justify-between">
                  <span className="text-foreground-muted">
                    Discount
                    {booking.promo_code_used && (
                      <span className="text-xs ml-1">({booking.promo_code_used})</span>
                    )}
                  </span>
                  <span className="text-success">
                    -{formatPrice(booking.discount_amount)}
                  </span>
                </div>
              )}
              <div className="border-t border-border pt-4 flex justify-between">
                <span className="font-medium text-foreground">Total</span>
                <span className="font-bold text-lg text-foreground">
                  {formatPrice(booking.final_amount)}
                </span>
              </div>
            </CardContent>
          </Card>

          {/* Quick Info */}
          <Card>
            <CardContent className="p-4 space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-foreground-muted">Booking ID</span>
                <span className="font-mono text-foreground">{booking.id}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-foreground-muted">User ID</span>
                <span className="font-mono text-foreground">{booking.user.id}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-foreground-muted">Event ID</span>
                <span className="font-mono text-foreground">{booking.event.id}</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
