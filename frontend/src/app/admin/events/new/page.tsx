/**
 * CreateEventPage - Admin form for creating a new event.
 *
 * Layout:
 * - Left column (2/3): Basic info (title, slug, category, venue, descriptions),
 *   date/time pickers (event start/end, booking window), and organizer details.
 * - Right sidebar (1/3): Settings (max tickets, featured toggle), image URLs,
 *   and the submit button.
 *
 * Key behaviors:
 * - Fetches all venues on mount for the venue dropdown.
 * - Auto-generates a URL slug from the title.
 * - Submits via POST to /admin/events; only sends non-empty optional fields.
 * - On success, redirects to the edit page so the admin can add seat categories.
 * - The event is created in "draft" status.
 */
"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Calendar,
  MapPin,
  Loader2,
  Save,
} from "lucide-react";
import { Button, Card, CardContent } from "@/components/ui";
import api from "@/lib/api";

// Venue dropdown option shape
interface Venue {
  id: number;
  name: string;
  city: string | null;
}

// Shape of the form data managed by local state
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
}

// Available event category options for the select dropdown
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

// Default empty form values
const initialFormData: EventFormData = {
  title: "",
  slug: "",
  category: "concert",
  short_description: "",
  description: "",
  event_date: "",
  event_end_date: "",
  booking_start_date: "",
  booking_end_date: "",
  venue_id: null,
  organizer_name: "",
  organizer_contact: "",
  max_tickets_per_booking: 10,
  is_featured: false,
  banner_image_url: "",
  thumbnail_image_url: "",
};

