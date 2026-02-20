/**
 * AdminVenuesPage - CRUD management page for event venues.
 *
 * Features:
 * - Summary stats: total venues, active count, combined capacity.
 * - Search by venue name, filter by city, filter by active/inactive.
 * - Grid of venue cards showing name, location, capacity, and active status.
 * - Inline edit and delete buttons per card.
 * - Modal form for creating a new venue or editing an existing one.
 *   The modal includes fields for name, address, city, state, country,
 *   pincode, capacity, contact phone, contact email, and an active toggle.
 * - Paginated navigation.
 *
 * Data is fetched from /admin/venues with search/filter/pagination params.
 */
"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Plus,
  Search,
  MapPin,
  Loader2,
  Edit,
  Trash2,
  Eye,
  Building,
} from "lucide-react";
import { Button, Card, CardContent } from "@/components/ui";
import api from "@/lib/api";

// Full venue shape as returned by the API
interface Venue {
  id: number;
  name: string;
  address: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
  pincode: string | null;
  capacity: number | null;
  contactPhone: string | null;
  contactEmail: string | null;
  isActive: boolean;
  createdAt: string;
}

// Form data shape used for both creating and editing venues (snake_case for API)
interface VenueFormData {
  name: string;
  address: string;
  city: string;
  state: string;
  country: string;
  pincode: string;
  capacity: number;
  contact_phone: string;
  contact_email: string;
  is_active: boolean;
}

// Default empty form state
const initialFormData: VenueFormData = {
  name: "",
  address: "",
  city: "",
  state: "",
  country: "India",
  pincode: "",
  capacity: 0,
  contact_phone: "",
  contact_email: "",
  is_active: true,
};

