/**
 * AdminBookingsPage - Lists all platform bookings with filtering, search, and pagination.
 *
 * Features:
 * - Summary stat cards (total, confirmed, pending, cancelled, revenue, tickets sold).
 * - Search by booking number.
 * - Filter by booking status and payment status.
 * - Paginated table of bookings with color-coded status/payment badges.
 * - "View" action button linking to the booking detail page.
 *
 * Data is fetched from /admin/bookings (with query params) and /admin/bookings/stats.
 * Refetches whenever page, search, statusFilter, or paymentFilter changes.
 */
"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  Search,
  Ticket,
  Download,
  Loader2,
  Eye,
} from "lucide-react";
import { Button, Card, CardContent } from "@/components/ui";
import { formatDate, formatPrice } from "@/lib/utils";
import api from "@/lib/api";

// Shape of an individual booking row returned by the API
interface Booking {
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
  created_at: string;
}

// Aggregate booking statistics
interface BookingStats {
  total_bookings: number;
  confirmed_bookings: number;
  pending_bookings: number;
  cancelled_bookings: number;
  total_revenue: number;
  total_tickets_sold: number;
}

// Mapping of booking statuses to Tailwind background/text color classes
const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  pending: { bg: "bg-warning/20", text: "text-warning" },
  confirmed: { bg: "bg-success/20", text: "text-success" },
  cancelled: { bg: "bg-error/20", text: "text-error" },
  refunded: { bg: "bg-foreground-muted/20", text: "text-foreground-muted" },
};

// Mapping of payment statuses to Tailwind background/text color classes
const PAYMENT_STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  pending: { bg: "bg-warning/20", text: "text-warning" },
  success: { bg: "bg-success/20", text: "text-success" },
  failed: { bg: "bg-error/20", text: "text-error" },
  refunded: { bg: "bg-primary/20", text: "text-primary" },
};

