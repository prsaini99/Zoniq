/*
 * types/index.ts — Central type definitions for the Zoniq frontend application.
 * Contains all TypeScript interfaces, type aliases, and constants used across
 * the app for users, authentication, events, venues, seats, bookings, carts,
 * wishlists, payments (Razorpay), tickets, notifications, queues, and API responses.
 */

// ============ User & Auth Types ============

// Represents a user account in the system
export interface User {
  id: number;
  username: string;
  email: string;
  role: "user" | "admin"; // User role for access control
  phone: string | null;
  fullName: string | null;
  isVerified: boolean; // Whether the user's email is verified
  isActive: boolean; // Whether the account is active (not deactivated)
  isLoggedIn: boolean; // Whether the user is currently logged in
  isPhoneVerified: boolean;
  createdAt: string;
  updatedAt: string | null;
}

// Response returned by the sign-up and sign-in endpoints
export interface AuthResponse {
  id: number;
  authorizedAccount: {
    token: string; // JWT authentication token
    username: string;
    email: string;
    role: "user" | "admin";
    phone: string | null;
    fullName: string | null;
    isVerified: boolean;
    isActive: boolean;
    isLoggedIn: boolean;
    isPhoneVerified: boolean;
    createdAt: string;
    updatedAt: string | null;
  };
}

// Payload for user registration
export interface SignUpRequest {
  username: string;
  email: string;
  password: string;
  phone?: string;
  full_name?: string;
  emailOtpCode: string; // OTP code required to verify email during signup
}

// ============ OTP Types ============

// Response after requesting an OTP to be sent
export interface OTPSendResponse {
  message: string;
  expiresInSeconds: number; // How long before the OTP expires
}

// Payload for user login
export interface SignInRequest {
  username: string;
  email: string;
  password: string;
}

// ============ Email OTP Types ============

// Payload to request an email OTP
export interface EmailOTPSendRequest {
  email: string;
}

// Payload to verify an email OTP
export interface EmailOTPVerifyRequest {
  email: string;
  code: string;
}

// ============ Venue Types ============

// Full venue representation with all details
export interface Venue {
  id: number;
  name: string;
  address: string | null;
  city: string | null;
  state: string | null;
  country: string;
  pincode: string | null;
  capacity: number | null; // Maximum seating capacity
  contactPhone: string | null;
  contactEmail: string | null;
  isActive: boolean;
  createdAt: string;
  updatedAt: string | null;
  seatMapConfig: Record<string, unknown> | null; // JSON config for visual seat map rendering
}

// Compact venue info embedded in event listings
export interface VenueCompact {
  id: number;
  name: string;
  city: string | null;
  state: string | null;
}

// ============ Event Types ============

// Possible lifecycle states of an event
export type EventStatus = "draft" | "published" | "cancelled" | "completed" | "soldout";

// Event category taxonomy
export type EventCategory =
  | "concert"
  | "sports"
  | "theater"
  | "comedy"
  | "conference"
  | "workshop"
  | "festival"
  | "exhibition"
  | "other";

// Core event representation used in listings
export interface Event {
  id: number;
  title: string;
  slug: string; // URL-friendly identifier
  shortDescription: string | null;
  category: EventCategory;
  venue: VenueCompact | null;
  eventDate: string; // ISO datetime of event start
  eventEndDate: string | null;
  bookingStartDate: string; // When ticket sales open
  bookingEndDate: string; // When ticket sales close
  status: EventStatus;
  bannerImageUrl: string | null;
  thumbnailImageUrl: string | null;
  organizerName: string | null;
  totalSeats: number;
  availableSeats: number;
  maxTicketsPerBooking: number; // Per-user ticket limit
  isBookingOpen: boolean; // Computed flag: booking window is currently active
  createdAt: string;
  // Queue settings (present when queue feature is enabled for the event)
  queueEnabled?: boolean;
  queueBatchSize?: number; // Number of users processed per batch
  queueProcessingMinutes?: number; // Time window for each batch
}

// Extended event info for the detail page
export interface EventDetail extends Event {
  description: string | null; // Full HTML/markdown description
  termsAndConditions: string | null;
  organizerContact: string | null;
  extraData: Record<string, unknown> | null; // Arbitrary additional metadata
  publishedAt: string | null;
}

// Paginated response wrapper for event listings
export interface EventListResponse {
  events: Event[];
  total: number;
  page: number;
  pageSize: number;
}

// ============ Seat Category Types ============

// A pricing tier / seating section for an event
export interface SeatCategory {
  id: number;
  eventId: number;
  name: string; // e.g., "VIP", "General", "Balcony"
  description: string | null;
  price: string; // Price as string for precise decimal handling
  totalSeats: number;
  availableSeats: number;
  displayOrder: number; // Sort order for UI display
  colorCode: string | null; // Hex color for seat map visualization
  isActive: boolean;
  createdAt: string;
}

