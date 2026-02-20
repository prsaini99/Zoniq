/*
 * api.ts — Centralized API client for the Zoniq frontend.
 * Configures an Axios instance with auth token injection, automatic error
 * handling, and snake_case-to-camelCase response transformations.
 * Exports domain-specific API modules for auth, events, bookings, payments,
 * cart, wishlist, notifications, queue, tickets, and admin operations.
 */

import axios, { AxiosError, AxiosInstance } from "axios";
import Cookies from "js-cookie";
import type {
  AuthResponse,
  SignUpRequest,
  SignInRequest,
  OTPSendResponse,
  EmailOTPSendRequest,
  EmailOTPVerifyRequest,
  User,
  Event,
  EventDetail,
  EventListResponse,
  SeatCategory,
  EventSeatsResponse,
  Venue,
  Booking,
  BookingDetail,
  BookingListResponse,
  Cart,
  CartValidation,
  WishlistItem,
  WishlistResponse,
  CreatePaymentOrderResponse,
  VerifyPaymentResponse,
  PaymentStatusResponse,
  TicketDetail,
  NotificationPreferences,
  NotificationPreferencesUpdate,
  QueueJoinResponse,
  QueuePositionResponse,
  QueueStatusResponse,
  QueueLeaveResponse,
} from "@/types";

// Base URL for all API requests, defaults to local dev server
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

// Cookie key used to persist the JWT auth token
const TOKEN_KEY = "zoniq_token";

// Create axios instance with default JSON content-type header
const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor: attaches the Bearer token from cookies to every outgoing request
api.interceptors.request.use(
  (config) => {
    const token = Cookies.get(TOKEN_KEY);
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: handles 401 unauthorized (auto-logout) and normalizes error messages
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string | { msg: string }[] }>) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      Cookies.remove(TOKEN_KEY);
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
    }

    // Extract error message from response body
    let errorMessage = "An unexpected error occurred";
    if (error.response?.data?.detail) {
      const detail = error.response.data.detail;
      if (typeof detail === "string") {
        errorMessage = detail;
      } else if (Array.isArray(detail) && detail.length > 0) {
        // FastAPI validation errors format
        errorMessage = detail.map(e => e.msg).join(", ");
      }
    } else if (error.message) {
      errorMessage = error.message;
    }

    // Create a new error with the extracted message
    const enhancedError = new Error(errorMessage);
    (enhancedError as any).status = error.response?.status;
    (enhancedError as any).originalError = error;

    return Promise.reject(enhancedError);
  }
);

// ---- Token management helpers ----

// Stores the auth token in a cookie that expires after 7 days
export const setToken = (token: string) => {
  Cookies.set(TOKEN_KEY, token, { expires: 7 }); // 7 days
};

// Retrieves the current auth token from cookies
export const getToken = () => {
  return Cookies.get(TOKEN_KEY);
};

// Removes the auth token cookie (used on logout or session invalidation)
export const removeToken = () => {
  Cookies.remove(TOKEN_KEY);
};

// ============ Auth API ============
// Handles user sign-up, sign-in, sign-out, and profile management

export const authApi = {
  // Registers a new user and automatically stores the returned JWT token
  signUp: async (data: SignUpRequest): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>("/auth/signup", data);
    setToken(response.data.authorizedAccount.token);
    return response.data;
  },

  // Authenticates an existing user and stores the JWT token
  signIn: async (data: SignInRequest): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>("/auth/signin", data);
    setToken(response.data.authorizedAccount.token);
    return response.data;
  },

  // Signs the user out server-side; always removes the local token even if the request fails
  signOut: async (): Promise<void> => {
    try {
      await api.post("/auth/signout");
    } finally {
      removeToken();
    }
  },

  // Fetches the currently authenticated user's profile
  getProfile: async (): Promise<User> => {
    const response = await api.get<User>("/users/me");
    return response.data;
  },

  // Partially updates the current user's profile fields
  updateProfile: async (data: Partial<User>): Promise<User> => {
    const response = await api.patch<User>("/users/me", data);
    return response.data;
  },
};

