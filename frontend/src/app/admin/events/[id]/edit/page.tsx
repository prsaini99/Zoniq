"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Loader2,
  Save,
  Plus,
  Trash2,
  CheckCircle,
  XCircle,
} from "lucide-react";
import { Button, Card, CardContent } from "@/components/ui";
import api from "@/lib/api";

interface Venue {
  id: number;
  name: string;
  city: string | null;
}

interface SeatCategory {
  id: number;
  name: string;
  price: number;
  totalSeats: number;
  availableSeats: number;
  color: string;
}

interface EventData {
  id: number;
  title: string;
  slug: string;
  category: string;
  status: string;
  shortDescription: string | null;
  description: string | null;
  eventDate: string;
  eventEndDate: string | null;
  bookingStartDate: string | null;
  bookingEndDate: string | null;
  venueId: number | null;
  organizerName: string | null;
  organizerContact: string | null;
  maxTicketsPerBooking: number;
  isFeatured: boolean;
  bannerImageUrl: string | null;
  thumbnailImageUrl: string | null;
  seatCategories: SeatCategory[];
  // Queue settings
  queueEnabled: boolean;
  queueBatchSize: number | null;
  queueProcessingMinutes: number | null;
}

interface EventFormData {
  title: string;
  slug: string;
  category: string;
  short_description: string;
  description: string;
  event_date: string;
  event_end_date: string;
  booking_start_date: string;
  booking_end_date: string;
  venue_id: number | null;
  organizer_name: string;
  organizer_contact: string;
  max_tickets_per_booking: number;
  is_featured: boolean;
  banner_image_url: string;
  thumbnail_image_url: string;
  // Queue settings
  queue_enabled: boolean;
  queue_batch_size: number;
  queue_processing_minutes: number;
}

interface CategoryFormData {
  name: string;
  price: number;
  total_seats: number;
  color_code: string;
}

const CATEGORIES = [
  { value: "concert", label: "Concert" },
  { value: "sports", label: "Sports" },
  { value: "theater", label: "Theater" },
  { value: "comedy", label: "Comedy" },
  { value: "festival", label: "Festival" },
  { value: "conference", label: "Conference" },
  { value: "exhibition", label: "Exhibition" },
  { value: "workshop", label: "Workshop" },
  { value: "other", label: "Other" },
];

const COLORS = [
  { value: "#FFD700", label: "Gold" },
  { value: "#C0C0C0", label: "Silver" },
  { value: "#CD7F32", label: "Bronze" },
  { value: "#4169E1", label: "Blue" },
  { value: "#32CD32", label: "Green" },
  { value: "#FF6347", label: "Red" },
  { value: "#9370DB", label: "Purple" },
];

function formatDateForInput(dateStr: string | null): string {
  if (!dateStr) return "";
  try {
    const date = new Date(dateStr);
    return date.toISOString().slice(0, 16);
  } catch {
    return "";
  }
}