// ============ Seat Types ============

// Possible states of an individual seat
export type SeatStatus = "available" | "locked" | "booked" | "blocked";

// Individual seat within a category
export interface Seat {
  id: number;
  categoryId: number;
  seatLabel: string | null; // e.g., "A12"
  rowName: string | null; // e.g., "A"
  section: string | null; // e.g., "Left Wing"
  status: SeatStatus;
  positionX: number | null; // X coordinate for seat map rendering
  positionY: number | null; // Y coordinate for seat map rendering
}

// Response containing all seats and categories for an event
export interface EventSeatsResponse {
  eventId: number;
  categories: SeatCategory[];
  seats: Seat[];
  totalSeats: number;
  availableSeats: number;
}

// Human-readable labels for each event category (used in UI dropdowns and badges)
export const CATEGORY_LABELS: Record<EventCategory, string> = {
  concert: "Concert",
  sports: "Sports",
  theater: "Theater",
  comedy: "Comedy",
  conference: "Conference",
  workshop: "Workshop",
  festival: "Festival",
  exhibition: "Exhibition",
  other: "Other",
};

// ============ Booking Types ============

// Lifecycle states of a booking
export type BookingStatus = "pending" | "confirmed" | "cancelled" | "refunded" | "failed";

// Payment completion states
export type PaymentStatus = "pending" | "success" | "failed" | "refunded";

// Compact event info embedded in booking responses
export interface BookingEventInfo {
  id: number;
  title: string;
  slug: string;
  eventDate: string;
  bannerImageUrl: string | null;
  thumbnailImageUrl: string | null;
  venueName: string | null;
  venueCity: string | null;
}

// A single line item within a booking (one seat/ticket)
export interface BookingItem {
  id: number;
  bookingId: number;
  seatId: number | null;
  categoryId: number;
  categoryName: string;
  seatLabel: string | null;
  price: string;
  ticketNumber: string; // Unique ticket identifier
  isUsed: boolean; // Whether the ticket has been scanned/used at the venue
  usedAt: string | null;
}

// Summary-level booking information (used in listings)
export interface Booking {
  id: number;
  bookingNumber: string; // Human-readable booking reference number
  userId: number;
  eventId: number;
  event: BookingEventInfo | null;
  status: BookingStatus;
  totalAmount: string; // Pre-discount total
  discountAmount: string;
  finalAmount: string; // Amount actually charged
  paymentStatus: PaymentStatus;
  promoCodeUsed: string | null;
  ticketCount: number;
  contactEmail: string | null;
  contactPhone: string | null;
  createdAt: string;
  updatedAt: string | null;
}

// Detailed booking with individual line items (tickets)
export interface BookingDetail extends Booking {
  items: BookingItem[];
}

// Paginated response wrapper for booking listings
export interface BookingListResponse {
  bookings: Booking[];
  total: number;
  page: number;
  pageSize: number;
}

// ============ Cart Types ============

// A single item in the shopping cart
export interface CartItem {
  id: number;
  seatCategoryId: number;
  categoryName: string | null;
  categoryColor: string | null;
  seatIds: number[] | null; // Specific seat IDs if seat selection is enabled
  quantity: number;
  unitPrice: string;
  subtotal: string;
  lockedUntil: string | null; // Seats are temporarily locked until this time
}

// The user's shopping cart for a specific event
export interface Cart {
  id: number;
  userId: number;
  eventId: number;
  eventTitle: string | null;
  eventDate: string | null;
  eventImage: string | null;
  status: "active" | "converted" | "abandoned" | "expired"; // Cart lifecycle state
  items: CartItem[];
  subtotal: string;
  total: string;
  itemCount: number;
  expiresAt: string; // Cart auto-expires after this time to release locked seats
}

// Result of cart validation (checks seat availability, lock expiry, etc.)
export interface CartValidation {
  isValid: boolean;
  errors: string[]; // Blocking issues that prevent checkout
  warnings: string[]; // Non-blocking notices
}

// ============ Wishlist Types ============

// A single event saved to the user's wishlist
export interface WishlistItem {
  id: number;
  eventId: number;
  event: Event; // Full event data for display
  createdAt: string;
}

// Response from the wishlist listing endpoint
export interface WishlistResponse {
  items: WishlistItem[];
  total: number;
}

// ============ Payment Types ============

// Response from creating a Razorpay payment order
export interface CreatePaymentOrderResponse {
  orderId: string; // Razorpay order ID
  amount: number; // Amount in paise (smallest currency unit)
  currency: string; // e.g., "INR"
  keyId: string; // Razorpay public key for the checkout SDK
  bookingId: number;
  bookingNumber: string;
  userName: string | null;
  userEmail: string;
  userPhone: string | null;
}