// ============ Email OTP API ============
// Passwordless authentication flow via one-time password sent to email

export const emailOtpApi = {
  // Sends a one-time password to the provided email address
  sendOTP: async (email: string): Promise<OTPSendResponse> => {
    const response = await api.post<{ message: string; expiresInSeconds: number }>("/auth/email-otp/send", {
      email,
    });
    return {
      message: response.data.message,
      expiresInSeconds: response.data.expiresInSeconds,
    };
  },

  // Verifies the OTP code and authenticates the user, storing the returned JWT token
  verify: async (email: string, code: string): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>("/auth/email-otp/verify", {
      email,
      code,
    });
    setToken(response.data.authorizedAccount.token);
    return response.data;
  },
};

// ============ Events API ============

// Filter parameters for paginated event listing
export interface EventFilters {
  page?: number;
  pageSize?: number;
  category?: string;
  city?: string;
  search?: string;
  dateFrom?: string;
  dateTo?: string;
}

export const eventsApi = {
  // Fetches a paginated, filtered list of events
  list: async (filters: EventFilters = {}): Promise<EventListResponse> => {
    const params = new URLSearchParams();
    if (filters.page) params.set("page", filters.page.toString());
    if (filters.pageSize) params.set("page_size", filters.pageSize.toString());
    if (filters.category) params.set("category", filters.category);
    if (filters.city) params.set("city", filters.city);
    if (filters.search) params.set("search", filters.search);
    if (filters.dateFrom) params.set("date_from", filters.dateFrom);
    if (filters.dateTo) params.set("date_to", filters.dateTo);

    const response = await api.get<EventListResponse>(`/events?${params}`);
    return response.data;
  },

  // Fetches a single event's full detail by its numeric ID or URL slug
  getByIdOrSlug: async (idOrSlug: string | number): Promise<EventDetail> => {
    const response = await api.get<EventDetail>(`/events/${idOrSlug}`);
    return response.data;
  },

  // Fetches upcoming events, optionally filtered by category, limited to `limit` results
  getUpcoming: async (limit: number = 10, category?: string): Promise<Event[]> => {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (category) params.set("category", category);
    const response = await api.get<Event[]>(`/events/upcoming?${params}`);
    return response.data;
  },

  // Retrieves the list of available event categories (value/label pairs for dropdowns)
  getCategories: async (): Promise<{ value: string; label: string }[]> => {
    const response = await api.get<{ value: string; label: string }[]>("/events/categories");
    return response.data;
  },

  // Gets seat categories (pricing tiers) for a specific event
  getSeatCategories: async (eventId: number): Promise<SeatCategory[]> => {
    const response = await api.get<SeatCategory[]>(`/events/${eventId}/categories`);
    return response.data;
  },

  // Gets individual seats for an event, optionally filtered by seat category
  getSeats: async (eventId: number, categoryId?: number): Promise<EventSeatsResponse> => {
    const params = categoryId ? `?category_id=${categoryId}` : "";
    const response = await api.get<EventSeatsResponse>(`/events/${eventId}/seats${params}`);
    return response.data;
  },
};

// ============ Bookings API ============
// Manages user booking operations: list, view, cancel, and ticket download

export const bookingsApi = {
  // Lists the current user's bookings with pagination and optional status filter
  list: async (page = 1, pageSize = 10, status?: string): Promise<BookingListResponse> => {
    const params = new URLSearchParams({ page: page.toString(), page_size: pageSize.toString() });
    if (status) params.set("status", status);
    const response = await api.get<BookingListResponse>(`/users/me/bookings?${params}`);
    return response.data;
  },

  // Retrieves a single booking's full details by its numeric ID
  get: async (bookingId: number): Promise<BookingDetail> => {
    const response = await api.get<BookingDetail>(`/bookings/${bookingId}`);
    return response.data;
  },

  // Retrieves a single booking by its human-readable booking number
  getByNumber: async (bookingNumber: string): Promise<BookingDetail> => {
    const response = await api.get<BookingDetail>(`/bookings/number/${bookingNumber}`);
    return response.data;
  },

  // Cancels a booking by its ID
  cancel: async (bookingId: number): Promise<BookingDetail> => {
    const response = await api.post<BookingDetail>(`/bookings/${bookingId}/cancel`);
    return response.data;
  },

  // Downloads a ticket PDF as a Blob for the given booking and ticket IDs
  downloadTicket: async (bookingId: number, ticketId: number): Promise<Blob> => {
    const response = await api.get(`/bookings/${bookingId}/tickets/${ticketId}/download`, {
      responseType: "blob",
    });
    return response.data;
  },
};

