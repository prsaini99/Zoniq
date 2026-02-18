"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  Users,
  Calendar,
  Ticket,
  DollarSign,
  TrendingUp,
  TrendingDown,
  ArrowRight,
  Loader2,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui";
import { formatPrice } from "@/lib/utils";
import api from "@/lib/api";

interface DashboardOverview {
  total_users: number;
  new_users_today: number;
  new_users_week: number;
  total_events: number;
  active_events: number;
  upcoming_events: number;
  total_bookings: number;
  bookings_today: number;
  bookings_week: number;
  total_revenue: number;
  revenue_today: number;
  revenue_week: number;
  total_tickets_sold: number;
  tickets_sold_today: number;
  tickets_sold_week: number;
}

interface RecentBooking {
  id: number;
  booking_number: string;
  user_email: string;
  user_name: string;
  event_title: string;
  amount: number;
  status: string;
  payment_status: string;
  ticket_count: number;
  created_at: string;
}

interface UpcomingEvent {
  id: number;
  title: string;
  event_date: string;
  status: string;
  total_seats: number;
  available_seats: number;
  bookings: number;
  tickets_sold: number;
}

function StatCard({
  title,
  value,
  subValue,
  subLabel,
  icon: Icon,
  trend,
  trendValue,
}: {
  title: string;
  value: string | number;
  subValue?: string | number;
  subLabel?: string;
  icon: React.ElementType;
  trend?: "up" | "down";
  trendValue?: string;
}) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm text-foreground-muted">{title}</p>
            <p className="text-2xl font-bold text-foreground mt-1">{value}</p>
            {subValue !== undefined && (
              <p className="text-sm text-foreground-muted mt-1">
                <span className="font-medium text-foreground">{subValue}</span>{" "}
                {subLabel}
              </p>
            )}
          </div>
          <div className="p-3 rounded-lg bg-primary/10">
            <Icon className="h-6 w-6 text-primary" />
          </div>
        </div>
        {trend && trendValue && (
          <div className="mt-4 flex items-center gap-1">
            {trend === "up" ? (
              <TrendingUp className="h-4 w-4 text-success" />
            ) : (
              <TrendingDown className="h-4 w-4 text-error" />
            )}
            <span
              className={`text-sm font-medium ${
                trend === "up" ? "text-success" : "text-error"
              }`}
            >
              {trendValue}
            </span>
            <span className="text-sm text-foreground-muted">vs last week</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function AdminDashboardPage() {
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [recentBookings, setRecentBookings] = useState<RecentBooking[]>([]);
  const [upcomingEvents, setUpcomingEvents] = useState<UpcomingEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      setIsLoading(true);
      try {
        const [overviewRes, bookingsRes, eventsRes] = await Promise.all([
          api.get("/admin/dashboard/overview"),
          api.get("/admin/dashboard/recent-bookings?limit=5"),
          api.get("/admin/dashboard/upcoming-events?limit=5"),
        ]);

        setOverview(overviewRes.data);
        setRecentBookings(bookingsRes.data.bookings);
        setUpcomingEvents(eventsRes.data.events);
      } catch (err) {
        setError("Failed to load dashboard data");
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !overview) {
    return (
      <div className="text-center py-12">
        <p className="text-error">{error || "Failed to load dashboard"}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground">Dashboard</h1>
        <p className="text-foreground-muted">
          Welcome back! Here's what's happening with your platform.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Revenue"
          value={formatPrice(overview.total_revenue)}
          subValue={formatPrice(overview.revenue_today)}
          subLabel="today"
          icon={DollarSign}
        />
        <StatCard
          title="Total Bookings"
          value={overview.total_bookings}
          subValue={overview.bookings_today}
          subLabel="today"
          icon={Ticket}
        />
        <StatCard
          title="Total Users"
          value={overview.total_users}
          subValue={overview.new_users_week}
          subLabel="this week"
          icon={Users}
        />
        <StatCard
          title="Active Events"
          value={overview.active_events}
          subValue={overview.upcoming_events}
          subLabel="upcoming"
          icon={Calendar}
        />
      </div>

      {/* Secondary Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-foreground-muted">Tickets Sold (Total)</p>
            <p className="text-3xl font-bold text-foreground mt-1">
              {overview.total_tickets_sold.toLocaleString()}
            </p>
            <p className="text-sm text-foreground-muted mt-2">
              <span className="font-medium text-success">
                +{overview.tickets_sold_week}
              </span>{" "}
              this week
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-foreground-muted">Revenue This Week</p>
            <p className="text-3xl font-bold text-foreground mt-1">
              {formatPrice(overview.revenue_week)}
            </p>
            <p className="text-sm text-foreground-muted mt-2">
              <span className="font-medium text-foreground">
                {overview.bookings_week}
              </span>{" "}
              bookings
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-foreground-muted">Total Events</p>
            <p className="text-3xl font-bold text-foreground mt-1">
              {overview.total_events}
            </p>
            <p className="text-sm text-foreground-muted mt-2">
              <span className="font-medium text-foreground">
                {overview.active_events}
              </span>{" "}
              active
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Bookings & Upcoming Events */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Recent Bookings */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Recent Bookings</CardTitle>
            <Link
              href="/admin/bookings"
              className="text-sm text-primary hover:underline flex items-center gap-1"
            >
              View all <ArrowRight className="h-4 w-4" />
            </Link>
          </CardHeader>
          <CardContent>
            {recentBookings.length === 0 ? (
              <p className="text-foreground-muted text-center py-4">
                No bookings yet
              </p>
            ) : (
              <div className="space-y-4">
                {recentBookings.map((booking) => (
                  <div
                    key={booking.id}
                    className="flex items-center justify-between py-2 border-b border-border last:border-0"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-foreground truncate">
                        {booking.event_title}
                      </p>
                      <p className="text-sm text-foreground-muted">
                        {booking.user_name} &bull; {booking.ticket_count} tickets
                      </p>
                    </div>
                    <div className="text-right ml-4">
                      <p className="font-medium text-foreground">
                        {formatPrice(booking.amount)}
                      </p>
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full ${
                          booking.status === "confirmed"
                            ? "bg-success/20 text-success"
                            : booking.status === "pending"
                            ? "bg-warning/20 text-warning"
                            : "bg-error/20 text-error"
                        }`}
                      >
                        {booking.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Upcoming Events */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Upcoming Events</CardTitle>
            <Link
              href="/admin/events"
              className="text-sm text-primary hover:underline flex items-center gap-1"
            >
              View all <ArrowRight className="h-4 w-4" />
            </Link>
          </CardHeader>
          <CardContent>
            {upcomingEvents.length === 0 ? (
              <p className="text-foreground-muted text-center py-4">
                No upcoming events
              </p>
            ) : (
              <div className="space-y-4">
                {upcomingEvents.map((event) => (
                  <div
                    key={event.id}
                    className="flex items-center justify-between py-2 border-b border-border last:border-0"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-foreground truncate">
                        {event.title}
                      </p>
                      <p className="text-sm text-foreground-muted">
                        {new Date(event.event_date).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="text-right ml-4">
                      <p className="text-sm text-foreground">
                        {event.tickets_sold} / {event.total_seats} sold
                      </p>
                      <div className="w-24 h-2 bg-background-elevated rounded-full mt-1">
                        <div
                          className="h-full bg-primary rounded-full"
                          style={{
                            width: `${Math.min(
                              100,
                              (event.tickets_sold / event.total_seats) * 100
                            )}%`,
                          }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