export default function AdminBookingsPage() {
  // Bookings list and aggregate stats
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [stats, setStats] = useState<BookingStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  // Filter/search state
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [paymentFilter, setPaymentFilter] = useState<string>("");
  // Pagination state
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 20;

  // Memoized fetch function - rebuilds query params from current filters and page
  const fetchBookings = useCallback(async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      });
      if (search) params.append("search", search);
      if (statusFilter) params.append("status", statusFilter);
      if (paymentFilter) params.append("payment_status", paymentFilter);

      // Fetch bookings list and aggregate stats in parallel
      const [bookingsRes, statsRes] = await Promise.all([
        api.get(`/admin/bookings?${params}`),
        api.get("/admin/bookings/stats"),
      ]);

      setBookings(bookingsRes.data.bookings);
      setTotal(bookingsRes.data.total);
      setStats(statsRes.data);
    } catch (err) {
      console.error("Failed to fetch bookings:", err);
    } finally {
      setIsLoading(false);
    }
  }, [page, search, statusFilter, paymentFilter]);

  // Trigger re-fetch whenever the fetch dependencies change
  useEffect(() => {
    fetchBookings();
  }, [fetchBookings]);

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="space-y-6">
      {/* Page Header with export button */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Bookings</h1>
          <p className="text-foreground-muted">
            View and manage all bookings
          </p>
        </div>
        <Button variant="outline" leftIcon={<Download className="h-4 w-4" />}>
          Export
        </Button>
      </div>

      {/* Summary Stats Row - 6 metric cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-6">
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-foreground">
                {stats.total_bookings}
              </p>
              <p className="text-sm text-foreground-muted">Total Bookings</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-success">
                {stats.confirmed_bookings}
              </p>
              <p className="text-sm text-foreground-muted">Confirmed</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-warning">
                {stats.pending_bookings}
              </p>
              <p className="text-sm text-foreground-muted">Pending</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-error">
                {stats.cancelled_bookings}
              </p>
              <p className="text-sm text-foreground-muted">Cancelled</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-foreground">
                {formatPrice(stats.total_revenue)}
              </p>
              <p className="text-sm text-foreground-muted">Total Revenue</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-foreground">
                {stats.total_tickets_sold}
              </p>
              <p className="text-sm text-foreground-muted">Tickets Sold</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters: search input, booking status dropdown, payment status dropdown */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            {/* Search by booking number */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-foreground-muted" />
              <input
                type="text"
                placeholder="Search by booking number..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
                className="w-full pl-10 pr-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>
            {/* Booking status filter */}
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
            >
              <option value="">All Status</option>
              <option value="pending">Pending</option>
              <option value="confirmed">Confirmed</option>
              <option value="cancelled">Cancelled</option>
            </select>
            {/* Payment status filter */}
            <select
              value={paymentFilter}
              onChange={(e) => {
                setPaymentFilter(e.target.value);
                setPage(1);
              }}
              className="px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
            >
              <option value="">All Payments</option>
              <option value="pending">Pending</option>
              <option value="success">Success</option>
              <option value="failed">Failed</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Bookings Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : bookings.length === 0 ? (
            <div className="text-center py-12">
              <Ticket className="h-12 w-12 text-foreground-muted mx-auto mb-4" />
              <p className="text-foreground-muted">No bookings found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left p-4 text-sm font-medium text-foreground-muted">
                      Booking
                    </th>
                    <th className="text-left p-4 text-sm font-medium text-foreground-muted">
                      Customer
                    </th>
                    <th className="text-left p-4 text-sm font-medium text-foreground-muted">
                      Event
                    </th>
                    <th className="text-left p-4 text-sm font-medium text-foreground-muted">
                      Tickets
                    </th>
                    <th className="text-left p-4 text-sm font-medium text-foreground-muted">
                      Amount
                    </th>
                    <th className="text-left p-4 text-sm font-medium text-foreground-muted">
                      Status
                    </th>
                    <th className="text-left p-4 text-sm font-medium text-foreground-muted">
                      Payment
                    </th>
                    <th className="text-right p-4 text-sm font-medium text-foreground-muted">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {bookings.map((booking) => (
                    <tr
                      key={booking.id}
                      className="border-b border-border last:border-0 hover:bg-background-soft"
                    >
                      {/* Booking number and creation date */}
                      <td className="p-4">
                        <p className="font-mono text-foreground">
                          #{booking.booking_number}
                        </p>
                        <p className="text-xs text-foreground-muted">
                          {formatDate(booking.created_at)}
                        </p>
                      </td>
                      {/* Customer name and email */}
                      <td className="p-4">
                        <p className="font-medium text-foreground">
                          {booking.user.full_name || booking.user.username}
                        </p>
                        <p className="text-sm text-foreground-muted">
                          {booking.user.email}
                        </p>
                      </td>
                      {/* Event title and date */}
                      <td className="p-4">
                        <p className="font-medium text-foreground truncate max-w-[200px]">
                          {booking.event.title}
                        </p>
                        <p className="text-sm text-foreground-muted">
                          {formatDate(booking.event.event_date)}
                        </p>
                      </td>
                      {/* Ticket count */}
                      <td className="p-4">
                        <p className="text-foreground">{booking.ticket_count}</p>
                      </td>
                      {/* Final amount with optional discount line */}
                      <td className="p-4">
                        <p className="font-medium text-foreground">
                          {formatPrice(booking.final_amount)}
                        </p>
                        {booking.discount_amount > 0 && (
                          <p className="text-xs text-success">
                            -{formatPrice(booking.discount_amount)}
                          </p>
                        )}
                      </td>
                      {/* Booking status badge */}
                      <td className="p-4">
                        <span
                          className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                            STATUS_COLORS[booking.status]?.bg
                          } ${STATUS_COLORS[booking.status]?.text}`}
                        >
                          {booking.status}
                        </span>
                      </td>
                      {/* Payment status badge */}
                      <td className="p-4">
                        <span
                          className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                            PAYMENT_STATUS_COLORS[booking.payment_status]?.bg
                          } ${PAYMENT_STATUS_COLORS[booking.payment_status]?.text}`}
                        >
                          {booking.payment_status}
                        </span>
                      </td>
                      {/* View detail action */}
                      <td className="p-4">
                        <div className="flex items-center justify-end">
                          <Link href={`/admin/bookings/${booking.id}`}>
                            <Button variant="ghost" size="sm">
                              <Eye className="h-4 w-4" />
                            </Button>
                          </Link>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pagination controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-foreground-muted">
            Showing {(page - 1) * pageSize + 1} to{" "}
            {Math.min(page * pageSize, total)} of {total} bookings
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page === 1}
              onClick={() => setPage(page - 1)}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page === totalPages}
              onClick={() => setPage(page + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