// ============ Wishlist API ============
// Allows users to save/remove events from their personal wishlist

export const wishlistApi = {
  // Fetches the current user's complete wishlist
  list: async (): Promise<WishlistResponse> => {
    const response = await api.get<WishlistResponse>("/users/me/wishlist");
    return response.data;
  },

  // Adds an event to the user's wishlist
  add: async (eventId: number): Promise<WishlistItem> => {
    const response = await api.post<WishlistItem>(`/users/me/wishlist/${eventId}`);
    return response.data;
  },

  // Removes an event from the user's wishlist
  remove: async (eventId: number): Promise<void> => {
    await api.delete(`/users/me/wishlist/${eventId}`);
  },

  // Checks whether a specific event is in the user's wishlist
  check: async (eventId: number): Promise<{ isInWishlist: boolean }> => {
    const response = await api.get<{ isInWishlist: boolean }>(`/users/me/wishlist/${eventId}/check`);
    return response.data;
  },
};

// ============ Admin API ============
// Administrative endpoints for managing venues, events, seats, users, and activity logs

export const adminApi = {
  // Venues — CRUD operations for event venues
  venues: {
    // Lists all venues with pagination
    list: async (page = 1, pageSize = 20) => {
      const response = await api.get<{ venues: Venue[]; total: number; page: number; pageSize: number }>(
        `/admin/venues?page=${page}&page_size=${pageSize}`
      );
      return response.data;
    },
    // Gets a single venue by ID
    get: async (id: number) => {
      const response = await api.get<Venue>(`/admin/venues/${id}`);
      return response.data;
    },
    // Creates a new venue
    create: async (data: Partial<Venue>) => {
      const response = await api.post<Venue>("/admin/venues", data);
      return response.data;
    },
    // Updates an existing venue by ID
    update: async (id: number, data: Partial<Venue>) => {
      const response = await api.patch<Venue>(`/admin/venues/${id}`, data);
      return response.data;
    },
    // Deletes a venue by ID
    delete: async (id: number) => {
      await api.delete(`/admin/venues/${id}`);
    },
  },

  // Events — admin CRUD plus publish and cancel actions
  events: {
    // Lists events with pagination and optional status filter
    list: async (page = 1, pageSize = 20, status?: string) => {
      const params = new URLSearchParams({ page: page.toString(), page_size: pageSize.toString() });
      if (status) params.set("status", status);
      const response = await api.get(`/admin/events?${params}`);
      return response.data;
    },
    // Gets a single event by ID
    get: async (id: number) => {
      const response = await api.get(`/admin/events/${id}`);
      return response.data;
    },
    // Creates a new event
    create: async (data: Partial<Event>) => {
      const response = await api.post("/admin/events", data);
      return response.data;
    },
    // Updates an existing event by ID
    update: async (id: number, data: Partial<Event>) => {
      const response = await api.patch(`/admin/events/${id}`, data);
      return response.data;
    },
    // Deletes an event by ID
    delete: async (id: number) => {
      await api.delete(`/admin/events/${id}`);
    },
    // Publishes a draft event, making it visible to users
    publish: async (id: number) => {
      const response = await api.post(`/admin/events/${id}/publish`);
      return response.data;
    },
    // Cancels an event
    cancel: async (id: number) => {
      const response = await api.post(`/admin/events/${id}/cancel`);
      return response.data;
    },
  },

  // Seat Categories — manage pricing tiers for event seating
  categories: {
    // Creates a new seat category for an event
    create: async (eventId: number, data: Partial<SeatCategory>) => {
      const response = await api.post(`/admin/events/${eventId}/categories`, data);
      return response.data;
    },
    // Updates an existing seat category
    update: async (eventId: number, categoryId: number, data: Partial<SeatCategory>) => {
      const response = await api.patch(`/admin/events/${eventId}/categories/${categoryId}`, data);
      return response.data;
    },
    // Deletes a seat category from an event
    delete: async (eventId: number, categoryId: number) => {
      await api.delete(`/admin/events/${eventId}/categories/${categoryId}`);
    },
  },

  // Seats — manage individual seats (list, bulk create, block/unblock)
  seats: {
    // Lists seats for an event, optionally filtered by category and status
    list: async (eventId: number, categoryId?: number, status?: string) => {
      const params = new URLSearchParams();
      if (categoryId) params.set("category_id", categoryId.toString());
      if (status) params.set("status", status);
      const response = await api.get(`/admin/seats/event/${eventId}?${params}`);
      return response.data;
    },
    // Creates multiple seats at once for a given event and category
    bulkCreate: async (eventId: number, data: { category_id: number; section?: string; rows: string[]; seats_per_row: number }) => {
      const response = await api.post(`/admin/seats/event/${eventId}/bulk`, data);
      return response.data;
    },
    // Blocks a seat so it cannot be booked
    block: async (seatId: number) => {
      const response = await api.post(`/admin/seats/${seatId}/block`);
      return response.data;
    },
    // Unblocks a previously blocked seat
    unblock: async (seatId: number) => {
      const response = await api.post(`/admin/seats/${seatId}/unblock`);
      return response.data;
    },
  },

  // Users — admin user management (list, block, role changes)
  users: {
    // Lists users with pagination and optional role/blocked/search filters
    list: async (page = 1, pageSize = 20, filters?: { role?: string; isBlocked?: boolean; search?: string }) => {
      const params = new URLSearchParams({ page: page.toString(), page_size: pageSize.toString() });
      if (filters?.role) params.set("role", filters.role);
      if (filters?.isBlocked !== undefined) params.set("is_blocked", filters.isBlocked.toString());
      if (filters?.search) params.set("search", filters.search);
      const response = await api.get(`/admin/users?${params}`);
      return response.data;
    },
    // Gets a single user by ID
    get: async (id: number) => {
      const response = await api.get(`/admin/users/${id}`);
      return response.data;
    },
    // Blocks a user with the specified reason
    block: async (id: number, reason: string) => {
      const response = await api.post(`/admin/users/${id}/block`, { reason });
      return response.data;
    },
    // Unblocks a previously blocked user
    unblock: async (id: number) => {
      const response = await api.post(`/admin/users/${id}/unblock`);
      return response.data;
    },
    // Promotes a user to admin role
    makeAdmin: async (id: number) => {
      const response = await api.post(`/admin/users/${id}/make-admin`);
      return response.data;
    },
    // Revokes admin role from a user
    removeAdmin: async (id: number) => {
      const response = await api.post(`/admin/users/${id}/remove-admin`);
      return response.data;
    },
  },

  // Activity Logs — view admin action audit trail
  logs: {
    // Lists admin activity logs with pagination and optional filters
    list: async (page = 1, pageSize = 20, filters?: { adminId?: number; action?: string; entityType?: string }) => {
      const params = new URLSearchParams({ page: page.toString(), page_size: pageSize.toString() });
      if (filters?.adminId) params.set("admin_id", filters.adminId.toString());
      if (filters?.action) params.set("action", filters.action);
      if (filters?.entityType) params.set("entity_type", filters.entityType);
      const response = await api.get(`/admin/logs?${params}`);
      return response.data;
    },
  },
};