export default function CreateEventPage() {
  const router = useRouter();
  const [formData, setFormData] = useState<EventFormData>(initialFormData);
  const [venues, setVenues] = useState<Venue[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch all venues on mount for the venue selector
  useEffect(() => {
    const fetchVenues = async () => {
      setIsLoading(true);
      try {
        const res = await api.get("/admin/venues/all");
        setVenues(res.data);
      } catch (err) {
        console.error("Failed to fetch venues:", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchVenues();
  }, []);

  // Auto-generate slug from title (lowercase, hyphens, strip leading/trailing hyphens)
  useEffect(() => {
    if (formData.title) {
      const slug = formData.title
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/(^-|-$)/g, "");
      setFormData((prev) => ({ ...prev, slug }));
    }
  }, [formData.title]);

  // Form submission handler: builds a cleaned payload and POSTs to the admin API
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
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
      };

      // Optional fields - only include if non-empty
      if (formData.short_description) cleanedData.short_description = formData.short_description;
      if (formData.description) cleanedData.description = formData.description;
      if (formData.event_end_date) cleanedData.event_end_date = formData.event_end_date;
      if (formData.venue_id) cleanedData.venue_id = formData.venue_id;
      if (formData.organizer_name) cleanedData.organizer_name = formData.organizer_name;
      if (formData.organizer_contact) cleanedData.organizer_contact = formData.organizer_contact;
      if (formData.is_featured) cleanedData.is_featured = formData.is_featured;
      if (formData.banner_image_url) cleanedData.banner_image_url = formData.banner_image_url;
      if (formData.thumbnail_image_url) cleanedData.thumbnail_image_url = formData.thumbnail_image_url;

      const res = await api.post("/admin/events", cleanedData);
      // Redirect to the edit page so the admin can add seat categories
      router.push(`/admin/events/${res.data.id}/edit`);
    } catch (err: any) {
      setError(err.message || "Failed to create event");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Generic change handler for text inputs, selects, textareas, and checkboxes
  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? (e.target as HTMLInputElement).checked : value,
    }));
  };

  // Show spinner while venues are loading
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header with back navigation */}
      <div className="flex items-center gap-4">
        <Link href="/admin/events">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Events
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-foreground">Create Event</h1>
          <p className="text-foreground-muted">Add a new event to your platform</p>
        </div>
      </div>

      {/* Error Message Banner */}
      {error && (
        <div className="p-4 bg-error/10 border border-error/20 rounded-lg text-error">
          {error}
        </div>
      )}

      {/* Event Creation Form */}
      <form onSubmit={handleSubmit}>
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Main Content Column (left 2/3) */}
          <div className="lg:col-span-2 space-y-6">
            {/* Basic Information Section */}
            <Card>
              <CardContent className="p-6 space-y-4">
                <h2 className="text-lg font-semibold text-foreground">Basic Information</h2>

                {/* Event Title (required) */}
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
                    placeholder="Enter event title"
                  />
                </div>

                {/* URL Slug (auto-generated from title, editable) */}
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
                    placeholder="event-url-slug"
                  />
                  <p className="text-xs text-foreground-muted mt-1">
                    Auto-generated from title. Used in event URL.
                  </p>
                </div>

                {/* Category and Venue selectors side by side */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      Category *
                    </label>
                    <select
                      name="category"
                      required
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

                  {/* Venue selector populated from the fetched venues list */}
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      Venue
                    </label>
                    <select
                      name="venue_id"
                      value={formData.venue_id || ""}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          venue_id: e.target.value ? parseInt(e.target.value) : null,
                        }))
                      }
                      className="w-full px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                    >
                      <option value="">Select a venue</option>
                      {venues.map((venue) => (
                        <option key={venue.id} value={venue.id}>
                          {venue.name} {venue.city ? `(${venue.city})` : ""}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Short Description (for event cards) */}
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
                    placeholder="Brief description for event cards"
                  />
                </div>

                {/* Full Description */}
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
                    placeholder="Detailed event description"
                  />
                </div>
              </CardContent>
            </Card>

            {/* Date & Time Section */}
            <Card>
              <CardContent className="p-6 space-y-4">
                <h2 className="text-lg font-semibold text-foreground">Date & Time</h2>

                {/* Event start and end datetime pickers */}
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

                {/* Booking window start and end datetime pickers */}
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

            {/* Organizer Details Section */}
            <Card>
              <CardContent className="p-6 space-y-4">
                <h2 className="text-lg font-semibold text-foreground">Organizer Details</h2>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      Organizer Name
                    </label>
                    <input
                      type="text"
                      name="organizer_name"
                      value={formData.organizer_name}
                      onChange={handleChange}
                      className="w-full px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                      placeholder="Event organizer name"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      Organizer Contact
                    </label>
                    <input
                      type="text"
                      name="organizer_contact"
                      value={formData.organizer_contact}
                      onChange={handleChange}
                      className="w-full px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                      placeholder="Phone or email"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar Column (right 1/3) */}
          <div className="space-y-6">
            {/* Settings Card: max tickets per booking and featured toggle */}
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

            {/* Images Card: banner and thumbnail URL inputs */}
            <Card>
              <CardContent className="p-6 space-y-4">
                <h2 className="text-lg font-semibold text-foreground">Images</h2>

                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Banner Image URL
                  </label>
                  <input
                    type="url"
                    name="banner_image_url"
                    value={formData.banner_image_url}
                    onChange={handleChange}
                    className="w-full px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                    placeholder="https://..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Thumbnail Image URL
                  </label>
                  <input
                    type="url"
                    name="thumbnail_image_url"
                    value={formData.thumbnail_image_url}
                    onChange={handleChange}
                    className="w-full px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                    placeholder="https://..."
                  />
                </div>
              </CardContent>
            </Card>

            {/* Submit Actions Card */}
            <Card>
              <CardContent className="p-6 space-y-3">
                <Button
                  type="submit"
                  className="w-full"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  ) : (
                    <Save className="h-4 w-4 mr-2" />
                  )}
                  Create Event
                </Button>
                <p className="text-xs text-foreground-muted text-center">
                  Event will be created as Draft. You can add seat categories and publish later.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </form>
    </div>
  );
}