export default function AdminVenuesPage() {
  // Venues list state
  const [venues, setVenues] = useState<Venue[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  // Search and filter state
  const [search, setSearch] = useState("");
  const [cityFilter, setCityFilter] = useState("");
  const [activeFilter, setActiveFilter] = useState<string>("");
  // Pagination
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  // Modal and form state
  const [showModal, setShowModal] = useState(false);
  const [editingVenue, setEditingVenue] = useState<Venue | null>(null);
  const [formData, setFormData] = useState<VenueFormData>(initialFormData);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const pageSize = 20;

  // Fetch venues from API with current search/filter/pagination params
  const fetchVenues = useCallback(async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      });
      if (search) params.append("search", search);
      if (cityFilter) params.append("city", cityFilter);
      if (activeFilter) params.append("is_active", activeFilter);

      const res = await api.get(`/admin/venues?${params}`);
      setVenues(res.data.venues);
      setTotal(res.data.total);
    } catch (err) {
      console.error("Failed to fetch venues:", err);
    } finally {
      setIsLoading(false);
    }
  }, [page, search, cityFilter, activeFilter]);

  // Re-fetch when filters/page change
  useEffect(() => {
    fetchVenues();
  }, [fetchVenues]);

  // Open the modal in "create" mode with a blank form
  const handleOpenCreate = () => {
    setEditingVenue(null);
    setFormData(initialFormData);
    setShowModal(true);
  };

  // Open the modal in "edit" mode, pre-populated with the selected venue's data
  const handleOpenEdit = (venue: Venue) => {
    setEditingVenue(venue);
    setFormData({
      name: venue.name,
      address: venue.address || "",
      city: venue.city || "",
      state: venue.state || "",
      country: venue.country || "India",
      pincode: venue.pincode || "",
      capacity: venue.capacity || 0,
      contact_phone: venue.contactPhone || "",
      contact_email: venue.contactEmail || "",
      is_active: venue.isActive,
    });
    setShowModal(true);
  };

  // Handle form submission for both create (POST) and edit (PATCH)
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      // Clean form data - convert empty strings to null for optional fields
      const cleanedData: Record<string, any> = {
        name: formData.name,
      };

      // Only include non-empty optional fields
      if (formData.address) cleanedData.address = formData.address;
      if (formData.city) cleanedData.city = formData.city;
      if (formData.state) cleanedData.state = formData.state;
      if (formData.country) cleanedData.country = formData.country;
      if (formData.pincode) cleanedData.pincode = formData.pincode;
      if (formData.capacity > 0) cleanedData.capacity = formData.capacity;
      if (formData.contact_phone) cleanedData.contact_phone = formData.contact_phone;
      if (formData.contact_email) cleanedData.contact_email = formData.contact_email;

      if (editingVenue) {
        // Include is_active status when editing
        cleanedData.is_active = formData.is_active;
        await api.patch(`/admin/venues/${editingVenue.id}`, cleanedData);
      } else {
        await api.post("/admin/venues", cleanedData);
      }
      setShowModal(false);
      fetchVenues();
    } catch (err: any) {
      alert(err.message || "Failed to save venue");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Delete (deactivate) a venue after user confirmation
  const handleDelete = async (venueId: number) => {
    if (!confirm("Are you sure you want to deactivate this venue?")) return;
    try {
      await api.delete(`/admin/venues/${venueId}`);
      fetchVenues();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to delete venue");
    }
  };

  const totalPages = Math.ceil(total / pageSize);

  // Derive unique city names from the loaded venues for the city filter dropdown
  const uniqueCities = [...new Set(venues.map((v) => v.city).filter(Boolean))];

  return (
    <div className="space-y-6">
      {/* Page Header with "Add Venue" CTA */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Venues</h1>
          <p className="text-foreground-muted">
            Manage event venues and locations
          </p>
        </div>
        <Button
          leftIcon={<Plus className="h-4 w-4" />}
          onClick={handleOpenCreate}
        >
          Add Venue
        </Button>
      </div>

      {/* Summary Stats: total venues, active count, combined capacity */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-foreground">{total}</p>
            <p className="text-sm text-foreground-muted">Total Venues</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-success">
              {venues.filter((v) => v.isActive).length}
            </p>
            <p className="text-sm text-foreground-muted">Active</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-foreground">
              {venues.reduce((sum, v) => sum + (v.capacity || 0), 0).toLocaleString()}
            </p>
            <p className="text-sm text-foreground-muted">Total Capacity</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters: search, city dropdown, active/inactive dropdown */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-foreground-muted" />
              <input
                type="text"
                placeholder="Search venues..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
                className="w-full pl-10 pr-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>
            {/* City filter populated from unique cities in the venues list */}
            <select
              value={cityFilter}
              onChange={(e) => {
                setCityFilter(e.target.value);
                setPage(1);
              }}
              className="px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
            >
              <option value="">All Cities</option>
              {uniqueCities.map((city) => (
                <option key={city} value={city || ""}>
                  {city}
                </option>
              ))}
            </select>
            {/* Active status filter */}
            <select
              value={activeFilter}
              onChange={(e) => {
                setActiveFilter(e.target.value);
                setPage(1);
              }}
              className="px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
            >
              <option value="">All Status</option>
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Venues Grid - responsive card layout */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : venues.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <Building className="h-12 w-12 text-foreground-muted mx-auto mb-4" />
            <p className="text-foreground-muted">No venues found</p>
            <Button className="mt-4" onClick={handleOpenCreate}>
              Add Your First Venue
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {venues.map((venue) => (
            // Inactive venues are visually dimmed
            <Card key={venue.id} className={!venue.isActive ? "opacity-60" : ""}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <MapPin className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-foreground">
                        {venue.name}
                      </h3>
                      {venue.city && (
                        <p className="text-sm text-foreground-muted">
                          {venue.city}, {venue.state}
                        </p>
                      )}
                    </div>
                  </div>
                  {/* Active / Inactive status badge */}
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-medium ${
                      venue.isActive
                        ? "bg-success/20 text-success"
                        : "bg-foreground-muted/20 text-foreground-muted"
                    }`}
                  >
                    {venue.isActive ? "Active" : "Inactive"}
                  </span>
                </div>

                {/* Venue address (truncated to 2 lines) */}
                {venue.address && (
                  <p className="text-sm text-foreground-muted mb-2 line-clamp-2">
                    {venue.address}
                  </p>
                )}

                {/* Capacity info */}
                <div className="flex items-center gap-4 text-sm text-foreground-muted mb-4">
                  {venue.capacity && (
                    <span>Capacity: {venue.capacity.toLocaleString()}</span>
                  )}
                </div>

                {/* Action buttons: edit and delete */}
                <div className="flex items-center gap-2 pt-3 border-t border-border">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleOpenEdit(venue)}
                    className="flex-1"
                  >
                    <Edit className="h-4 w-4 mr-1" />
                    Edit
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(venue.id)}
                    className="text-error hover:text-error"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-foreground-muted">
            Showing {(page - 1) * pageSize + 1} to{" "}
            {Math.min(page * pageSize, total)} of {total} venues
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

      {/* Create / Edit Venue Modal Overlay */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-background rounded-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
            {/* Modal header */}
            <div className="p-6 border-b border-border">
              <h2 className="text-xl font-bold text-foreground">
                {editingVenue ? "Edit Venue" : "Add New Venue"}
              </h2>
            </div>
            {/* Venue form */}
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              {/* Venue Name (required) */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Venue Name *
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  className="w-full px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                  placeholder="Enter venue name"
                />
              </div>

              {/* Address textarea */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Address
                </label>
                <textarea
                  value={formData.address}
                  onChange={(e) =>
                    setFormData({ ...formData, address: e.target.value })
                  }
                  className="w-full px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                  rows={2}
                  placeholder="Full address"
                />
              </div>

              {/* City and State */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    City
                  </label>
                  <input
                    type="text"
                    value={formData.city}
                    onChange={(e) =>
                      setFormData({ ...formData, city: e.target.value })
                    }
                    className="w-full px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                    placeholder="City"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    State
                  </label>
                  <input
                    type="text"
                    value={formData.state}
                    onChange={(e) =>
                      setFormData({ ...formData, state: e.target.value })
                    }
                    className="w-full px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                    placeholder="State"
                  />
                </div>
              </div>

              {/* Country and Pincode */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Country
                  </label>
                  <input
                    type="text"
                    value={formData.country}
                    onChange={(e) =>
                      setFormData({ ...formData, country: e.target.value })
                    }
                    className="w-full px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                    placeholder="Country"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Pincode
                  </label>
                  <input
                    type="text"
                    value={formData.pincode}
                    onChange={(e) =>
                      setFormData({ ...formData, pincode: e.target.value })
                    }
                    className="w-full px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                    placeholder="Pincode"
                  />
                </div>
              </div>

              {/* Capacity */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Capacity
                </label>
                <input
                  type="number"
                  value={formData.capacity || ""}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      capacity: parseInt(e.target.value) || 0,
                    })
                  }
                  className="w-full px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                  placeholder="Total seating capacity"
                />
              </div>

              {/* Contact Phone and Email */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Contact Phone
                  </label>
                  <input
                    type="tel"
                    value={formData.contact_phone}
                    onChange={(e) =>
                      setFormData({ ...formData, contact_phone: e.target.value })
                    }
                    className="w-full px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                    placeholder="Phone number"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Contact Email
                  </label>
                  <input
                    type="email"
                    value={formData.contact_email}
                    onChange={(e) =>
                      setFormData({ ...formData, contact_email: e.target.value })
                    }
                    className="w-full px-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                    placeholder="Email address"
                  />
                </div>
              </div>

              {/* Active Status Toggle - Only shown when editing an existing venue */}
              {editingVenue && (
                <div className="flex items-center justify-between p-4 bg-background-elevated rounded-lg border border-border">
                  <div>
                    <label className="block text-sm font-medium text-foreground">
                      Venue Status
                    </label>
                    <p className="text-xs text-foreground-muted">
                      Inactive venues won&apos;t be available for new events
                    </p>
                  </div>
                  {/* Custom toggle switch */}
                  <button
                    type="button"
                    onClick={() =>
                      setFormData({ ...formData, is_active: !formData.is_active })
                    }
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      formData.is_active ? "bg-success" : "bg-foreground-muted/30"
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        formData.is_active ? "translate-x-6" : "translate-x-1"
                      }`}
                    />
                  </button>
                </div>
              )}

              {/* Modal action buttons: cancel and submit */}
              <div className="flex gap-3 pt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowModal(false)}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button type="submit" className="flex-1" disabled={isSubmitting}>
                  {isSubmitting ? (
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  ) : null}
                  {editingVenue ? "Update Venue" : "Create Venue"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