// ============ Tickets API ============

// Transforms a raw ticket response from snake_case backend format to camelCase frontend format
const transformTicket = (data: any): TicketDetail => ({
  id: data.id,
  bookingId: data.booking_id,
  ticketNumber: data.ticket_number,
  categoryName: data.category_name,
  seatLabel: data.seat_label,
  price: data.price,
  isUsed: data.is_used,
  usedAt: data.used_at,
  createdAt: data.created_at,
  eventId: data.event_id,
  eventTitle: data.event_title,
  eventDate: data.event_date,
  venueName: data.venue_name,
  venueCity: data.venue_city,
  bookingNumber: data.booking_number,
  bookingStatus: data.booking_status,
});

export const ticketsApi = {
  // Fetches a single ticket by ID
  get: async (ticketId: number): Promise<TicketDetail> => {
    const response = await api.get(`/tickets/${ticketId}`);
    return transformTicket(response.data);
  },

  // Fetches all tickets associated with a specific booking
  getByBooking: async (bookingId: number): Promise<TicketDetail[]> => {
    const response = await api.get(`/tickets/booking/${bookingId}`);
    return response.data.map(transformTicket);
  },

  // Downloads a ticket as a PDF Blob
  downloadPDF: async (ticketId: number): Promise<Blob> => {
    const response = await api.get(`/tickets/${ticketId}/download`, {
      responseType: "blob",
    });
    return response.data;
  },
};

