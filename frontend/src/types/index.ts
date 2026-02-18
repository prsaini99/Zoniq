// User & Auth Types
export interface User {
  id: number;
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
}

export interface AuthResponse {
  id: number;
  authorizedAccount: {
    token: string;
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

export interface SignUpRequest {
  username: string;
  email: string;
  password: string;
  phone?: string;
  full_name?: string;
  emailOtpCode: string;
}

// OTP Types
export interface OTPSendResponse {
  message: string;
  expiresInSeconds: number;
}

export interface SignInRequest {
  username: string;
  email: string;
  password: string;
}

// Email OTP Types
export interface EmailOTPSendRequest {
  email: string;
}

export interface EmailOTPVerifyRequest {
  email: string;
  code: string;
}

// Venue Types
export interface Venue {
  id: number;
  name: string;
  address: string | null;
  city: string | null;
  state: string | null;
  country: string;
  pincode: string | null;
  capacity: number | null;
  contactPhone: string | null;
  contactEmail: string | null;
  isActive: boolean;
  createdAt: string;
  updatedAt: string | null;
  seatMapConfig: Record<string, unknown> | null;
}

export interface VenueCompact {
  id: number;
  name: string;
  city: string | null;
  state: string | null;
}

// Event Types
export type EventStatus = "draft" | "published" | "cancelled" | "completed" | "soldout";
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

export interface Event {
  id: number;
  title: string;
  slug: string;
  shortDescription: string | null;
  category: EventCategory;
  venue: VenueCompact | null;
  eventDate: string;
  eventEndDate: string | null;
  bookingStartDate: string;
  bookingEndDate: string;
  status: EventStatus;
  bannerImageUrl: string | null;
  thumbnailImageUrl: string | null;
  organizerName: string | null;
  totalSeats: number;
  availableSeats: number;
  maxTicketsPerBooking: number;
  isBookingOpen: boolean;
  createdAt: string;
  // Queue settings
  queueEnabled?: boolean;
  queueBatchSize?: number;
  queueProcessingMinutes?: number;
}

export interface EventDetail extends Event {
  description: string | null;
  termsAndConditions: string | null;
  organizerContact: string | null;
  extraData: Record<string, unknown> | null;
  publishedAt: string | null;
}

export interface EventListResponse {
  events: Event[];
  total: number;
  page: number;
  pageSize: number;
}

// Seat Category Types
export interface SeatCategory {
  id: number;
  eventId: number;
  name: string;
  description: string | null;
  price: string;
  totalSeats: number;
  availableSeats: number;
  displayOrder: number;
  colorCode: string | null;
  isActive: boolean;
  createdAt: string;
}

// Seat Types
export type SeatStatus = "available" | "locked" | "booked" | "blocked";

export interface Seat {
  id: number;
  categoryId: number;
  seatLabel: string | null;
  rowName: string | null;
  section: string | null;
  status: SeatStatus;
  positionX: number | null;
  positionY: number | null;
}

export interface EventSeatsResponse {
  eventId: number;
  categories: SeatCategory[];
  seats: Seat[];
  totalSeats: number;
  availableSeats: number;
}

// Category Label Map
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

// Booking Types
export type BookingStatus = "pending" | "confirmed" | "cancelled" | "refunded" | "failed";
export type PaymentStatus = "pending" | "success" | "failed" | "refunded";

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

export interface BookingItem {
  id: number;
  bookingId: number;
  seatId: number | null;
  categoryId: number;
  categoryName: string;
  seatLabel: string | null;
  price: string;
  ticketNumber: string;
  isUsed: boolean;
  usedAt: string | null;
}

export interface Booking {
  id: number;
  bookingNumber: string;
  userId: number;
  eventId: number;
  event: BookingEventInfo | null;
  status: BookingStatus;
  totalAmount: string;
  discountAmount: string;
  finalAmount: string;
  paymentStatus: PaymentStatus;
  promoCodeUsed: string | null;
  ticketCount: number;
  contactEmail: string | null;
  contactPhone: string | null;
  createdAt: string;
  updatedAt: string | null;
}

export interface BookingDetail extends Booking {
  items: BookingItem[];
}

export interface BookingListResponse {
  bookings: Booking[];
  total: number;
  page: number;
  pageSize: number;
}

// Cart Types
export interface CartItem {
  id: number;
  seatCategoryId: number;
  categoryName: string | null;
  categoryColor: string | null;
  seatIds: number[] | null;
  quantity: number;
  unitPrice: string;
  subtotal: string;
  lockedUntil: string | null;
}

export interface Cart {
  id: number;
  userId: number;
  eventId: number;
  eventTitle: string | null;
  eventDate: string | null;
  eventImage: string | null;
  status: "active" | "converted" | "abandoned" | "expired";
  items: CartItem[];
  subtotal: string;
  total: string;
  itemCount: number;
  expiresAt: string;
}

export interface CartValidation {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

// Wishlist Types
export interface WishlistItem {
  id: number;
  eventId: number;
  event: Event;
  createdAt: string;
}

export interface WishlistResponse {
  items: WishlistItem[];
  total: number;
}

// Payment Types
export interface CreatePaymentOrderResponse {
  orderId: string;
  amount: number; // Amount in paise
  currency: string;
  keyId: string;
  bookingId: number;
  bookingNumber: string;
  userName: string | null;
  userEmail: string;
  userPhone: string | null;
}

export interface VerifyPaymentRequest {
  razorpayOrderId: string;
  razorpayPaymentId: string;
  razorpaySignature: string;
}

export interface VerifyPaymentResponse {
  success: boolean;
  bookingId: number;
  bookingNumber: string;
  message: string;
}

export interface PaymentStatusResponse {
  bookingId: number;
  paymentStatus: PaymentStatus;
  payment: {
    id: number;
    orderId: string;
    paymentId: string | null;
    status: string;
    amount: number;
    method: string | null;
    paidAt: string | null;
  } | null;
}

// Razorpay checkout options (for frontend SDK)
export interface RazorpayOptions {
  key: string;
  amount: number;
  currency: string;
  name: string;
  description: string;
  order_id: string;
  prefill: {
    name?: string;
    email?: string;
    contact?: string;
  };
  theme: {
    color: string;
  };
  handler: (response: RazorpayResponse) => void;
  modal?: {
    ondismiss?: () => void;
  };
}

export interface RazorpayResponse {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
}

// Ticket Types
export interface TicketDetail {
  id: number;
  bookingId: number;
  ticketNumber: string;
  categoryName: string;
  seatLabel: string | null;
  price: string;
  isUsed: boolean;
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

// Notification Preference Types
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

export interface NotificationPreferencesUpdate {
  emailBookingConfirmation?: boolean;
  emailPaymentUpdates?: boolean;
  emailTicketDelivery?: boolean;
  emailEventReminders?: boolean;
  emailEventUpdates?: boolean;
  emailTransferNotifications?: boolean;
  emailMarketing?: boolean;
}

// Queue Types
export type QueueStatus = "waiting" | "processing" | "completed" | "expired" | "left";

export interface QueueJoinResponse {
  queueEntryId: string;
  eventId: number;
  position: number;
  status: QueueStatus;
  estimatedWaitMinutes: number | null;
  totalAhead: number;
  joinedAt: string;
}

export interface QueuePositionResponse {
  queueEntryId: string;
  eventId: number;
  position: number;
  status: QueueStatus;
  estimatedWaitMinutes: number | null;
  totalAhead: number;
  expiresAt: string | null;
  canProceed: boolean;
}

export interface QueueStatusResponse {
  eventId: number;
  queueEnabled: boolean;
  totalInQueue: number;
  currentlyProcessing: number;
  estimatedWaitMinutes: number | null;
  isQueueActive: boolean;
}

export interface QueueLeaveResponse {
  success: boolean;
  message: string;
}

export interface QueuePositionUpdate {
  position: number;
  status: QueueStatus;
  estimatedWaitMinutes: number | null;
  totalAhead: number;
  expiresAt: string | null;
  canProceed: boolean;
}

export interface QueueWebSocketMessage {
  type: "position_update" | "status_change" | "heartbeat" | "error";
  data: Record<string, unknown>;
}

// API Response Types
export interface ApiError {
  detail: string | { msg: string; type: string }[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

