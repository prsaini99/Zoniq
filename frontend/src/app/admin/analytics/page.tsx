/**
 * AdminAnalyticsPage - Displays detailed platform analytics and performance metrics.
 *
 * Features:
 * - Key metric stat cards (revenue, bookings, users, tickets) with growth trend indicators.
 * - A date-range selector (week/month/quarter) that re-fetches chart data on change.
 * - A bar chart visualizing revenue over the selected period.
 * - A ranked list of top-performing events by revenue.
 * - Additional stat cards for active and completed events.
 * - Period breakdowns for today, this week, and this month.
 *
 * Data is loaded from three parallel API calls: overview, top events, and revenue chart.
 */
"use client";

import { useState, useEffect } from "react";
import {
  BarChart3,
  Calendar,
  Users,
  Ticket,
  DollarSign,
  Loader2,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui";
import { formatPrice } from "@/lib/utils";
import api from "@/lib/api";

// Shape of the analytics overview data returned by the API
interface AnalyticsOverview {
  total_revenue: number;
  revenue_today: number;
  revenue_week: number;
  revenue_month: number;
  revenue_growth_percent: number;
  total_bookings: number;
  bookings_today: number;
  bookings_week: number;
  bookings_month: number;
  bookings_growth_percent: number;
  total_users: number;
  new_users_today: number;
  new_users_week: number;
  new_users_month: number;
  users_growth_percent: number;
  total_events: number;
  active_events: number;
  completed_events: number;
  upcoming_events: number;
  total_tickets_sold: number;
  tickets_sold_today: number;
  tickets_sold_week: number;
}

// A single top-performing event entry
interface TopEvent {
  id: number;
  title: string;
  revenue: number;
  tickets_sold: number;
  bookings: number;
}

// A single data point for the revenue bar chart
interface RevenueDataPoint {
  date: string;
  revenue: number;
  bookings: number;
}

/**
 * StatCard - Renders a single analytics KPI card with an optional
 * growth percentage trend (up/down/neutral arrow + colored label).
 */
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
  trend?: "up" | "down" | "neutral";
  trendValue?: number;
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
        {/* Trend indicator: shows percentage change vs the prior period */}
        {trendValue !== undefined && (
          <div className="mt-4 flex items-center gap-1">
            {trend === "up" ? (
              <ArrowUpRight className="h-4 w-4 text-success" />
            ) : trend === "down" ? (
              <ArrowDownRight className="h-4 w-4 text-error" />
            ) : null}
            <span
              className={`text-sm font-medium ${
                trend === "up"
                  ? "text-success"
                  : trend === "down"
                  ? "text-error"
                  : "text-foreground-muted"
              }`}
            >
              {trendValue > 0 ? "+" : ""}
              {trendValue.toFixed(1)}%
            </span>
            <span className="text-sm text-foreground-muted">vs last period</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function AdminAnalyticsPage() {
  // Core analytics state
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [topEvents, setTopEvents] = useState<TopEvent[]>([]);
  const [revenueData, setRevenueData] = useState<RevenueDataPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  // Selected date range filter; drives re-fetch via the useEffect dependency
  const [dateRange, setDateRange] = useState("week");

  // Fetch analytics data whenever the dateRange changes
  useEffect(() => {
    const fetchAnalytics = async () => {
      setIsLoading(true);
      try {
        const [overviewRes, topEventsRes, revenueChartRes] = await Promise.all([
          api.get("/admin/dashboard/overview"),
          api.get("/admin/bookings/top-events?limit=5"),
          api.get(`/admin/dashboard/revenue-chart?period=${dateRange}`),
        ]);

        setOverview(overviewRes.data);
        setTopEvents(topEventsRes.data.events || []);
        setRevenueData(revenueChartRes.data.data || []);
      } catch (err) {
        console.error("Failed to fetch analytics:", err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAnalytics();
  }, [dateRange]);

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  // Error / empty state
  if (!overview) {
    return (
      <div className="text-center py-12">
        <BarChart3 className="h-12 w-12 text-foreground-muted mx-auto mb-4" />
        <p className="text-foreground-muted">Failed to load analytics</p>
      </div>
    );
  }

  // Used to scale bar heights proportionally in the revenue chart
  const maxRevenue = Math.max(...revenueData.map((d) => d.revenue), 1);

  return (
    <div className="space-y-6">
      {/* Page header with date-range selector dropdown */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Analytics</h1>
          <p className="text-foreground-muted">
            Platform performance and insights
          </p>
        </div>
        <select
          value={dateRange}
          onChange={(e) => setDateRange(e.target.value)}
          className="px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
        >
          <option value="week">Last 7 days</option>
          <option value="month">Last 30 days</option>
          <option value="quarter">Last 90 days</option>
        </select>
      </div>

      {/* Key Metrics row - 4 stat cards with growth trends */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Revenue"
          value={formatPrice(overview.total_revenue)}
          subValue={formatPrice(overview.revenue_week)}
          subLabel="this week"
          icon={DollarSign}
          trend={overview.revenue_growth_percent >= 0 ? "up" : "down"}
          trendValue={overview.revenue_growth_percent}
        />
        <StatCard
          title="Total Bookings"
          value={overview.total_bookings.toLocaleString()}
          subValue={overview.bookings_week}
          subLabel="this week"
          icon={Ticket}
          trend={overview.bookings_growth_percent >= 0 ? "up" : "down"}
          trendValue={overview.bookings_growth_percent}
        />
        <StatCard
          title="Total Users"
          value={overview.total_users.toLocaleString()}
          subValue={overview.new_users_week}
          subLabel="new this week"
          icon={Users}
          trend={overview.users_growth_percent >= 0 ? "up" : "down"}
          trendValue={overview.users_growth_percent}
        />
        <StatCard
          title="Tickets Sold"
          value={overview.total_tickets_sold.toLocaleString()}
          subValue={overview.tickets_sold_week}
          subLabel="this week"
          icon={Calendar}
        />
      </div>

      {/* Revenue Chart (bar chart) & Top Events (ranked list) */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Revenue bar chart - each bar is proportionally scaled to maxRevenue */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Revenue Overview</CardTitle>
          </CardHeader>
          <CardContent>
            {revenueData.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-foreground-muted">
                No revenue data available
              </div>
            ) : (
              <div className="h-64">
                <div className="flex items-end justify-between h-full gap-1">
                  {revenueData.map((data, index) => (
                    <div
                      key={index}
                      className="flex-1 flex flex-col items-center gap-2"
                    >
                      <div className="w-full flex flex-col items-center">
                        {/* Revenue label above each bar */}
                        <span className="text-xs text-foreground-muted mb-1">
                          {formatPrice(data.revenue)}
                        </span>
                        {/* Bar element whose height is proportional to revenue */}
                        <div
                          className="w-full bg-primary rounded-t-sm transition-all duration-300"
                          style={{
                            height: `${Math.max(
                              (data.revenue / maxRevenue) * 180,
                              4
                            )}px`,
                          }}
                        />
                      </div>
                      {/* Date label below each bar */}
                      <span className="text-xs text-foreground-muted truncate max-w-full">
                        {new Date(data.date).toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                        })}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Top Performing Events - ranked list with numbered badges */}
        <Card>
          <CardHeader>
            <CardTitle>Top Events</CardTitle>
          </CardHeader>
          <CardContent>
            {topEvents.length === 0 ? (
              <p className="text-foreground-muted text-center py-4">
                No events yet
              </p>
            ) : (
              <div className="space-y-4">
                {topEvents.map((event, index) => (
                  <div
                    key={event.id}
                    className="flex items-center gap-3 py-2 border-b border-border last:border-0"
                  >
                    {/* Rank number badge */}
                    <div className="w-6 h-6 rounded-full bg-primary/20 text-primary flex items-center justify-center text-sm font-bold">
                      {index + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-foreground truncate">
                        {event.title}
                      </p>
                      <p className="text-sm text-foreground-muted">
                        {event.tickets_sold} tickets
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium text-foreground">
                        {formatPrice(event.revenue)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Additional Stats - active and completed event counts */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-lg bg-warning/10">
                <Calendar className="h-5 w-5 text-warning" />
              </div>
              <div>
                <p className="text-sm text-foreground-muted">Active Events</p>
                <p className="text-xl font-bold text-foreground">
                  {overview.active_events}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-lg bg-foreground-muted/10">
                <BarChart3 className="h-5 w-5 text-foreground-muted" />
              </div>
              <div>
                <p className="text-sm text-foreground-muted">Completed Events</p>
                <p className="text-xl font-bold text-foreground">
                  {overview.completed_events || 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Period-specific Stats Grid: Today / This Week / This Month */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Today's Stats */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Today</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-foreground-muted">Revenue</span>
              <span className="font-semibold text-foreground">
                {formatPrice(overview.revenue_today)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-foreground-muted">Bookings</span>
              <span className="font-semibold text-foreground">
                {overview.bookings_today}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-foreground-muted">Tickets Sold</span>
              <span className="font-semibold text-foreground">
                {overview.tickets_sold_today}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-foreground-muted">New Users</span>
              <span className="font-semibold text-foreground">
                {overview.new_users_today}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* This Week's Stats */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">This Week</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-foreground-muted">Revenue</span>
              <span className="font-semibold text-foreground">
                {formatPrice(overview.revenue_week)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-foreground-muted">Bookings</span>
              <span className="font-semibold text-foreground">
                {overview.bookings_week}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-foreground-muted">Tickets Sold</span>
              <span className="font-semibold text-foreground">
                {overview.tickets_sold_week}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-foreground-muted">New Users</span>
              <span className="font-semibold text-foreground">
                {overview.new_users_week}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* This Month's Stats */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">This Month</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-foreground-muted">Revenue</span>
              <span className="font-semibold text-foreground">
                {formatPrice(overview.revenue_month || 0)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-foreground-muted">Bookings</span>
              <span className="font-semibold text-foreground">
                {overview.bookings_month || 0}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-foreground-muted">Total Events</span>
              <span className="font-semibold text-foreground">
                {overview.total_events}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-foreground-muted">New Users</span>
              <span className="font-semibold text-foreground">
                {overview.new_users_month || 0}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