// ============ Payments API ============
// Integrates with Razorpay for payment order creation, verification, and status checks

export const paymentsApi = {
  // Creates a Razorpay payment order for a booking and returns order details
  createOrder: async (bookingId: number): Promise<CreatePaymentOrderResponse> => {
    const response = await api.post<{
      order_id: string;
      amount: number;
      currency: string;
      key_id: string;
      booking_id: number;
      booking_number: string;
      user_name: string | null;
      user_email: string;
      user_phone: string | null;
    }>("/payments/create-order", { booking_id: bookingId });
    // Transform snake_case to camelCase
    return {
      orderId: response.data.order_id,
      amount: response.data.amount,
      currency: response.data.currency,
      keyId: response.data.key_id,
      bookingId: response.data.booking_id,
      bookingNumber: response.data.booking_number,
      userName: response.data.user_name,
      userEmail: response.data.user_email,
      userPhone: response.data.user_phone,
    };
  },

  // Verifies a completed Razorpay payment using the signature from the client SDK
  verifyPayment: async (data: {
    razorpayOrderId: string;
    razorpayPaymentId: string;
    razorpaySignature: string;
  }): Promise<VerifyPaymentResponse> => {
    const response = await api.post<{
      success: boolean;
      booking_id: number;
      booking_number: string;
      message: string;
    }>("/payments/verify", {
      razorpay_order_id: data.razorpayOrderId,
      razorpay_payment_id: data.razorpayPaymentId,
      razorpay_signature: data.razorpaySignature,
    });
    return {
      success: response.data.success,
      bookingId: response.data.booking_id,
      bookingNumber: response.data.booking_number,
      message: response.data.message,
    };
  },

  // Retrieves the current payment status and details for a booking
  getPaymentStatus: async (bookingId: number): Promise<PaymentStatusResponse> => {
    const response = await api.get<{
      booking_id: number;
      payment_status: string;
      payment: {
        id: number;
        order_id: string;
        payment_id: string | null;
        status: string;
        amount: number;
        method: string | null;
        paid_at: string | null;
      } | null;
    }>(`/payments/booking/${bookingId}/status`);
    return {
      bookingId: response.data.booking_id,
      paymentStatus: response.data.payment_status as any,
      payment: response.data.payment ? {
        id: response.data.payment.id,
        orderId: response.data.payment.order_id,
        paymentId: response.data.payment.payment_id,
        status: response.data.payment.status,
        amount: response.data.payment.amount,
        method: response.data.payment.method,
        paidAt: response.data.payment.paid_at,
      } : null,
    };
  },

  // Cancels a booking that is still in pending payment state
  cancelPendingBooking: async (bookingId: number): Promise<{ success: boolean; message: string }> => {
    const response = await api.post<{ success: boolean; message: string }>(
      `/payments/booking/${bookingId}/cancel`
    );
    return response.data;
  },
};