// Payload sent to verify a payment after Razorpay checkout
export interface VerifyPaymentRequest {
  razorpayOrderId: string;
  razorpayPaymentId: string;
  razorpaySignature: string; // HMAC signature for server-side verification
}

// Response from payment verification
export interface VerifyPaymentResponse {
  success: boolean;
  bookingId: number;
  bookingNumber: string;
  message: string;
}

// Current payment status for a booking
export interface PaymentStatusResponse {
  bookingId: number;
  paymentStatus: PaymentStatus;
  payment: {
    id: number;
    orderId: string;
    paymentId: string | null;
    status: string;
    amount: number;
    method: string | null; // e.g., "upi", "card", "netbanking"
    paidAt: string | null;
  } | null;
}

// ============ Razorpay SDK Types ============

// Options passed to the Razorpay checkout frontend SDK
export interface RazorpayOptions {
  key: string; // Razorpay public API key
  amount: number; // Amount in paise
  currency: string;
  name: string; // Merchant/business name shown in checkout
  description: string; // Payment description
  order_id: string; // Razorpay order ID
  prefill: {
    name?: string;
    email?: string;
    contact?: string; // Phone number
  };
  theme: {
    color: string; // Brand color for the checkout modal
  };
  handler: (response: RazorpayResponse) => void; // Callback on successful payment
  modal?: {
    ondismiss?: () => void; // Callback when user closes the checkout modal
  };
}

// Response object returned by Razorpay after a successful payment
export interface RazorpayResponse {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string; // Signature for backend verification
}

// ============ Ticket Types ============

// Full ticket detail (combines ticket, event, and booking info)
export interface TicketDetail {
  id: number;
  bookingId: number;
  ticketNumber: string;
  categoryName: string;
  seatLabel: string | null;
  price: string;
  isUsed: boolean; // Whether the ticket has been scanned at the venue
  usedAt: string | null;
  createdAt: string;
  eventId: number;
  eventTitle: string;
  eventDate: string;
  venueName: string | null;
  venueCity: string | null;
  bookingNumber: string;
  bookingStatus: string;
}

// ============ Notification Preference Types ============

// User's email notification preferences (all toggles)
export interface NotificationPreferences {
  emailBookingConfirmation: boolean;
  emailPaymentUpdates: boolean;
  emailTicketDelivery: boolean;
  emailEventReminders: boolean;
  emailEventUpdates: boolean;
  emailTransferNotifications: boolean;
  emailMarketing: boolean;
  createdAt: string;
  updatedAt: string | null;
}

// Partial update payload for notification preferences (all fields optional)
export interface NotificationPreferencesUpdate {
  emailBookingConfirmation?: boolean;
  emailPaymentUpdates?: boolean;
  emailTicketDelivery?: boolean;
  emailEventReminders?: boolean;
  emailEventUpdates?: boolean;
  emailTransferNotifications?: boolean;
  emailMarketing?: boolean;
}

// ============ Queue Types ============

// Possible states a user can be in within the waiting queue
export type QueueStatus = "waiting" | "processing" | "completed" | "expired" | "left";

// Response when a user joins the queue
export interface QueueJoinResponse {
  queueEntryId: string;
  eventId: number;
  position: number; // User's position in the queue
  status: QueueStatus;
  estimatedWaitMinutes: number | null;
  totalAhead: number; // Number of people ahead in the queue
  joinedAt: string;
}

// Response when polling the user's current queue position
export interface QueuePositionResponse {
  queueEntryId: string;
  eventId: number;
  position: number;
  status: QueueStatus;
  estimatedWaitMinutes: number | null;
  totalAhead: number;
  expiresAt: string | null; // When the user's processing window expires
  canProceed: boolean; // Whether the user is allowed to proceed to booking
}

// Overall queue status for an event (public info)
export interface QueueStatusResponse {
  eventId: number;
  queueEnabled: boolean;
  totalInQueue: number;
  currentlyProcessing: number;
  estimatedWaitMinutes: number | null;
  isQueueActive: boolean;
}

// Response when leaving the queue
export interface QueueLeaveResponse {
  success: boolean;
  message: string;
}

// Data payload in a WebSocket position_update message
export interface QueuePositionUpdate {
  position: number;
  status: QueueStatus;
  estimatedWaitMinutes: number | null;
  totalAhead: number;
  expiresAt: string | null;
  canProceed: boolean;
}

// Structure of messages received over the queue WebSocket
export interface QueueWebSocketMessage {
  type: "position_update" | "status_change" | "heartbeat" | "error";
  data: Record<string, unknown>;
}

// ============ API Response Types ============

// Standard API error format returned by FastAPI
export interface ApiError {
  detail: string | { msg: string; type: string }[];
}

// Generic paginated response wrapper
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}
