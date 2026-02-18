"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  Plus,
  Search,
  Calendar,
  MapPin,
  MoreVertical,
  Edit,
  Trash2,
  Eye,
  CheckCircle,
  XCircle,
  Loader2,
  RotateCcw,
} from "lucide-react";
import { Button, Card, CardContent, Badge } from "@/components/ui";
import { formatDate, formatPrice } from "@/lib/utils";
import api from "@/lib/api";

interface Venue {
  id: number;
  name: string;
  city: string | null;
  state: string | null;
}

interface Event {
  id: number;
  title: string;
  slug: string;
  category: string;
  status: string;
  eventDate: string;
  venue: Venue | null;
  totalSeats: number;
  availableSeats: number;
  createdAt: string;
}

interface EventStats {
  total: number;
  published: number;
  draft: number;
  cancelled: number;
  completed: number;
}

const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  draft: { bg: "bg-foreground-muted/20", text: "text-foreground-muted" },
  published: { bg: "bg-success/20", text: "text-success" },
  cancelled: { bg: "bg-error/20", text: "text-error" },
  completed: { bg: "bg-primary/20", text: "text-primary" },
  soldout: { bg: "bg-warning/20", text: "text-warning" },
};

export default function AdminEventsPage() {
  const [events, setEvents] = useState<Event[]>([]);
  const [stats, setStats] = useState<EventStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 10;

  const fetchEvents = useCallback(async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      });
      if (search) params.append("search", search);
      if (statusFilter) params.append("status", statusFilter);

      const [eventsRes, statsRes] = await Promise.all([
        api.get(`/admin/events?${params}`),
        api.get("/admin/events/stats"),
      ]);

      setEvents(eventsRes.data.events);
      setTotal(eventsRes.data.total);
      setStats(statsRes.data);
    } catch (err) {
      console.error("Failed to fetch events:", err);
    } finally {
      setIsLoading(false);
    }
  }, [page, search, statusFilter]);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  const handlePublish = async (eventId: number) => {
    try {
      await api.post(`/admin/events/${eventId}/publish`);
      fetchEvents();
    } catch (err) {
      console.error("Failed to publish event:", err);
    }
  };

  const handleCancel = async (eventId: number) => {
    if (!confirm("Are you sure you want to cancel this event?")) return;
    try {
      await api.post(`/admin/events/${eventId}/cancel`);
      fetchEvents();
    } catch (err) {
      console.error("Failed to cancel event:", err);
    }
  };

  const handleReactivate = async (eventId: number) => {
    if (!confirm("Reactivate this event? It will be set to draft status.")) return;
    try {
      await api.post(`/admin/events/${eventId}/reactivate`);
      fetchEvents();
    } catch (err) {
      console.error("Failed to reactivate event:", err);
    }
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Events</h1>
          <p className="text-foreground-muted">
            Manage your events and ticket sales
          </p>
        </div>
        <Link href="/admin/events/new">
          <Button leftIcon={<Plus className="h-4 w-4" />}>Create Event</Button>
        </Link>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-5">
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-foreground">{stats.total}</p>
              <p className="text-sm text-foreground-muted">Total Events</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-success">{stats.published}</p>
              <p className="text-sm text-foreground-muted">Published</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-foreground-muted">
                {stats.draft}
              </p>
              <p className="text-sm text-foreground-muted">Draft</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-primary">{stats.completed}</p>
              <p className="text-sm text-foreground-muted">Completed</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-error">{stats.cancelled}</p>
              <p className="text-sm text-foreground-muted">Cancelled</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-foreground-muted" />
              <input
                type="text"
                placeholder="Search events..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
                className="w-full pl-10 pr-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
            >
              <option value="">All Status</option>
              <option value="draft">Draft</option>
              <option value="published">Published</option>
              <option value="cancelled">Cancelled</option>
              <option value="completed">Completed</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Events List */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : events.length === 0 ? (
            <div className="text-center py-12">
              <Calendar className="h-12 w-12 text-foreground-muted mx-auto mb-4" />
              <p className="text-foreground-muted">No events found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left p-4 text-sm font-medium text-foreground-muted">
                      Event
                    </th>
                    <th className="text-left p-4 text-sm font-medium text-foreground-muted">
                      Date
                    </th>
                    <th className="text-left p-4 text-sm font-medium text-foreground-muted">
                      Venue
                    </th>
                    <th className="text-left p-4 text-sm font-medium text-foreground-muted">
                      Tickets
                    </th>
                    <th className="text-left p-4 text-sm font-medium text-foreground-muted">
                      Status
                    </th>
                    <th className="text-right p-4 text-sm font-medium text-foreground-muted">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {events.map((event) => (
                    <tr
                      key={event.id}
                      className="border-b border-border last:border-0 hover:bg-background-soft"
                    >
                      <td className="p-4">
                        <div>
                          <p className="font-medium text-foreground">
                            {event.title}
                          </p>
                          <p className="text-sm text-foreground-muted capitalize">
                            {event.category}
                          </p>
                        </div>
                      </td>
                      <td className="p-4">
                        <p className="text-foreground">
                          {formatDate(event.eventDate)}
                        </p>
                      </td>
                      <td className="p-4">
                        <p className="text-foreground">
                          {event.venue?.name || "No venue"}
                        </p>
                        {event.venue?.city && (
                          <p className="text-sm text-foreground-muted">
                            {event.venue.city}
                          </p>
                        )}
                      </td>
                      <td className="p-4">
                        <p className="text-foreground">
                          {event.totalSeats - event.availableSeats} /{" "}
                          {event.totalSeats}
                        </p>
                        <div className="w-20 h-1.5 bg-background-elevated rounded-full mt-1">
                          <div
                            className="h-full bg-primary rounded-full"
                            style={{
                              width: `${
                                event.totalSeats > 0
                                  ? Math.min(
                                      100,
                                      ((event.totalSeats - event.availableSeats) /
                                        event.totalSeats) *
                                        100
                                    )
                                  : 0
                              }%`,
                            }}
                          />
                        </div>
                      </td>
                      <td className="p-4">
                        <span
                          className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                            STATUS_COLORS[event.status]?.bg || "bg-gray-100"
                          } ${STATUS_COLORS[event.status]?.text || "text-gray-800"}`}
                        >
                          {event.status}
                        </span>
                      </td>
                      <td className="p-4">
                        <div className="flex items-center justify-end gap-2">
                          <Link href={`/events/${event.slug}`} target="_blank">
                            <Button variant="ghost" size="sm">
                              <Eye className="h-4 w-4" />
                            </Button>
                          </Link>
                          <Link href={`/admin/events/${event.id}/edit`}>
                            <Button variant="ghost" size="sm">
                              <Edit className="h-4 w-4" />
                            </Button>
                          </Link>
                          {event.status === "draft" && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handlePublish(event.id)}
                            >
                              <CheckCircle className="h-4 w-4 text-success" />
                            </Button>
                          )}
                          {event.status === "published" && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleCancel(event.id)}
                              title="Cancel event"
                            >
                              <XCircle className="h-4 w-4 text-error" />
                            </Button>
                          )}
                          {event.status === "cancelled" && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleReactivate(event.id)}
                              title="Reactivate event (set to draft)"
                            >
                              <RotateCcw className="h-4 w-4 text-success" />
                            </Button>
                          )}
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

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-foreground-muted">
            Showing {(page - 1) * pageSize + 1} to{" "}
            {Math.min(page * pageSize, total)} of {total} events
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