// ============ Cart API ============
// Manages the shopping cart: fetch, add/update/remove items, validate, checkout

export const cartApi = {
  // Fetches the current active cart (returns null if none exists)
  getCurrent: async (): Promise<Cart | null> => {
    const response = await api.get<Cart | null>("/cart/current");
    return response.data;
  },
  // Gets an existing cart for the event or creates a new one
  getOrCreate: async (eventId: number): Promise<Cart> => {
    const response = await api.post<Cart>("/cart", { eventId });
    return response.data;
  },
  // Adds a seat category (with optional specific seats) to the cart
  addItem: async (data: { eventId: number; seatCategoryId: number; quantity?: number; seatIds?: number[] }): Promise<Cart> => {
    const response = await api.post<Cart>("/cart/items", data);
    return response.data;
  },
  // Updates the quantity of an existing cart item
  updateItem: async (itemId: number, quantity: number): Promise<Cart> => {
    const response = await api.patch<Cart>(`/cart/items/${itemId}`, { quantity });
    return response.data;
  },
  // Removes an item from the cart
  removeItem: async (itemId: number): Promise<Cart> => {
    const response = await api.delete<Cart>(`/cart/items/${itemId}`);
    return response.data;
  },
  // Validates the cart contents (checks seat availability, lock expiry, etc.)
  validate: async (): Promise<CartValidation> => {
    const response = await api.get<CartValidation>("/cart/validate");
    return response.data;
  },
  // Clears all items from the cart
  clear: async (): Promise<void> => {
    await api.delete("/cart/clear");
  },
  // Converts the cart into a confirmed booking, optionally with contact info
  checkout: async (data?: { contactEmail?: string; contactPhone?: string }): Promise<BookingDetail> => {
    const response = await api.post<BookingDetail>("/cart/checkout", data || {});
    return response.data;
  },
  // Gets the total number of items in the cart (for badge display)
  getCount: async (): Promise<number> => {
    const response = await api.get<{ count: number }>("/cart/count");
    return response.data.count;
  },
};

// ============ Notifications API ============
// Manages user email notification preferences

export const notificationsApi = {
  // Fetches the user's current notification preferences, transforming snake_case to camelCase
  getPreferences: async (): Promise<NotificationPreferences> => {
    const response = await api.get<{
      email_booking_confirmation: boolean;
      email_payment_updates: boolean;
      email_ticket_delivery: boolean;
      email_event_reminders: boolean;
      email_event_updates: boolean;
      email_transfer_notifications: boolean;
      email_marketing: boolean;
      created_at: string;
      updated_at: string | null;
    }>("/users/me/notifications/preferences");
    return {
      emailBookingConfirmation: response.data.email_booking_confirmation,
      emailPaymentUpdates: response.data.email_payment_updates,
      emailTicketDelivery: response.data.email_ticket_delivery,
      emailEventReminders: response.data.email_event_reminders,
      emailEventUpdates: response.data.email_event_updates,
      emailTransferNotifications: response.data.email_transfer_notifications,
      emailMarketing: response.data.email_marketing,
      createdAt: response.data.created_at,
      updatedAt: response.data.updated_at,
    };
  },

  // Updates notification preferences, converting camelCase to snake_case for the backend
  updatePreferences: async (
    data: NotificationPreferencesUpdate
  ): Promise<NotificationPreferences> => {
    const response = await api.patch<{
      email_booking_confirmation: boolean;
      email_payment_updates: boolean;
      email_ticket_delivery: boolean;
      email_event_reminders: boolean;
      email_event_updates: boolean;
      email_transfer_notifications: boolean;
      email_marketing: boolean;
      created_at: string;
      updated_at: string | null;
    }>("/users/me/notifications/preferences", {
      email_booking_confirmation: data.emailBookingConfirmation,
      email_payment_updates: data.emailPaymentUpdates,
      email_ticket_delivery: data.emailTicketDelivery,
      email_event_reminders: data.emailEventReminders,
      email_event_updates: data.emailEventUpdates,
      email_transfer_notifications: data.emailTransferNotifications,
      email_marketing: data.emailMarketing,
    });
    return {
      emailBookingConfirmation: response.data.email_booking_confirmation,
      emailPaymentUpdates: response.data.email_payment_updates,
      emailTicketDelivery: response.data.email_ticket_delivery,
      emailEventReminders: response.data.email_event_reminders,
      emailEventUpdates: response.data.email_event_updates,
      emailTransferNotifications: response.data.email_transfer_notifications,
      emailMarketing: response.data.email_marketing,
      createdAt: response.data.created_at,
      updatedAt: response.data.updated_at,
    };
  },
};

