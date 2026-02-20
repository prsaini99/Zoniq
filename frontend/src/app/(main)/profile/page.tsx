/*
 * Profile page: allows authenticated users to view and edit their profile information,
 * manage email notification preferences, and see account verification status.
 *
 * Key features:
 *   - Displays user avatar (first letter), username, email, full name, phone, and join date.
 *   - Inline editing of full name and phone number via the authApi.updateProfile endpoint.
 *   - Notification preferences (booking confirmations, payment updates, ticket delivery,
 *     event reminders, event updates, marketing) with individual toggle switches.
 *   - Quick links to My Tickets, Wishlist, and Settings pages.
 *   - Account status indicators for email verification, phone verification, and active status.
 *
 * Requires authentication; redirects to /login if not authenticated.
 */

"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  User,
  Mail,
  Phone,
  Calendar,
  Shield,
  Edit2,
  Check,
  X,
  Ticket,
  Heart,
  Settings,
  Bell,
  Loader2,
} from "lucide-react";
import { Button, Input, Card, CardContent, CardHeader, CardTitle } from "@/components/ui";
import { useAuthStore, useUser, useIsAuthenticated } from "@/store/auth";
import { authApi, notificationsApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import type { NotificationPreferences } from "@/types";

export default function ProfilePage() {
  const router = useRouter();
  const user = useUser();
  const isAuthenticated = useIsAuthenticated();
  const { setUser } = useAuthStore();

  // Profile editing state
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Editable form fields (only fullName and phone are editable)
  const [formData, setFormData] = useState({
    fullName: "",
    phone: "",
  });

  // Notification preferences state
  const [notifPrefs, setNotifPrefs] = useState<NotificationPreferences | null>(null);
  const [notifLoading, setNotifLoading] = useState(false);
  // Tracks which specific notification preference is currently being toggled
  const [notifUpdating, setNotifUpdating] = useState<string | null>(null);

  // Fetch notification preferences from the API
  const fetchNotificationPrefs = useCallback(async () => {
    setNotifLoading(true);
    try {
      const prefs = await notificationsApi.getPreferences();
      setNotifPrefs(prefs);
    } catch (err) {
      console.error("Failed to load notification preferences:", err);
    } finally {
      setNotifLoading(false);
    }
  }, []);

  // On mount: redirect if not authenticated, otherwise populate form and fetch preferences
  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login?redirect=/profile");
      return;
    }
    if (user) {
      setFormData({
        fullName: user.fullName || "",
        phone: user.phone || "",
      });
      fetchNotificationPrefs();
    }
  }, [isAuthenticated, user, router, fetchNotificationPrefs]);

  // Toggle a single notification preference on/off via the API
  const handleNotifToggle = async (key: keyof NotificationPreferences) => {
    if (!notifPrefs || notifUpdating) return;

    setNotifUpdating(key);
    try {
      const updated = await notificationsApi.updatePreferences({
        [key]: !notifPrefs[key],
      });
      setNotifPrefs(updated);
    } catch (err) {
      console.error("Failed to update notification preference:", err);
    } finally {
      setNotifUpdating(null);
    }
  };

  // Generic input change handler for editable form fields
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  // Save updated profile fields to the backend
  const handleSave = async () => {
    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const updatedUser = await authApi.updateProfile({
        fullName: formData.fullName || null,
        phone: formData.phone || null,
      });
      setUser(updatedUser);
      setIsEditing(false);
      setSuccess("Profile updated successfully");
      // Auto-dismiss success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update profile");
    } finally {
      setIsLoading(false);
    }
  };

  // Cancel editing and revert form fields to current user data
  const handleCancel = () => {
    if (user) {
      setFormData({
        fullName: user.fullName || "",
        phone: user.phone || "",
      });
    }
    setIsEditing(false);
    setError(null);
  };

  // Loading state while user data is not yet available
  if (!user) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground">My Profile</h1>
          <p className="text-foreground-muted mt-1">
            Manage your account settings and preferences
          </p>
        </div>

        {/* Success/Error Messages */}
        {success && (
          <div className="mb-6 p-4 rounded-lg bg-success/10 text-success flex items-center gap-2">
            <Check className="h-5 w-5" />
            {success}
          </div>
        )}
        {error && (
          <div className="mb-6 p-4 rounded-lg bg-error/10 text-error flex items-center gap-2">
            <X className="h-5 w-5" />
            {error}
          </div>
        )}

        <div className="grid gap-6 md:grid-cols-3">
          {/* Profile Card: avatar, editable fields, and read-only info */}
          <div className="md:col-span-2">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Profile Information</CardTitle>
                {/* Toggle between view and edit modes */}
                {!isEditing ? (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setIsEditing(true)}
                    leftIcon={<Edit2 className="h-4 w-4" />}
                  >
                    Edit
                  </Button>
                ) : (
                  <div className="flex gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleCancel}
                      disabled={isLoading}
                    >
                      Cancel
                    </Button>
                    <Button
                      size="sm"
                      onClick={handleSave}
                      isLoading={isLoading}
                      leftIcon={<Check className="h-4 w-4" />}
                    >
                      Save
                    </Button>
                  </div>
                )}
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Avatar and Name */}
                <div className="flex items-center gap-4">
                  <div className="h-20 w-20 rounded-full bg-primary/20 flex items-center justify-center">
                    <span className="text-2xl font-bold text-primary">
                      {user.username.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold text-foreground">
                      {user.fullName || user.username}
                    </h3>
                    <p className="text-foreground-muted">@{user.username}</p>
                    {/* Admin badge (if applicable) */}
                    {user.role === "admin" && (
                      <span className="inline-flex items-center gap-1 mt-1 px-2 py-0.5 rounded-full text-xs font-medium bg-primary/20 text-primary">
                        <Shield className="h-3 w-3" />
                        Admin
                      </span>
                    )}
                  </div>
                </div>

                {/* Form Fields: read-only username/email, editable fullName/phone */}
                <div className="space-y-4">
                  <div className="grid gap-4 sm:grid-cols-2">
                    {/* Username (read-only) */}
                    <div>
                      <label className="block text-sm font-medium text-foreground-muted mb-1.5">
                        Username
                      </label>
                      <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-background-soft border border-border">
                        <User className="h-4 w-4 text-foreground-muted" />
                        <span className="text-foreground">{user.username}</span>
                      </div>
                    </div>

                    {/* Email (read-only, with verification checkmark) */}
                    <div>
                      <label className="block text-sm font-medium text-foreground-muted mb-1.5">
                        Email
                      </label>
                      <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-background-soft border border-border">
                        <Mail className="h-4 w-4 text-foreground-muted" />
                        <span className="text-foreground">{user.email}</span>
                        {user.isVerified && (
                          <Check className="h-4 w-4 text-success ml-auto" />
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Editable fields: fullName and phone (or read-only when not editing) */}
                  <div className="grid gap-4 sm:grid-cols-2">
                    {isEditing ? (
                      <>
                        <Input
                          label="Full Name"
                          name="fullName"
                          placeholder="Enter your full name"
                          value={formData.fullName}
                          onChange={handleChange}
                          leftIcon={<User className="h-4 w-4" />}
                        />
                        <Input
                          label="Phone Number"
                          name="phone"
                          type="tel"
                          placeholder="Enter your phone number"
                          value={formData.phone}
                          onChange={handleChange}
                          leftIcon={<Phone className="h-4 w-4" />}
                        />
                      </>
                    ) : (
                      <>
                        <div>
                          <label className="block text-sm font-medium text-foreground-muted mb-1.5">
                            Full Name
                          </label>
                          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-background-soft border border-border">
                            <User className="h-4 w-4 text-foreground-muted" />
                            <span className="text-foreground">
                              {user.fullName || "Not set"}
                            </span>
                          </div>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-foreground-muted mb-1.5">
                            Phone Number
                          </label>
                          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-background-soft border border-border">
                            <Phone className="h-4 w-4 text-foreground-muted" />
                            <span className="text-foreground">
                              {user.phone || "Not set"}
                            </span>
                            {user.isPhoneVerified && user.phone && (
                              <Check className="h-4 w-4 text-success ml-auto" />
                            )}
                          </div>
                        </div>
                      </>
                    )}
                  </div>

                  {/* Member since date (read-only) */}
                  <div>
                    <label className="block text-sm font-medium text-foreground-muted mb-1.5">
                      Member Since
                    </label>
                    <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-background-soft border border-border">
                      <Calendar className="h-4 w-4 text-foreground-muted" />
                      <span className="text-foreground">
                        {formatDate(user.createdAt)}
                      </span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar: Quick Links and Account Status */}
          <div className="space-y-4">
            {/* Quick navigation links */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Quick Links</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button
                  variant="ghost"
                  className="w-full justify-start"
                  onClick={() => router.push("/my-tickets")}
                  leftIcon={<Ticket className="h-4 w-4" />}
                >
                  My Tickets
                </Button>
                <Button
                  variant="ghost"
                  className="w-full justify-start"
                  onClick={() => router.push("/wishlist")}
                  leftIcon={<Heart className="h-4 w-4" />}
                >
                  Wishlist
                </Button>
                <Button
                  variant="ghost"
                  className="w-full justify-start"
                  onClick={() => router.push("/settings")}
                  leftIcon={<Settings className="h-4 w-4" />}
                >
                  Settings
                </Button>
              </CardContent>
            </Card>

            {/* Account verification and status indicators */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Account Status</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-foreground-muted">Email</span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full ${
                      user.isVerified
                        ? "bg-success/20 text-success"
                        : "bg-warning/20 text-warning"
                    }`}
                  >
                    {user.isVerified ? "Verified" : "Unverified"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-foreground-muted">Phone</span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full ${
                      user.isPhoneVerified && user.phone
                        ? "bg-success/20 text-success"
                        : "bg-foreground-subtle/20 text-foreground-muted"
                    }`}
                  >
                    {user.isPhoneVerified && user.phone ? "Verified" : "Not set"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-foreground-muted">Account</span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full ${
                      user.isActive
                        ? "bg-success/20 text-success"
                        : "bg-error/20 text-error"
                    }`}
                  >
                    {user.isActive ? "Active" : "Inactive"}
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Notification Preferences: toggle switches for each email notification category */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              Email Notifications
            </CardTitle>
          </CardHeader>
          <CardContent>
            {notifLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-primary" />
              </div>
            ) : notifPrefs ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <NotificationToggle
                  label="Booking Confirmations"
                  description="Receive emails when your booking is confirmed"
                  checked={notifPrefs.emailBookingConfirmation}
                  loading={notifUpdating === "emailBookingConfirmation"}
                  onChange={() => handleNotifToggle("emailBookingConfirmation")}
                />
                <NotificationToggle
                  label="Payment Updates"
                  description="Get notified about payment success or failures"
                  checked={notifPrefs.emailPaymentUpdates}
                  loading={notifUpdating === "emailPaymentUpdates"}
                  onChange={() => handleNotifToggle("emailPaymentUpdates")}
                />
                <NotificationToggle
                  label="Ticket Delivery"
                  description="Receive your e-tickets via email"
                  checked={notifPrefs.emailTicketDelivery}
                  loading={notifUpdating === "emailTicketDelivery"}
                  onChange={() => handleNotifToggle("emailTicketDelivery")}
                />
                <NotificationToggle
                  label="Event Reminders"
                  description="Get reminded before your events start"
                  checked={notifPrefs.emailEventReminders}
                  loading={notifUpdating === "emailEventReminders"}
                  onChange={() => handleNotifToggle("emailEventReminders")}
                />
                <NotificationToggle
                  label="Event Updates"
                  description="Get notified about event changes or cancellations"
                  checked={notifPrefs.emailEventUpdates}
                  loading={notifUpdating === "emailEventUpdates"}
                  onChange={() => handleNotifToggle("emailEventUpdates")}
                />
                <NotificationToggle
                  label="Marketing & Promotions"
                  description="Receive promotional offers and event suggestions"
                  checked={notifPrefs.emailMarketing}
                  loading={notifUpdating === "emailMarketing"}
                  onChange={() => handleNotifToggle("emailMarketing")}
                />
              </div>
            ) : (
              <p className="text-foreground-muted text-center py-4">
                Failed to load notification preferences
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

/*
 * NotificationToggle: a reusable toggle switch component for notification preferences.
 * Renders a label, description, and an accessible toggle button with a loading spinner.
 */
function NotificationToggle({
  label,
  description,
  checked,
  loading,
  onChange,
}: {
  label: string;
  description: string;
  checked: boolean;
  loading: boolean;
  onChange: () => void;
}) {
  return (
    <div className="flex items-start justify-between gap-4 p-3 rounded-lg bg-background-soft">
      <div className="flex-1">
        <p className="font-medium text-foreground text-sm">{label}</p>
        <p className="text-xs text-foreground-muted mt-0.5">{description}</p>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={onChange}
        disabled={loading}
        className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${
          checked ? "bg-primary" : "bg-foreground-subtle"
        }`}
      >
        <span
          className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
            checked ? "translate-x-5" : "translate-x-0"
          }`}
        >
          {loading && (
            <Loader2 className="h-3 w-3 animate-spin text-primary absolute top-1 left-1" />
          )}
        </span>
      </button>
    </div>
  );
}