export default function EditEventPage() {
  const router = useRouter();
  const params = useParams();
  const eventId = params.id as string;

  const [event, setEvent] = useState<EventData | null>(null);
  const [formData, setFormData] = useState<EventFormData | null>(null);
  const [venues, setVenues] = useState<Venue[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"details" | "categories">("details");

  // Category form state
  const [showCategoryForm, setShowCategoryForm] = useState(false);
  const [categoryForm, setCategoryForm] = useState<CategoryFormData>({
    name: "",
    price: 0,
    total_seats: 0,
    color_code: "#4169E1",
  });
  const [isCategorySubmitting, setIsCategorySubmitting] = useState(false);
  const [seatCategories, setSeatCategories] = useState<SeatCategory[]>([]);

  const fetchEvent = useCallback(async () => {
    try {
      const res = await api.get(`/admin/events/${eventId}`);
      const data = res.data;
      setEvent(data);
      setFormData({
        title: data.title,
        slug: data.slug,
        category: data.category,
        short_description: data.shortDescription || "",
        description: data.description || "",
        event_date: formatDateForInput(data.eventDate),
        event_end_date: formatDateForInput(data.eventEndDate),
        booking_start_date: formatDateForInput(data.bookingStartDate),
        booking_end_date: formatDateForInput(data.bookingEndDate),
        venue_id: data.venueId,
        organizer_name: data.organizerName || "",
        organizer_contact: data.organizerContact || "",
        max_tickets_per_booking: data.maxTicketsPerBooking,
        is_featured: data.isFeatured,
        banner_image_url: data.bannerImageUrl || "",
        thumbnail_image_url: data.thumbnailImageUrl || "",
        // Queue settings
        queue_enabled: data.queueEnabled || false,
        queue_batch_size: data.queueBatchSize || 50,
        queue_processing_minutes: data.queueProcessingMinutes || 10,
      });
    } catch (err: any) {
      setError(err.message || "Failed to load event");
    }
  }, [eventId]);

  const fetchCategories = useCallback(async () => {
    try {
      const res = await api.get(`/admin/events/${eventId}/categories`);
      // Transform from API response (camelCase) to frontend format
      const categories = res.data.map((cat: any) => ({
        id: cat.id,
        name: cat.name,
        price: cat.price,
        totalSeats: cat.totalSeats,
        availableSeats: cat.availableSeats,
        color: cat.colorCode || "#4169E1",
      }));
      setSeatCategories(categories);
    } catch (err) {
      console.error("Failed to fetch categories:", err);
    }
  }, [eventId]);

  useEffect(() => {
    const init = async () => {
      setIsLoading(true);
      try {
        const [_, venuesRes, __] = await Promise.all([
          fetchEvent(),
          api.get("/admin/venues/all"),
          fetchCategories(),
        ]);
        setVenues(venuesRes.data);
      } catch (err) {
        console.error("Failed to load data:", err);
      } finally {
        setIsLoading(false);
      }
    };
    init();
  }, [fetchEvent, fetchCategories]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData) return;

    setIsSubmitting(true);
    setError(null);

    try {
      // Required fields
      const cleanedData: Record<string, any> = {
        title: formData.title,
        slug: formData.slug,
        category: formData.category,
        event_date: formData.event_date,
        booking_start_date: formData.booking_start_date,
        booking_end_date: formData.booking_end_date,
        max_tickets_per_booking: formData.max_tickets_per_booking,
        is_featured: formData.is_featured,
        // Queue settings
        queue_enabled: formData.queue_enabled,
        queue_batch_size: formData.queue_batch_size,
        queue_processing_minutes: formData.queue_processing_minutes,
      };

      // Optional fields - only include if non-empty
      if (formData.short_description) cleanedData.short_description = formData.short_description;
      if (formData.description) cleanedData.description = formData.description;
      if (formData.event_end_date) cleanedData.event_end_date = formData.event_end_date;
      if (formData.venue_id) cleanedData.venue_id = formData.venue_id;
      if (formData.organizer_name) cleanedData.organizer_name = formData.organizer_name;
      if (formData.organizer_contact) cleanedData.organizer_contact = formData.organizer_contact;
      if (formData.banner_image_url) cleanedData.banner_image_url = formData.banner_image_url;
      if (formData.thumbnail_image_url) cleanedData.thumbnail_image_url = formData.thumbnail_image_url;

      await api.patch(`/admin/events/${eventId}`, cleanedData);
      await fetchEvent();
      setError(null);
      alert("Event updated successfully!");
    } catch (err: any) {
      setError(err.message || "Failed to update event");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;
    setFormData((prev) =>
      prev
        ? {
            ...prev,
            [name]: type === "checkbox" ? (e.target as HTMLInputElement).checked : value,
          }
        : prev
    );
  };

  const handlePublish = async () => {
    try {
      await api.post(`/admin/events/${eventId}/publish`);
      await fetchEvent();
    } catch (err: any) {
      alert(err.message || "Failed to publish event");
    }
  };

  const handleCancel = async () => {
    if (!confirm("Are you sure you want to cancel this event?")) return;
    try {
      await api.post(`/admin/events/${eventId}/cancel`);
      await fetchEvent();
    } catch (err: any) {
      alert(err.message || "Failed to cancel event");
    }
  };

  const handleReactivate = async () => {
    if (!confirm("Reactivate this event? It will be set to draft status.")) return;
    try {
      await api.post(`/admin/events/${eventId}/reactivate`);
      await fetchEvent();
    } catch (err: any) {
      alert(err.message || "Failed to reactivate event");
    }
  };

  const handleAddCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsCategorySubmitting(true);
    try {
      await api.post(`/admin/events/${eventId}/categories`, categoryForm);
      await fetchCategories();
      await fetchEvent(); // Refresh event to update seat counts
      setShowCategoryForm(false);
      setCategoryForm({ name: "", price: 0, total_seats: 0, color_code: "#4169E1" });
    } catch (err: any) {
      alert(err.message || "Failed to add category");
    } finally {
      setIsCategorySubmitting(false);
    }
  };

  const handleDeleteCategory = async (categoryId: number) => {
    if (!confirm("Are you sure you want to delete this category?")) return;
    try {
      // Note: The delete endpoint is at /admin/events/categories/{categoryId}
      await api.delete(`/admin/events/categories/${categoryId}`);
      await fetchCategories();
      await fetchEvent(); // Refresh event to update seat counts
    } catch (err: any) {
      alert(err.message || "Failed to delete category");
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!event || !formData) {
    return (
      <div className="text-center py-12">
        <p className="text-error">Event not found</p>
        <Link href="/admin/events">
          <Button className="mt-4">Back to Events</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/admin/events">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-foreground">{event.title}</h1>
            <p className="text-foreground-muted">Edit event details and manage categories</p>
          </div>
        </div>
        <div className="flex gap-2">
          {event.status === "draft" && (
            <Button onClick={handlePublish} className="bg-success hover:bg-success/90">
              <CheckCircle className="h-4 w-4 mr-2" />
              Publish
            </Button>
          )}
          {event.status === "published" && (
            <Button onClick={handleCancel} variant="outline" className="text-error border-error">
              <XCircle className="h-4 w-4 mr-2" />
              Cancel Event
            </Button>
          )}
          {event.status === "cancelled" && (
            <Button onClick={handleReactivate} className="bg-success hover:bg-success/90">
              <CheckCircle className="h-4 w-4 mr-2" />
              Reactivate
            </Button>
          )}
        </div>
      </div>

      {/* Status Badge */}
      <div className="flex items-center gap-4">
        <span
          className={`px-3 py-1 rounded-full text-sm font-medium ${
            event.status === "published"
              ? "bg-success/20 text-success"
              : event.status === "draft"
              ? "bg-foreground-muted/20 text-foreground-muted"
              : event.status === "cancelled"
              ? "bg-error/20 text-error"
              : "bg-primary/20 text-primary"
          }`}
        >
          {event.status.toUpperCase()}
        </span>
        <span className="text-foreground-muted">
          {seatCategories.length} seat categories
        </span>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-4 bg-error/10 border border-error/20 rounded-lg text-error">
          {error}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-4 border-b border-border">
        <button
          onClick={() => setActiveTab("details")}
          className={`pb-3 px-1 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "details"
              ? "border-primary text-primary"
              : "border-transparent text-foreground-muted hover:text-foreground"
          }`}
        >
          Event Details
        </button>
        <button
          onClick={() => setActiveTab("categories")}
          className={`pb-3 px-1 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "categories"
              ? "border-primary text-primary"
              : "border-transparent text-foreground-muted hover:text-foreground"
          }`}
        >
          Seat Categories
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === "details" ? (
        <form onSubmit={handleSubmit}>
          <div className="grid gap-6 lg:grid-cols-3">
            {/* Main Content */}
            <div className="lg:col-span-2 space-y-6">
              <Card>
                <CardContent className="p-6 space-y-4">
                  <h2 className="text-lg font-semibold text-foreground">Basic Information</h2>

                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      Event Title *
                    </label>
                    <input
                      type="text"
                      name="title"
                      required
                      value={formData.title}
                      onChange={handleChange}
                      className="w-full px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      URL Slug
                    </label>
                    <input
                      type="text"
                      name="slug"
                      value={formData.slug}
                      onChange={handleChange}
                      className="w-full px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-1">
                        Category
                      </label>
                      <select
                        name="category"
                        value={formData.category}
                        onChange={handleChange}
                        className="w-full px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                      >
                        {CATEGORIES.map((cat) => (
                          <option key={cat.value} value={cat.value}>
                            {cat.label}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-foreground mb-1">
                        Venue
                      </label>
                      <select
                        name="venue_id"
                        value={formData.venue_id || ""}
                        onChange={(e) =>
                          setFormData((prev) =>
                            prev
                              ? {
                                  ...prev,
                                  venue_id: e.target.value ? parseInt(e.target.value) : null,
                                }
                              : prev
                          )
                        }
                        className="w-full px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                      >
                        <option value="">Select a venue</option>
                        {venues.map((venue) => (
                          <option key={venue.id} value={venue.id}>
                            {venue.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      Short Description
                    </label>
                    <textarea
                      name="short_description"
                      value={formData.short_description}
                      onChange={handleChange}
                      rows={2}
                      className="w-full px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      Full Description
                    </label>
                    <textarea
                      name="description"
                      value={formData.description}
                      onChange={handleChange}
                      rows={5}
                      className="w-full px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                    />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6 space-y-4">
                  <h2 className="text-lg font-semibold text-foreground">Date & Time</h2>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-1">
                        Event Start Date & Time *
                      </label>
                      <input
                        type="datetime-local"
                        name="event_date"
                        required
                        value={formData.event_date}
                        onChange={handleChange}
                        className="w-full px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-foreground mb-1">
                        Event End Date & Time
                      </label>
                      <input
                        type="datetime-local"
                        name="event_end_date"
                        value={formData.event_end_date}
                        onChange={handleChange}
                        className="w-full px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-1">
                        Booking Start Date & Time *
                      </label>
                      <input
                        type="datetime-local"
                        name="booking_start_date"
                        required
                        value={formData.booking_start_date}
                        onChange={handleChange}
                        className="w-full px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-foreground mb-1">
                        Booking End Date & Time *
                      </label>
                      <input
                        type="datetime-local"
                        name="booking_end_date"
                        required
                        value={formData.booking_end_date}
                        onChange={handleChange}
                        className="w-full px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              <Card>
                <CardContent className="p-6 space-y-4">
                  <h2 className="text-lg font-semibold text-foreground">Settings</h2>

                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      Max Tickets Per Booking
                    </label>
                    <input
                      type="number"
                      name="max_tickets_per_booking"
                      min="1"
                      value={formData.max_tickets_per_booking}
                      onChange={handleChange}
                      className="w-full px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                    />
                  </div>

                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      name="is_featured"
                      id="is_featured"
                      checked={formData.is_featured}
                      onChange={handleChange}
                      className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                    />
                    <label htmlFor="is_featured" className="text-sm text-foreground">
                      Featured Event
                    </label>
                  </div>
                </CardContent>
              </Card>

              {/* Queue Settings */}
              <Card>
                <CardContent className="p-6 space-y-4">
                  <h2 className="text-lg font-semibold text-foreground">Queue Settings</h2>
                  <p className="text-sm text-foreground-muted">
                    Enable virtual queue for high-demand events
                  </p>

                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      name="queue_enabled"
                      id="queue_enabled"
                      checked={formData.queue_enabled}
                      onChange={handleChange}
                      className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                    />
                    <label htmlFor="queue_enabled" className="text-sm text-foreground">
                      Enable Queue System
                    </label>
                  </div>

                  {formData.queue_enabled && (
                    <>
                      <div>
                        <label className="block text-sm font-medium text-foreground mb-1">
                          Batch Size
                        </label>
                        <input
                          type="number"
                          name="queue_batch_size"
                          min="1"
                          max="500"
                          value={formData.queue_batch_size}
                          onChange={handleChange}
                          className="w-full px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                        />
                        <p className="text-xs text-foreground-muted mt-1">
                          Users processed per batch (default: 50)
                        </p>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-foreground mb-1">
                          Processing Time (minutes)
                        </label>
                        <input
                          type="number"
                          name="queue_processing_minutes"
                          min="1"
                          max="60"
                          value={formData.queue_processing_minutes}
                          onChange={handleChange}
                          className="w-full px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                        />
                        <p className="text-xs text-foreground-muted mt-1">
                          Time allowed to complete booking (default: 10)
                        </p>
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6 space-y-3">
                  <Button type="submit" className="w-full" disabled={isSubmitting}>
                    {isSubmitting ? (
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    ) : (
                      <Save className="h-4 w-4 mr-2" />
                    )}
                    Save Changes
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>
        </form>
      ) : (
        <div className="space-y-6">
          {/* Add Category Button */}
          <div className="flex justify-end">
            <Button onClick={() => setShowCategoryForm(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add Seat Category
            </Button>
          </div>

          {/* Category Form Modal */}
          {showCategoryForm && (
            <Card>
              <CardContent className="p-6">
                <h3 className="text-lg font-semibold text-foreground mb-4">Add Seat Category</h3>
                <form onSubmit={handleAddCategory} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-1">
                        Category Name *
                      </label>
                      <input
                        type="text"
                        required
                        value={categoryForm.name}
                        onChange={(e) =>
                          setCategoryForm({ ...categoryForm, name: e.target.value })
                        }
                        className="w-full px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                        placeholder="e.g., VIP, Standard"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-1">
                        Color
                      </label>
                      <select
                        value={categoryForm.color_code}
                        onChange={(e) =>
                          setCategoryForm({ ...categoryForm, color_code: e.target.value })
                        }
                        className="w-full px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                      >
                        {COLORS.map((color) => (
                          <option key={color.value} value={color.value}>
                            {color.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-1">
                        Price (INR) *
                      </label>
                      <input
                        type="number"
                        required
                        min="0"
                        value={categoryForm.price}
                        onChange={(e) =>
                          setCategoryForm({ ...categoryForm, price: parseFloat(e.target.value) || 0 })
                        }
                        className="w-full px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-1">
                        Total Seats *
                      </label>
                      <input
                        type="number"
                        required
                        min="1"
                        value={categoryForm.total_seats}
                        onChange={(e) =>
                          setCategoryForm({ ...categoryForm, total_seats: parseInt(e.target.value) || 0 })
                        }
                        className="w-full px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                      />
                    </div>
                  </div>

                  <div className="flex gap-3">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => setShowCategoryForm(false)}
                    >
                      Cancel
                    </Button>
                    <Button type="submit" disabled={isCategorySubmitting}>
                      {isCategorySubmitting && (
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      )}
                      Add Category
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          )}

          {/* Categories List */}
          {seatCategories && seatCategories.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {seatCategories.map((category) => (
                <Card key={category.id}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-4 h-4 rounded-full"
                          style={{ backgroundColor: category.color }}
                        />
                        <h3 className="font-semibold text-foreground">{category.name}</h3>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteCategory(category.id)}
                        className="text-error hover:text-error"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>

                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-foreground-muted">Price</span>
                        <span className="font-medium text-foreground">
                          Rs. {category.price.toLocaleString()}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-foreground-muted">Total Seats</span>
                        <span className="font-medium text-foreground">{category.totalSeats}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-foreground-muted">Available</span>
                        <span className="font-medium text-success">{category.availableSeats}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="p-12 text-center">
                <p className="text-foreground-muted mb-4">No seat categories yet</p>
                <Button onClick={() => setShowCategoryForm(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Add First Category
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