// ============ Queue API ============
// Virtual waiting queue for high-demand events; supports REST + WebSocket real-time updates

export const queueApi = {
  // Joins the waiting queue for an event, returns initial position and status
  join: async (eventId: number): Promise<QueueJoinResponse> => {
    const response = await api.post<{
      queue_entry_id: string;
      event_id: number;
      position: number;
      status: string;
      estimated_wait_minutes: number | null;
      total_ahead: number;
      joined_at: string;
    }>(`/queue/${eventId}/join`);
    return {
      queueEntryId: response.data.queue_entry_id,
      eventId: response.data.event_id,
      position: response.data.position,
      status: response.data.status as QueueJoinResponse["status"],
      estimatedWaitMinutes: response.data.estimated_wait_minutes,
      totalAhead: response.data.total_ahead,
      joinedAt: response.data.joined_at,
    };
  },

  // Polls the user's current position in the queue for an event
  getPosition: async (eventId: number): Promise<QueuePositionResponse> => {
    const response = await api.get<{
      queue_entry_id: string;
      event_id: number;
      position: number;
      status: string;
      estimated_wait_minutes: number | null;
      total_ahead: number;
      expires_at: string | null;
      can_proceed: boolean;
    }>(`/queue/${eventId}/position`);
    return {
      queueEntryId: response.data.queue_entry_id,
      eventId: response.data.event_id,
      position: response.data.position,
      status: response.data.status as QueuePositionResponse["status"],
      estimatedWaitMinutes: response.data.estimated_wait_minutes,
      totalAhead: response.data.total_ahead,
      expiresAt: response.data.expires_at,
      canProceed: response.data.can_proceed,
    };
  },

  // Removes the user from the waiting queue for an event
  leave: async (eventId: number): Promise<QueueLeaveResponse> => {
    const response = await api.delete<{
      success: boolean;
      message: string;
    }>(`/queue/${eventId}/leave`);
    return response.data;
  },

  // Gets the overall queue status for an event (total waiting, processing count, etc.)
  getStatus: async (eventId: number): Promise<QueueStatusResponse> => {
    const response = await api.get<{
      event_id: number;
      queue_enabled: boolean;
      total_in_queue: number;
      currently_processing: number;
      estimated_wait_minutes: number | null;
      is_queue_active: boolean;
    }>(`/queue/${eventId}/status`);
    return {
      eventId: response.data.event_id,
      queueEnabled: response.data.queue_enabled,
      totalInQueue: response.data.total_in_queue,
      currentlyProcessing: response.data.currently_processing,
      estimatedWaitMinutes: response.data.estimated_wait_minutes,
      isQueueActive: response.data.is_queue_active,
    };
  },

  // Builds a WebSocket URL for real-time queue position updates, embedding the auth token
  getWebSocketUrl: (eventId: number): string => {
    const token = getToken();
    if (!token) {
      throw new Error("No authentication token available");
    }
    // Build WebSocket URL - remove /api suffix since WebSocket might be at root
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
    const wsBase = baseUrl
      .replace("http://", "ws://")
      .replace("https://", "wss://");
    return `${wsBase}/ws/queue/${eventId}?token=${token}`;
  },
};

export default api;
