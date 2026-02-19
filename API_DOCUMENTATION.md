# API Documentation - Event Booking Platform

**Base URL:** `http://localhost:{PORT}/api`
**Authentication:** JWT Bearer Token (pass in `Authorization: Bearer <token>` header)
**Content-Type:** `application/json`

> **Note:** All request/response field names use **camelCase** in the API (auto-converted from snake_case by the backend). The documentation below shows camelCase as it appears in Postman.

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [User Profile](#2-user-profile)
3. [Events (Public)](#3-events-public)
4. [Cart](#4-cart)
5. [Bookings](#5-bookings)
6. [Payments](#6-payments)
7. [Tickets](#7-tickets)
8. [Queue](#8-queue)
9. [Wishlist](#9-wishlist)
10. [Notifications](#10-notifications)
11. [WebSocket](#11-websocket)
12. [Admin - Users](#12-admin---users)
13. [Admin - Events](#13-admin---events)
14. [Admin - Venues](#14-admin---venues)
15. [Admin - Seats](#15-admin---seats)
16. [Admin - Bookings](#16-admin---bookings)
17. [Admin - Activity Logs](#17-admin---activity-logs)
18. [Admin - Dashboard](#18-admin---dashboard)
19. [Accounts (Legacy)](#19-accounts-legacy)

---

## 1. Authentication

**File Path:** `backend/src/api/routes/authentication.py`

### 1.1 Sign Up

| Field | Value |
|-------|-------|
| **API Name** | Sign Up |
| **Method** | `POST` |
| **Path** | `/api/auth/signup` |
| **Auth** | None |
| **Description** | Register a new user account. Requires a valid email OTP code (send it first via the email-otp/send endpoint). |

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securePassword123",
  "phone": "+919876543210",       // optional
  "fullName": "John Doe",         // optional
  "emailOtpCode": "123456"        // optional - email OTP for verification
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "authorizedAccount": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "username": "john_doe",
    "email": "john@example.com",
    "role": "user",
    "phone": "+919876543210",
    "fullName": "John Doe",
    "isVerified": true,
    "isActive": true,
    "isLoggedIn": true,
    "isPhoneVerified": false,
    "createdAt": "2026-02-19T10:00:00",
    "updatedAt": null
  }
}
```

---

### 1.2 Sign In

| Field | Value |
|-------|-------|
| **API Name** | Sign In |
| **Method** | `POST` |
| **Path** | `/api/auth/signin` |
| **Auth** | None |
| **Description** | Login with existing credentials. Checks if account is blocked. |

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securePassword123"
}
```

**Response (202 Accepted):**
```json
{
  "id": 1,
  "authorizedAccount": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "username": "john_doe",
    "email": "john@example.com",
    "role": "user",
    "phone": "+919876543210",
    "fullName": "John Doe",
    "isVerified": true,
    "isActive": true,
    "isLoggedIn": true,
    "isPhoneVerified": false,
    "createdAt": "2026-02-19T10:00:00",
    "updatedAt": "2026-02-19T10:30:00"
  }
}
```

---

### 1.3 Send Email OTP

| Field | Value |
|-------|-------|
| **API Name** | Send Email OTP |
| **Method** | `POST` |
| **Path** | `/api/auth/email-otp/send` |
| **Auth** | None |
| **Description** | Send a one-time password to an email address for login/signup verification. |

**Request Body:**
```json
{
  "email": "john@example.com"
}
```

**Response (200 OK):**
```json
{
  "message": "OTP sent to your email",
  "expiresInSeconds": 600
}
```

---

### 1.4 Verify Email OTP

| Field | Value |
|-------|-------|
| **API Name** | Verify Email OTP |
| **Method** | `POST` |
| **Path** | `/api/auth/email-otp/verify` |
| **Auth** | None |
| **Description** | Verify email OTP. Auto-registers new users or logs in existing users. |

**Request Body:**
```json
{
  "email": "john@example.com",
  "code": "123456"
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "authorizedAccount": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "username": "john_doe",
    "email": "john@example.com",
    "role": "user",
    "isVerified": true,
    "isActive": true,
    "isLoggedIn": true,
    "isPhoneVerified": false,
    "createdAt": "2026-02-19T10:00:00",
    "updatedAt": "2026-02-19T10:30:00"
  }
}
```

---

---

## 2. User Profile

**File Path:** `backend/src/api/routes/users.py`

### 2.1 Get Current User Profile

| Field | Value |
|-------|-------|
| **API Name** | Get Current User |
| **Method** | `GET` |
| **Path** | `/api/users/me` |
| **Auth** | Bearer Token |
| **Description** | Get the authenticated user's profile information. |

**Response (200 OK):**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "role": "user",
  "phone": "+919876543210",
  "fullName": "John Doe",
  "isVerified": true,
  "isActive": true,
  "isPhoneVerified": false,
  "createdAt": "2026-02-19T10:00:00",
  "updatedAt": "2026-02-19T10:30:00"
}
```

---

### 2.2 Update Current User Profile

| Field | Value |
|-------|-------|
| **API Name** | Update Profile |
| **Method** | `PATCH` |
| **Path** | `/api/users/me` |
| **Auth** | Bearer Token |
| **Description** | Update the authenticated user's profile. Validates username/email uniqueness if changed. |

**Request Body (all fields optional):**
```json
{
  "username": "new_username",
  "email": "newemail@example.com",
  "phone": "+919876543211",
  "fullName": "John Updated"
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "username": "new_username",
  "email": "newemail@example.com",
  "role": "user",
  "phone": "+919876543211",
  "fullName": "John Updated",
  "isVerified": true,
  "isActive": true,
  "isPhoneVerified": false,
  "createdAt": "2026-02-19T10:00:00",
  "updatedAt": "2026-02-19T11:00:00"
}
```

---

### 2.3 Send Phone Verification OTP

| Field | Value |
|-------|-------|
| **API Name** | Send Phone Verification |
| **Method** | `POST` |
| **Path** | `/api/users/me/verify-phone` |
| **Auth** | Bearer Token |
| **Description** | Send OTP to verify the user's phone number. Phone must be set in profile first. |

**Request Body:** None

**Response (200 OK):**
```json
{
  "message": "Verification OTP sent to your phone",
  "expiresInSeconds": 600
}
```

---

### 2.4 Confirm Phone Verification

| Field | Value |
|-------|-------|
| **API Name** | Confirm Phone Verification |
| **Method** | `POST` |
| **Path** | `/api/users/me/verify-phone/confirm` |
| **Auth** | Bearer Token |
| **Description** | Confirm phone verification using the OTP received via SMS. |

**Request Body:**
```json
{
  "code": "123456"
}
```

**Response (200 OK):**
```json
{
  "message": "Phone verified successfully"
}
```

---

### 2.5 Send Email Verification OTP

| Field | Value |
|-------|-------|
| **API Name** | Send Email Verification |
| **Method** | `POST` |
| **Path** | `/api/users/me/verify-email` |
| **Auth** | Bearer Token |
| **Description** | Send OTP to verify the user's email address. |

**Request Body:** None

**Response (200 OK):**
```json
{
  "message": "Verification OTP sent to your email",
  "expiresInSeconds": 600
}
```

---

### 2.6 Confirm Email Verification

| Field | Value |
|-------|-------|
| **API Name** | Confirm Email Verification |
| **Method** | `POST` |
| **Path** | `/api/users/me/verify-email/confirm` |
| **Auth** | Bearer Token |
| **Description** | Confirm email verification using the OTP received via email. |

**Request Body:**
```json
{
  "code": "123456"
}
```

**Response (200 OK):**
```json
{
  "message": "Email verified successfully"
}
```

---

## 3. Events (Public)

**File Path:** `backend/src/api/routes/events.py`

### 3.1 List Events

| Field | Value |
|-------|-------|
| **API Name** | List Events |
| **Method** | `GET` |
| **Path** | `/api/events` |
| **Auth** | None |
| **Description** | List published events with filters, search, and pagination. Only shows published events. |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number (>= 1) |
| `page_size` | int | 20 | Items per page (1-100) |
| `search` | string | - | Full-text search on title/description |
| `category` | string | - | Filter by category |
| `city` | string | - | Filter by venue city |
| `date_from` | date | - | Events from this date |
| `date_to` | date | - | Events until this date |
| `min_price` | decimal | - | Minimum price filter |
| `max_price` | decimal | - | Maximum price filter |

**Response (200 OK):**
```json
{
  "events": [
    {
      "id": 1,
      "title": "Music Festival 2026",
      "slug": "music-festival-2026",
      "shortDescription": "Annual music festival",
      "category": "music",
      "venue": {
        "id": 1,
        "name": "Stadium Arena",
        "city": "Mumbai",
        "state": "Maharashtra"
      },
      "eventDate": "2026-03-15T18:00:00",
      "eventEndDate": "2026-03-15T23:00:00",
      "bookingStartDate": "2026-02-01T00:00:00",
      "bookingEndDate": "2026-03-14T23:59:59",
      "status": "published",
      "bannerImageUrl": "https://example.com/banner.jpg",
      "thumbnailImageUrl": "https://example.com/thumb.jpg",
      "organizerName": "Event Corp",
      "totalSeats": 5000,
      "availableSeats": 3200,
      "maxTicketsPerBooking": 10,
      "isBookingOpen": true,
      "createdAt": "2026-01-15T10:00:00",
      "queueEnabled": false,
      "queueBatchSize": null,
      "queueProcessingMinutes": null
    }
  ],
  "total": 25,
  "page": 1,
  "pageSize": 20
}
```

---

### 3.2 Get Event Details

| Field | Value |
|-------|-------|
| **API Name** | Get Event Details |
| **Method** | `GET` |
| **Path** | `/api/events/{event_id}` |
| **Auth** | None |
| **Description** | Get full details of a single published event including description and terms. |

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `event_id` | int | Event ID |

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "Music Festival 2026",
  "slug": "music-festival-2026",
  "shortDescription": "Annual music festival",
  "description": "Full event description with all details...",
  "category": "music",
  "venue": { "id": 1, "name": "Stadium Arena", "city": "Mumbai", "state": "Maharashtra" },
  "eventDate": "2026-03-15T18:00:00",
  "eventEndDate": "2026-03-15T23:00:00",
  "bookingStartDate": "2026-02-01T00:00:00",
  "bookingEndDate": "2026-03-14T23:59:59",
  "status": "published",
  "bannerImageUrl": "https://example.com/banner.jpg",
  "thumbnailImageUrl": "https://example.com/thumb.jpg",
  "organizerName": "Event Corp",
  "organizerContact": "contact@eventcorp.com",
  "totalSeats": 5000,
  "availableSeats": 3200,
  "maxTicketsPerBooking": 10,
  "isBookingOpen": true,
  "createdAt": "2026-01-15T10:00:00",
  "queueEnabled": false,
  "termsAndConditions": "Terms text...",
  "extraData": null,
  "publishedAt": "2026-01-20T10:00:00"
}
```

---

### 3.3 Get Event Seats

| Field | Value |
|-------|-------|
| **API Name** | Get Event Seats |
| **Method** | `GET` |
| **Path** | `/api/events/{event_id}/seats` |
| **Auth** | None |
| **Description** | Get seat availability for an event with category details. |

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `event_id` | int | Event ID |

**Response (200 OK):**
```json
{
  "eventId": 1,
  "categories": [
    {
      "id": 1,
      "eventId": 1,
      "name": "VIP",
      "description": "Front row VIP seats",
      "price": 5000.00,
      "totalSeats": 100,
      "availableSeats": 45,
      "displayOrder": 1,
      "colorCode": "#FFD700",
      "isActive": true,
      "createdAt": "2026-01-15T10:00:00"
    }
  ],
  "seats": [
    {
      "id": 1,
      "categoryId": 1,
      "seatLabel": "A-1",
      "rowName": "A",
      "section": "Front",
      "status": "available",
      "positionX": 0,
      "positionY": 0
    }
  ],
  "totalSeats": 5000,
  "availableSeats": 3200
}
```

---

### 3.4 Search Events

| Field | Value |
|-------|-------|
| **API Name** | Search Events |
| **Method** | `GET` |
| **Path** | `/api/events/search` |
| **Auth** | None |
| **Description** | Full-text search across events using PostgreSQL text search with relevance ranking. Title matches are weighted highest. |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `q` | string | (required) | Search query (1-100 chars) |
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Items per page (max 50) |

**Response (200 OK):** `EventListResponse` (same as List Events).

---

### 3.5 Upcoming Events

| Field | Value |
|-------|-------|
| **API Name** | Upcoming Events |
| **Method** | `GET` |
| **Path** | `/api/events/upcoming` |
| **Auth** | None |
| **Description** | Get published events with future dates, sorted by date. |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 10 | Max results (1-50) |
| `category` | string | - | Filter by category |

**Response (200 OK):** `list[EventResponse]`

---

### 3.6 List Event Categories (Enum)

| Field | Value |
|-------|-------|
| **API Name** | List Event Categories |
| **Method** | `GET` |
| **Path** | `/api/events/categories` |
| **Auth** | None |
| **Description** | Get all available event category options (for dropdown selectors). |

**Response (200 OK):**
```json
[
  { "value": "music", "label": "Music" },
  { "value": "sports", "label": "Sports" },
  { "value": "comedy", "label": "Comedy" },
  { "value": "other", "label": "Other" }
]
```

---

### 3.7 Get Event Seat Categories

| Field | Value |
|-------|-------|
| **API Name** | Get Event Seat Categories |
| **Method** | `GET` |
| **Path** | `/api/events/{event_id}/categories` |
| **Auth** | None |
| **Description** | Get seat categories (pricing tiers) for an event. |

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `event_id` | int | Event ID |

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "eventId": 1,
    "name": "VIP",
    "description": "Front row VIP seats",
    "price": 5000.00,
    "totalSeats": 100,
    "availableSeats": 45,
    "displayOrder": 1,
    "colorCode": "#FFD700",
    "isActive": true,
    "createdAt": "2026-01-15T10:00:00"
  },
  {
    "id": 2,
    "eventId": 1,
    "name": "General",
    "description": "General admission",
    "price": 1000.00,
    "totalSeats": 4900,
    "availableSeats": 3155,
    "displayOrder": 2,
    "colorCode": "#3B82F6",
    "isActive": true,
    "createdAt": "2026-01-15T10:00:00"
  }
]
```

---

## 4. Cart

**File Path:** `backend/src/api/routes/cart.py`

### 4.1 Create Cart / Get Cart for Event

| Field | Value |
|-------|-------|
| **API Name** | Create Cart |
| **Method** | `POST` |
| **Path** | `/api/cart` |
| **Auth** | Bearer Token |
| **Description** | Create a new cart for an event or get the existing active cart. |

**Request Body:**
```json
{
  "eventId": 1
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "userId": 1,
  "eventId": 1,
  "eventTitle": "Music Festival 2026",
  "eventDate": "2026-03-15T18:00:00",
  "eventImage": "https://example.com/thumb.jpg",
  "status": "active",
  "items": [],
  "subtotal": 0,
  "total": 0,
  "itemCount": 0,
  "expiresAt": "2026-02-19T10:15:00"
}
```

---

### 4.2 Add Item to Cart

| Field | Value |
|-------|-------|
| **API Name** | Add Item to Cart |
| **Method** | `POST` |
| **Path** | `/api/cart/items` |
| **Auth** | Bearer Token |
| **Description** | Add a seat category item to the active cart. Locks seats automatically. |

**Request Body:**
```json
{
  "eventId": 1,
  "seatCategoryId": 1,
  "quantity": 2,
  "seatIds": [101, 102]    // optional - for assigned seating
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "userId": 1,
  "eventId": 1,
  "eventTitle": "Music Festival 2026",
  "eventDate": "2026-03-15T18:00:00",
  "eventImage": "https://example.com/thumb.jpg",
  "status": "active",
  "items": [
    {
      "id": 1,
      "seatCategoryId": 1,
      "categoryName": "VIP",
      "categoryColor": "#FFD700",
      "seatIds": [101, 102],
      "quantity": 2,
      "unitPrice": 5000.00,
      "subtotal": 10000.00,
      "lockedUntil": "2026-02-19T10:15:00"
    }
  ],
  "subtotal": 10000.00,
  "total": 10000.00,
  "itemCount": 2,
  "expiresAt": "2026-02-19T10:15:00"
}
```

---

### 4.3 Update Cart Item

| Field | Value |
|-------|-------|
| **API Name** | Update Cart Item |
| **Method** | `PATCH` |
| **Path** | `/api/cart/items/{item_id}` |
| **Auth** | Bearer Token |
| **Description** | Update the quantity of a cart item. |

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `item_id` | int | Cart item ID |

**Request Body:**
```json
{
  "quantity": 3
}
```

**Response (200 OK):** Same as Cart response structure above.

---

### 4.4 Remove Cart Item

| Field | Value |
|-------|-------|
| **API Name** | Remove Cart Item |
| **Method** | `DELETE` |
| **Path** | `/api/cart/items/{item_id}` |
| **Auth** | Bearer Token |
| **Description** | Remove an item from the cart and release locked seats. |

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `item_id` | int | Cart item ID |

**Response (200 OK):** Updated Cart response.

---

### 4.5 Validate Cart

| Field | Value |
|-------|-------|
| **API Name** | Validate Cart |
| **Method** | `GET` |
| **Path** | `/api/cart/validate` |
| **Auth** | Bearer Token |
| **Description** | Validate the cart before checkout (checks seat availability, expiry, etc.). |

**Response (200 OK):**
```json
{
  "isValid": true,
  "errors": [],
  "warnings": []
}
```

---

### 4.6 Checkout

| Field | Value |
|-------|-------|
| **API Name** | Checkout |
| **Method** | `POST` |
| **Path** | `/api/cart/checkout` |
| **Auth** | Bearer Token |
| **Description** | Convert the cart into a confirmed booking. Validates cart first. |

**Request Body:**
```json
{
  "contactEmail": "john@example.com",   // optional - defaults to user's email
  "contactPhone": "+919876543210"        // optional - defaults to user's phone
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "bookingNumber": "BK-20260219-ABC123",
  "userId": 1,
  "eventId": 1,
  "event": {
    "id": 1,
    "title": "Music Festival 2026",
    "slug": "music-festival-2026",
    "eventDate": "2026-03-15T18:00:00",
    "bannerImageUrl": "https://example.com/banner.jpg",
    "thumbnailImageUrl": "https://example.com/thumb.jpg",
    "venueName": "Stadium Arena",
    "venueCity": "Mumbai"
  },
  "status": "confirmed",
  "totalAmount": 10000.00,
  "discountAmount": 0,
  "finalAmount": 10000.00,
  "paymentStatus": "pending",
  "promoCodeUsed": null,
  "ticketCount": 2,
  "contactEmail": "john@example.com",
  "contactPhone": "+919876543210",
  "createdAt": "2026-02-19T10:05:00",
  "updatedAt": null,
  "items": [
    {
      "id": 1,
      "bookingId": 1,
      "seatId": 101,
      "categoryId": 1,
      "categoryName": "VIP",
      "seatLabel": "A-1",
      "price": 5000.00,
      "ticketNumber": "TK-ABC12345",
      "isUsed": false,
      "usedAt": null
    }
  ]
}
```

---

### 4.7 Get Current Cart

| Field | Value |
|-------|-------|
| **API Name** | Get Current Cart |
| **Method** | `GET` |
| **Path** | `/api/cart/current` |
| **Auth** | Bearer Token |
| **Description** | Get the user's current active cart (if any). Returns null if no active cart. |

**Response (200 OK):** Cart response or `null`.

---

### 4.8 Clear Cart

| Field | Value |
|-------|-------|
| **API Name** | Clear Cart |
| **Method** | `DELETE` |
| **Path** | `/api/cart/clear` |
| **Auth** | Bearer Token |
| **Description** | Clear/abandon the user's current active cart and release any locked seats. |

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Cart cleared"
}
```

---

### 4.9 Get Cart Count

| Field | Value |
|-------|-------|
| **API Name** | Get Cart Count |
| **Method** | `GET` |
| **Path** | `/api/cart/count` |
| **Auth** | Bearer Token |
| **Description** | Get the total item count in the user's active cart. |

**Response (200 OK):**
```json
{
  "count": 3
}
```

---

## 5. Bookings

**File Path:** `backend/src/api/routes/bookings.py`

### 5.1 List User Bookings

| Field | Value |
|-------|-------|
| **API Name** | List Bookings |
| **Method** | `GET` |
| **Path** | `/api/users/me/bookings` |
| **Auth** | Bearer Token |
| **Description** | List the authenticated user's bookings with pagination. |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Items per page |
| `status` | string | - | Filter: confirmed, cancelled, pending |

**Response (200 OK):**
```json
{
  "bookings": [
    {
      "id": 1,
      "bookingNumber": "BK-20260219-ABC123",
      "userId": 1,
      "eventId": 1,
      "event": {
        "id": 1,
        "title": "Music Festival 2026",
        "slug": "music-festival-2026",
        "eventDate": "2026-03-15T18:00:00",
        "bannerImageUrl": null,
        "thumbnailImageUrl": null,
        "venueName": "Stadium Arena",
        "venueCity": "Mumbai"
      },
      "status": "confirmed",
      "totalAmount": 10000.00,
      "discountAmount": 0,
      "finalAmount": 10000.00,
      "paymentStatus": "paid",
      "promoCodeUsed": null,
      "ticketCount": 2,
      "contactEmail": "john@example.com",
      "contactPhone": "+919876543210",
      "createdAt": "2026-02-19T10:05:00",
      "updatedAt": null
    }
  ],
  "total": 5,
  "page": 1,
  "pageSize": 20
}
```

---

### 5.2 Get Booking Details

| Field | Value |
|-------|-------|
| **API Name** | Get Booking Details |
| **Method** | `GET` |
| **Path** | `/api/bookings/{booking_id}` |
| **Auth** | Bearer Token |
| **Description** | Get full details of a specific booking including all ticket items. |

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `booking_id` | int | Booking ID |

**Response (200 OK):** `BookingDetailResponse` (same as checkout response - includes `items` array).

---

### 5.3 Get Booking by Number

| Field | Value |
|-------|-------|
| **API Name** | Get Booking by Number |
| **Method** | `GET` |
| **Path** | `/api/bookings/number/{booking_number}` |
| **Auth** | Bearer Token |
| **Description** | Get booking details by booking number (e.g., BK-20260219-ABC123) instead of ID. Owner verification enforced. |

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `booking_number` | string | Booking number |

**Response (200 OK):** `BookingDetailResponse` (same as Get Booking Details).

---

### 5.4 Cancel Booking

| Field | Value |
|-------|-------|
| **API Name** | Cancel Booking |
| **Method** | `POST` |
| **Path** | `/api/bookings/{booking_id}/cancel` |
| **Auth** | Bearer Token |
| **Description** | Cancel a booking. Releases locked seats and updates status. |

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `booking_id` | int | Booking ID |

**Request Body:**
```json
{
  "reason": "Cannot attend"    // optional
}
```

**Response (200 OK):** Updated `BookingDetailResponse`.

---

## 6. Payments

**File Path:** `backend/src/api/routes/payments.py`

### 6.1 Create Payment Order

| Field | Value |
|-------|-------|
| **API Name** | Create Payment Order |
| **Method** | `POST` |
| **Path** | `/api/payments/create-order` |
| **Auth** | Bearer Token |
| **Description** | Create a Razorpay order for a booking. Returns details needed for frontend Razorpay checkout. |

**Request Body:**
```json
{
  "bookingId": 1
}
```

**Response (200 OK):**
```json
{
  "orderId": "order_RzP1abc123xyz",
  "amount": 1000000,
  "currency": "INR",
  "keyId": "rzp_test_xxxxx",
  "bookingId": 1,
  "bookingNumber": "BK-20260219-ABC123",
  "userName": "John Doe",
  "userEmail": "john@example.com",
  "userPhone": "+919876543210"
}
```

---

### 6.2 Verify Payment

| Field | Value |
|-------|-------|
| **API Name** | Verify Payment |
| **Method** | `POST` |
| **Path** | `/api/payments/verify` |
| **Auth** | Bearer Token |
| **Description** | Verify a Razorpay payment signature after successful payment on the frontend. |

**Request Body:**
```json
{
  "razorpayOrderId": "order_RzP1abc123xyz",
  "razorpayPaymentId": "pay_RzP1def456uvw",
  "razorpaySignature": "abc123signaturehash..."
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "bookingId": 1,
  "bookingNumber": "BK-20260219-ABC123",
  "message": "Payment verified successfully"
}
```

---

### 6.3 Payment Webhook

| Field | Value |
|-------|-------|
| **API Name** | Payment Webhook |
| **Method** | `POST` |
| **Path** | `/api/payments/webhook` |
| **Auth** | Razorpay Webhook Secret (in headers) |
| **Description** | Razorpay webhook endpoint for automated payment event processing. |

**Request Body:** Razorpay webhook event payload.

**Response (200 OK):**
```json
{
  "status": "ok"
}
```

---

### 6.4 Get Payment Details

| Field | Value |
|-------|-------|
| **API Name** | Get Payment |
| **Method** | `GET` |
| **Path** | `/api/payments/{payment_id}` |
| **Auth** | Bearer Token |
| **Description** | Get payment details. Verifies ownership. |

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `payment_id` | int | Payment ID |

**Response (200 OK):**
```json
{
  "id": 1,
  "bookingId": 1,
  "razorpayOrderId": "order_RzP1abc123xyz",
  "razorpayPaymentId": "pay_RzP1def456uvw",
  "amount": 1000000,
  "currency": "INR",
  "status": "captured",
  "method": "upi",
  "errorCode": null,
  "errorDescription": null,
  "createdAt": "2026-02-19T10:05:00",
  "paidAt": "2026-02-19T10:06:30"
}
```

---

### 6.5 Cancel Pending Booking (Payment)

| Field | Value |
|-------|-------|
| **API Name** | Cancel Pending Booking |
| **Method** | `POST` |
| **Path** | `/api/payments/booking/{booking_id}/cancel` |
| **Auth** | Bearer Token |
| **Description** | Cancel a pending booking (before payment) and release locked seats. |

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `booking_id` | int | Booking ID |

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Booking cancelled and seats released"
}
```

---

### 6.6 Get Payment Status

| Field | Value |
|-------|-------|
| **API Name** | Get Payment Status |
| **Method** | `GET` |
| **Path** | `/api/payments/booking/{booking_id}/status` |
| **Auth** | Bearer Token |
| **Description** | Get the payment status for a booking. |

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `booking_id` | int | Booking ID |

**Response (200 OK):**
```json
{
  "bookingId": 1,
  "paymentStatus": "paid",
  "payment": {
    "id": 1,
    "orderId": "order_RzP1abc123xyz",
    "paymentId": "pay_RzP1def456uvw",
    "status": "captured",
    "amount": 1000000,
    "method": "upi",
    "paidAt": "2026-02-19T10:06:30"
  }
}
```

> **Note:** `payment` will be `null` if no payment has been initiated for the booking.

---

## 7. Tickets

**File Path:** `backend/src/api/routes/tickets.py`

### 7.1 Get Ticket Details

| Field | Value |
|-------|-------|
| **API Name** | Get Ticket |
| **Method** | `GET` |
| **Path** | `/api/tickets/{ticket_id}` |
| **Auth** | Bearer Token |
| **Description** | Get details of a specific ticket. |

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `ticket_id` | int | Ticket ID |

**Response (200 OK):** Same as single ticket object above.

---

### 7.2 Download Ticket PDF

| Field | Value |
|-------|-------|
| **API Name** | Download Ticket PDF |
| **Method** | `GET` |
| **Path** | `/api/tickets/{ticket_id}/download` |
| **Auth** | Bearer Token |
| **Description** | Download a ticket as a PDF file with event, venue, and booking details. |

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `ticket_id` | int | Ticket ID |

**Response (200 OK):** PDF file download.

---

### 7.3 Mark Ticket as Used

| Field | Value |
|-------|-------|
| **API Name** | Mark Ticket Used |
| **Method** | `POST` |
| **Path** | `/api/tickets/mark-used` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Mark a ticket as used at event entry (for organizers/check-in). |

**Request Body:**
```json
{
  "ticketNumber": "TK-ABC12345"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "ticketNumber": "TK-ABC12345",
  "message": "Ticket marked as used",
  "usedAt": "2026-03-15T18:30:00"
}
```

---

### 7.4 Transfer Ticket

| Field | Value |
|-------|-------|
| **API Name** | Transfer Ticket |
| **Method** | `POST` |
| **Path** | `/api/tickets/{ticket_id}/transfer` |
| **Auth** | Bearer Token |
| **Description** | Initiate a ticket transfer to another user by email. |

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `ticket_id` | int | Ticket ID |

**Request Body:**
```json
{
  "toEmail": "friend@example.com",
  "message": "Enjoy the show!"     // optional
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "transferId": 1,
  "message": "Ticket transfer initiated",
  "expiresAt": "2026-02-20T10:00:00"
}
```

---

### 7.5 Claim Transferred Ticket

| Field | Value |
|-------|-------|
| **API Name** | Claim Transfer |
| **Method** | `POST` |
| **Path** | `/api/tickets/claim` |
| **Auth** | Bearer Token |
| **Description** | Claim a ticket that was transferred to the authenticated user. |

**Request Body:**
```json
{
  "transferToken": "unique-transfer-token"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "ticketNumber": "TK-ABC12345",
  "message": "Ticket claimed successfully"
}
```

---

### 7.6 Cancel Transfer

| Field | Value |
|-------|-------|
| **API Name** | Cancel Transfer |
| **Method** | `POST` |
| **Path** | `/api/tickets/transfers/{transfer_id}/cancel` |
| **Auth** | Bearer Token |
| **Description** | Cancel a pending ticket transfer. |

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `transfer_id` | int | Transfer ID |

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Transfer cancelled"
}
```

---

### 7.7 Transfer History

| Field | Value |
|-------|-------|
| **API Name** | Transfer History |
| **Method** | `GET` |
| **Path** | `/api/tickets/transfers/history` |
| **Auth** | Bearer Token |
| **Description** | Get the transfer history for the authenticated user with pagination. |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Items per page |

**Response (200 OK):**
```json
{
  "transfers": [
    {
      "id": 1,
      "ticketNumber": "TK-ABC12345",
      "fromEmail": "john@example.com",
      "toEmail": "friend@example.com",
      "status": "completed",
      "message": "Enjoy the show!",
      "createdAt": "2026-02-19T10:00:00",
      "transferredAt": "2026-02-19T12:00:00",
      "expiresAt": "2026-02-20T10:00:00"
    }
  ],
  "total": 1
}
```

---

### 7.8 Get Booking Tickets

| Field | Value |
|-------|-------|
| **API Name** | Get Booking Tickets |
| **Method** | `GET` |
| **Path** | `/api/tickets/booking/{booking_id}` |
| **Auth** | Bearer Token |
| **Description** | Get all tickets for a specific booking. Owner or admin access. |

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `booking_id` | int | Booking ID |

**Response (200 OK):** `list[TicketResponse]`

---

## 8. Queue

**File Path:** `backend/src/api/routes/queue.py`

### 8.1 Join Queue

| Field | Value |
|-------|-------|
| **API Name** | Join Queue |
| **Method** | `POST` |
| **Path** | `/api/queue/{event_id}/join` |
| **Auth** | Bearer Token |
| **Description** | Join the virtual queue for a high-demand event. |

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `event_id` | int | Event ID |

**Response (200 OK):**
```json
{
  "queueEntryId": "550e8400-e29b-41d4-a716-446655440000",
  "eventId": 1,
  "position": 42,
  "status": "waiting",
  "estimatedWaitMinutes": 15,
  "totalAhead": 41,
  "joinedAt": "2026-02-19T10:00:00"
}
```

---

### 8.2 Get Queue Position

| Field | Value |
|-------|-------|
| **API Name** | Get Queue Position |
| **Method** | `GET` |
| **Path** | `/api/queue/{event_id}/position` |
| **Auth** | Bearer Token |
| **Description** | Get the user's current position in the queue. |

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `event_id` | int | Event ID |

**Response (200 OK):**
```json
{
  "queueEntryId": "550e8400-e29b-41d4-a716-446655440000",
  "eventId": 1,
  "position": 35,
  "status": "waiting",
  "estimatedWaitMinutes": 12,
  "totalAhead": 34,
  "expiresAt": null,
  "canProceed": false
}
```

---

### 8.3 Get Queue Status

| Field | Value |
|-------|-------|
| **API Name** | Get Queue Status |
| **Method** | `GET` |
| **Path** | `/api/queue/{event_id}/status` |
| **Auth** | None |
| **Description** | Get public queue status for an event. |

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `event_id` | int | Event ID |

**Response (200 OK):**
```json
{
  "eventId": 1,
  "queueEnabled": true,
  "totalInQueue": 250,
  "currentlyProcessing": 50,
  "estimatedWaitMinutes": 25,
  "isQueueActive": true
}
```

---

### 8.4 Leave Queue

| Field | Value |
|-------|-------|
| **API Name** | Leave Queue |
| **Method** | `DELETE` |
| **Path** | `/api/queue/{event_id}/leave` |
| **Auth** | Bearer Token |
| **Description** | Leave the virtual queue. |

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `event_id` | int | Event ID |

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Left the queue"
}
```

---

## 9. Wishlist

**File Path:** `backend/src/api/routes/wishlist.py`

### 9.1 Get Wishlist

| Field | Value |
|-------|-------|
| **API Name** | Get Wishlist |
| **Method** | `GET` |
| **Path** | `/api/users/me/wishlist` |
| **Auth** | Bearer Token |
| **Description** | Get the user's wishlist with full event details. |

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": 1,
      "eventId": 1,
      "event": {
        "id": 1,
        "title": "Music Festival 2026",
        "slug": "music-festival-2026",
        "shortDescription": "Annual music festival",
        "category": "music",
        "venue": { "id": 1, "name": "Stadium Arena", "city": "Mumbai", "state": "Maharashtra" },
        "eventDate": "2026-03-15T18:00:00",
        "status": "published",
        "totalSeats": 5000,
        "availableSeats": 3200,
        "isBookingOpen": true,
        "createdAt": "2026-01-15T10:00:00"
      },
      "createdAt": "2026-02-10T10:00:00"
    }
  ],
  "total": 1
}
```

---

### 9.2 Add to Wishlist

| Field | Value |
|-------|-------|
| **API Name** | Add to Wishlist |
| **Method** | `POST` |
| **Path** | `/api/users/me/wishlist/{event_id}` |
| **Auth** | Bearer Token |
| **Description** | Add an event to the user's wishlist. |

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `event_id` | int | Event ID |

**Response (201 Created):**
```json
{
  "id": 1,
  "eventId": 1,
  "event": { ... },
  "createdAt": "2026-02-19T10:00:00"
}
```

---

### 9.3 Remove from Wishlist

| Field | Value |
|-------|-------|
| **API Name** | Remove from Wishlist |
| **Method** | `DELETE` |
| **Path** | `/api/users/me/wishlist/{event_id}` |
| **Auth** | Bearer Token |
| **Description** | Remove an event from the user's wishlist. |

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `event_id` | int | Event ID |

**Response (200 OK):**
```json
{
  "message": "Removed from wishlist"
}
```

---

### 9.4 Check Wishlist

| Field | Value |
|-------|-------|
| **API Name** | Check Wishlist |
| **Method** | `GET` |
| **Path** | `/api/users/me/wishlist/{event_id}/check` |
| **Auth** | Bearer Token |
| **Description** | Check if a specific event is in the user's wishlist. |

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `event_id` | int | Event ID |

**Response (200 OK):**
```json
{
  "isInWishlist": true
}
```

---

## 10. Notifications

**File Path:** `backend/src/api/routes/notifications.py`

### 10.1 Get Notification Preferences

| Field | Value |
|-------|-------|
| **API Name** | Get Notification Preferences |
| **Method** | `GET` |
| **Path** | `/api/users/me/notifications/preferences` |
| **Auth** | Bearer Token |
| **Description** | Get the user's notification preference settings. |

**Response (200 OK):**
```json
{
  "emailBookingConfirmation": true,
  "emailPaymentUpdates": true,
  "emailTicketDelivery": true,
  "emailEventReminders": true,
  "emailEventUpdates": true,
  "emailTransferNotifications": true,
  "emailMarketing": false,
  "createdAt": "2026-02-19T10:00:00",
  "updatedAt": null
}
```

---

### 10.2 Update Notification Preferences

| Field | Value |
|-------|-------|
| **API Name** | Update Notification Preferences |
| **Method** | `PATCH` |
| **Path** | `/api/users/me/notifications/preferences` |
| **Auth** | Bearer Token |
| **Description** | Update the user's notification preferences. Only send fields you want to change. |

**Request Body (all fields optional):**
```json
{
  "emailBookingConfirmation": true,
  "emailPaymentUpdates": true,
  "emailTicketDelivery": true,
  "emailEventReminders": false,
  "emailEventUpdates": true,
  "emailTransferNotifications": true,
  "emailMarketing": false
}
```

**Response (200 OK):** Updated notification preferences object.

---

## 11. WebSocket

**File Path:** `backend/src/api/routes/websocket.py`

### 11.1 Queue WebSocket

| Field | Value |
|-------|-------|
| **API Name** | Queue WebSocket |
| **Protocol** | `WebSocket` |
| **Path** | `/api/ws/queue/{event_id}?token=<jwt_token>` |
| **Auth** | JWT Token (query parameter) |
| **Description** | Real-time queue position updates via WebSocket. |

**Connection URL:** `ws://localhost:{PORT}/api/ws/queue/{event_id}?token=<jwt_token>`

**Server Messages:**
```json
// Position update
{
  "type": "position_update",
  "data": {
    "position": 35,
    "status": "waiting",
    "estimatedWait": 12,
    "totalAhead": 34,
    "expiresAt": null,
    "canProceed": false
  }
}

// Error
{
  "type": "error",
  "data": { "message": "Invalid token" }
}
```

**Client Messages:**
```json
// Request position refresh
{ "type": "refresh" }
```

---

## 12. Admin - Users

**File Path:** `backend/src/api/routes/admin/users.py`
**Auth:** Bearer Token (Admin role required)

### 12.1 List Users

| Field | Value |
|-------|-------|
| **API Name** | Admin List Users |
| **Method** | `GET` |
| **Path** | `/api/admin/users` |
| **Auth** | Bearer Token (Admin) |
| **Description** | List all users with search and pagination. |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Items per page |
| `search` | string | - | Search by username/email |

**Response (200 OK):**
```json
{
  "users": [
    {
      "id": 1,
      "username": "john_doe",
      "email": "john@example.com",
      "role": "user",
      "phone": "+919876543210",
      "fullName": "John Doe",
      "isVerified": true,
      "isActive": true,
      "isPhoneVerified": false,
      "isBlocked": false,
      "blockedReason": null,
      "lastLoginAt": "2026-02-19T10:00:00",
      "createdAt": "2026-01-01T00:00:00",
      "updatedAt": "2026-02-19T10:00:00"
    }
  ],
  "total": 150,
  "page": 1,
  "pageSize": 20
}
```

---

### 12.2 Get User Stats

| Field | Value |
|-------|-------|
| **API Name** | Admin User Stats |
| **Method** | `GET` |
| **Path** | `/api/admin/users/stats` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Get user statistics for the admin dashboard. |

**Response (200 OK):**
```json
{
  "totalUsers": 1500,
  "activeUsers": 1420,
  "blockedUsers": 5,
  "adminUsers": 3,
  "newUsersToday": 12,
  "newUsersWeek": 85
}
```

---

### 12.3 Get User Details

| Field | Value |
|-------|-------|
| **API Name** | Admin Get User |
| **Method** | `GET` |
| **Path** | `/api/admin/users/{user_id}` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Get detailed information about a specific user. |

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | int | User ID |

**Response (200 OK):** Single `AdminAccountView` object (same as items in list response).

---

### 12.4 Block User

| Field | Value |
|-------|-------|
| **API Name** | Admin Block User |
| **Method** | `POST` |
| **Path** | `/api/admin/users/{user_id}/block` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Block a user account. Blocked users cannot log in. |

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | int | User ID |

**Request Body:**
```json
{
  "reason": "Violation of terms"   // optional
}
```

**Response (200 OK):** Updated `AdminAccountView` with `isBlocked: true`.

---

### 12.5 Unblock User

| Field | Value |
|-------|-------|
| **API Name** | Admin Unblock User |
| **Method** | `POST` |
| **Path** | `/api/admin/users/{user_id}/unblock` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Unblock a previously blocked user account. |

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | int | User ID |

**Response (200 OK):** Updated `AdminAccountView` with `isBlocked: false`.

---

## 13. Admin - Events

**File Path:** `backend/src/api/routes/admin/events.py`
**Auth:** Bearer Token (Admin role required)

### 13.1 List Events (Admin)

| Field | Value |
|-------|-------|
| **API Name** | Admin List Events |
| **Method** | `GET` |
| **Path** | `/api/admin/events` |
| **Auth** | Bearer Token (Admin) |
| **Description** | List all events including draft/cancelled. Supports filters and pagination. |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Items per page (max 100) |
| `status` | string | - | Filter by status |
| `category` | string | - | Filter by category |
| `city` | string | - | Filter by venue city |
| `search` | string | - | Search in title/description |
| `date_from` | date | - | From date |
| `date_to` | date | - | To date |

**Response (200 OK):** `EventListResponse`

---

### 13.2 Create Event

| Field | Value |
|-------|-------|
| **API Name** | Admin Create Event |
| **Method** | `POST` |
| **Path** | `/api/admin/events` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Create a new event in draft status. |

**Request Body:**
```json
{
  "title": "Music Festival 2026",
  "description": "Full description...",
  "shortDescription": "Annual music festival",
  "category": "music",
  "venueId": 1,
  "eventDate": "2026-03-15T18:00:00",
  "eventEndDate": "2026-03-15T23:00:00",
  "bookingStartDate": "2026-02-01T00:00:00",
  "bookingEndDate": "2026-03-14T23:59:59",
  "bannerImageUrl": "https://example.com/banner.jpg",
  "thumbnailImageUrl": "https://example.com/thumb.jpg",
  "termsAndConditions": "Terms text...",
  "organizerName": "Event Corp",
  "organizerContact": "contact@eventcorp.com",
  "maxTicketsPerBooking": 10,
  "extraData": null,
  "queueEnabled": false,
  "queueBatchSize": 50,
  "queueProcessingMinutes": 10
}
```

**Response (201 Created):** `EventAdminResponse` (includes `createdBy`, `updatedAt`, `cancelledAt`).

---

### 13.3 Get Event Stats

| Field | Value |
|-------|-------|
| **API Name** | Admin Event Stats |
| **Method** | `GET` |
| **Path** | `/api/admin/events/stats` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Get event statistics. |

**Response (200 OK):**
```json
{
  "total": 25,
  "draft": 5,
  "published": 15,
  "cancelled": 2,
  "completed": 3
}
```

---

### 13.4 Get Event (Admin)

| Field | Value |
|-------|-------|
| **API Name** | Admin Get Event |
| **Method** | `GET` |
| **Path** | `/api/admin/events/{event_id}` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Get full event details including all admin-only fields. |

**Response (200 OK):** `EventAdminResponse`

---

### 13.5 Update Event

| Field | Value |
|-------|-------|
| **API Name** | Admin Update Event |
| **Method** | `PATCH` |
| **Path** | `/api/admin/events/{event_id}` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Update event details. All fields are optional. |

**Request Body:** Same fields as Create Event, all optional.

**Response (200 OK):** Updated `EventAdminResponse`.

---

### 13.6 Publish Event

| Field | Value |
|-------|-------|
| **API Name** | Admin Publish Event |
| **Method** | `POST` |
| **Path** | `/api/admin/events/{event_id}/publish` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Publish a draft event, making it visible to users. |

**Response (200 OK):** Updated `EventAdminResponse` with `status: "published"`.

---

### 13.7 Cancel Event

| Field | Value |
|-------|-------|
| **API Name** | Admin Cancel Event |
| **Method** | `POST` |
| **Path** | `/api/admin/events/{event_id}/cancel` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Cancel an event. |

**Response (200 OK):** Updated `EventAdminResponse` with `status: "cancelled"`.

---

### 13.8 Reactivate Event

| Field | Value |
|-------|-------|
| **API Name** | Admin Reactivate Event |
| **Method** | `POST` |
| **Path** | `/api/admin/events/{event_id}/reactivate` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Reactivate a cancelled event (sets back to draft). |

**Response (200 OK):** Updated `EventAdminResponse` with `status: "draft"`.

---

### 13.9 Delete Event

| Field | Value |
|-------|-------|
| **API Name** | Admin Delete Event |
| **Method** | `DELETE` |
| **Path** | `/api/admin/events/{event_id}` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Delete an event. Only draft events can be deleted. |

**Response (200 OK):**
```json
{
  "message": "Event deleted successfully"
}
```

---

### 13.10 List Seat Categories

| Field | Value |
|-------|-------|
| **API Name** | Admin List Seat Categories |
| **Method** | `GET` |
| **Path** | `/api/admin/events/{event_id}/categories` |
| **Auth** | Bearer Token (Admin) |
| **Description** | List all seat categories for an event (includes inactive). |

**Response (200 OK):** `list[SeatCategoryResponse]`

---

### 13.11 Create Seat Category

| Field | Value |
|-------|-------|
| **API Name** | Admin Create Seat Category |
| **Method** | `POST` |
| **Path** | `/api/admin/events/{event_id}/categories` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Create a new seat category (pricing tier) for an event. |

**Request Body:**
```json
{
  "name": "VIP",
  "description": "Front row VIP seats",
  "price": 5000.00,
  "totalSeats": 100,
  "displayOrder": 1,
  "colorCode": "#FFD700"
}
```

**Response (201 Created):** `SeatCategoryResponse`

---

### 13.12 Update Seat Category

| Field | Value |
|-------|-------|
| **API Name** | Admin Update Seat Category |
| **Method** | `PATCH` |
| **Path** | `/api/admin/events/categories/{category_id}` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Update a seat category. |

**Request Body (all optional):**
```json
{
  "name": "Super VIP",
  "price": 7500.00,
  "totalSeats": 150,
  "isActive": true
}
```

**Response (200 OK):** Updated `SeatCategoryResponse`.

---

### 13.13 Delete Seat Category

| Field | Value |
|-------|-------|
| **API Name** | Admin Delete Seat Category |
| **Method** | `DELETE` |
| **Path** | `/api/admin/events/categories/{category_id}` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Delete a seat category. Only possible if no seats have been sold. |

**Response (200 OK):**
```json
{
  "message": "Category deleted successfully"
}
```

---

## 14. Admin - Venues

**File Path:** `backend/src/api/routes/admin/venues.py`
**Auth:** Bearer Token (Admin role required)

### 14.1 List Venues

| Field | Value |
|-------|-------|
| **API Name** | Admin List Venues |
| **Method** | `GET` |
| **Path** | `/api/admin/venues` |
| **Auth** | Bearer Token (Admin) |
| **Description** | List all venues with filters and pagination. |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Items per page |
| `city` | string | - | Filter by city |
| `is_active` | bool | - | Filter by active status |
| `search` | string | - | Search by name |

**Response (200 OK):**
```json
{
  "venues": [
    {
      "id": 1,
      "name": "Stadium Arena",
      "address": "123 Main St",
      "city": "Mumbai",
      "state": "Maharashtra",
      "country": "India",
      "pincode": "400001",
      "capacity": 50000,
      "contactPhone": "+91222222222",
      "contactEmail": "info@stadium.com",
      "isActive": true,
      "createdAt": "2026-01-01T00:00:00",
      "updatedAt": null
    }
  ],
  "total": 10,
  "page": 1,
  "pageSize": 20
}
```

---

### 14.2 Get All Active Venues

| Field | Value |
|-------|-------|
| **API Name** | Admin All Venues |
| **Method** | `GET` |
| **Path** | `/api/admin/venues/all` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Get all active venues (for dropdown selectors). |

**Response (200 OK):** `list[VenueResponse]`

---

### 14.3 Create Venue

| Field | Value |
|-------|-------|
| **API Name** | Admin Create Venue |
| **Method** | `POST` |
| **Path** | `/api/admin/venues` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Create a new venue. |

**Request Body:**
```json
{
  "name": "Stadium Arena",
  "address": "123 Main St",
  "city": "Mumbai",
  "state": "Maharashtra",
  "country": "India",
  "pincode": "400001",
  "capacity": 50000,
  "seatMapConfig": { "layout": "stadium" },
  "contactPhone": "+91222222222",
  "contactEmail": "info@stadium.com"
}
```

**Response (201 Created):** `VenueDetailResponse` (includes `seatMapConfig`).

---

### 14.4 Get Venue

| Field | Value |
|-------|-------|
| **API Name** | Admin Get Venue |
| **Method** | `GET` |
| **Path** | `/api/admin/venues/{venue_id}` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Get full venue details including seat map config. |

**Response (200 OK):** `VenueDetailResponse`

---

### 14.5 Update Venue

| Field | Value |
|-------|-------|
| **API Name** | Admin Update Venue |
| **Method** | `PATCH` |
| **Path** | `/api/admin/venues/{venue_id}` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Update venue details. All fields are optional. |

**Request Body:** Same fields as Create, all optional. Also accepts `isActive: bool`.

**Response (200 OK):** Updated `VenueDetailResponse`.

---

### 14.6 Delete Venue

| Field | Value |
|-------|-------|
| **API Name** | Admin Delete Venue |
| **Method** | `DELETE` |
| **Path** | `/api/admin/venues/{venue_id}` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Delete a venue. Soft delete by default (sets isActive=false). |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `permanent` | bool | false | Hard delete if true |

**Response (200 OK):**
```json
{
  "message": "Venue deactivated successfully"
}
```

---

## 15. Admin - Seats

**File Path:** `backend/src/api/routes/admin/seats.py`
**Auth:** Bearer Token (Admin role required)

### 15.1 List Event Seats

| Field | Value |
|-------|-------|
| **API Name** | Admin List Seats |
| **Method** | `GET` |
| **Path** | `/api/admin/seats/event/{event_id}` |
| **Auth** | Bearer Token (Admin) |
| **Description** | List all seats for an event with optional filters. |

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `category_id` | int | Filter by category |
| `status` | string | Filter: available, locked, booked, blocked |

**Response (200 OK):** `list[SeatResponse]`

---

### 15.2 Get Seat Counts

| Field | Value |
|-------|-------|
| **API Name** | Admin Seat Counts |
| **Method** | `GET` |
| **Path** | `/api/admin/seats/event/{event_id}/counts` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Get seat counts by status for an event. |

**Response (200 OK):**
```json
{
  "available": 3200,
  "locked": 50,
  "booked": 1700,
  "blocked": 50
}
```

---

### 15.3 Create Single Seat

| Field | Value |
|-------|-------|
| **API Name** | Admin Create Seat |
| **Method** | `POST` |
| **Path** | `/api/admin/seats/event/{event_id}` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Create a single seat for an event. |

**Request Body:**
```json
{
  "categoryId": 1,
  "seatNumber": "A-1",
  "rowName": "A",
  "section": "Front",
  "positionX": 0,
  "positionY": 0
}
```

**Response (201 Created):** `SeatResponse`

---

### 15.4 Bulk Create Seats

| Field | Value |
|-------|-------|
| **API Name** | Admin Bulk Create Seats |
| **Method** | `POST` |
| **Path** | `/api/admin/seats/event/{event_id}/bulk` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Bulk create seats by specifying rows and seats per row (e.g., A1-A10, B1-B10). |

**Request Body:**
```json
{
  "categoryId": 1,
  "section": "Main Hall",
  "rows": ["A", "B", "C", "D"],
  "seatsPerRow": 20
}
```

**Response (201 Created):**
```json
{
  "message": "80 seats created successfully",
  "count": 80
}
```

---

### 15.5 Get Seat

| Field | Value |
|-------|-------|
| **API Name** | Admin Get Seat |
| **Method** | `GET` |
| **Path** | `/api/admin/seats/{seat_id}` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Get details of a specific seat. |

**Response (200 OK):** `SeatResponse`

---

### 15.6 Update Seat

| Field | Value |
|-------|-------|
| **API Name** | Admin Update Seat |
| **Method** | `PATCH` |
| **Path** | `/api/admin/seats/{seat_id}` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Update seat details. |

**Request Body (all optional):**
```json
{
  "categoryId": 2,
  "seatNumber": "A-1",
  "rowName": "A",
  "section": "VIP",
  "status": "blocked",
  "positionX": 10,
  "positionY": 5
}
```

**Response (200 OK):** Updated `SeatResponse`.

---

### 15.7 Block Seat

| Field | Value |
|-------|-------|
| **API Name** | Admin Block Seat |
| **Method** | `POST` |
| **Path** | `/api/admin/seats/{seat_id}/block` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Block a seat (mark as not available for sale). |

**Response (200 OK):** Updated `SeatResponse` with `status: "blocked"`.

---

### 15.8 Unblock Seat

| Field | Value |
|-------|-------|
| **API Name** | Admin Unblock Seat |
| **Method** | `POST` |
| **Path** | `/api/admin/seats/{seat_id}/unblock` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Unblock a seat (make it available for sale). |

**Response (200 OK):** Updated `SeatResponse` with `status: "available"`.

---

### 15.9 Release Seat Lock

| Field | Value |
|-------|-------|
| **API Name** | Admin Release Seat |
| **Method** | `POST` |
| **Path** | `/api/admin/seats/{seat_id}/release` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Force release a locked seat (admin override). |

**Response (200 OK):** Updated `SeatResponse` with `status: "available"`.

---

### 15.10 Delete Seat

| Field | Value |
|-------|-------|
| **API Name** | Admin Delete Seat |
| **Method** | `DELETE` |
| **Path** | `/api/admin/seats/{seat_id}` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Delete a seat. Only available/blocked seats can be deleted. |

**Response (200 OK):**
```json
{
  "message": "Seat deleted successfully"
}
```

---

### 15.11 Release Expired Seat Locks

| Field | Value |
|-------|-------|
| **API Name** | Admin Release Expired Locks |
| **Method** | `POST` |
| **Path** | `/api/admin/seats/release-expired` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Maintenance: Release all expired seat locks across all events. |

**Response (200 OK):**
```json
{
  "message": "Released 5 expired seat locks",
  "count": 5
}
```

---

## 16. Admin - Bookings

**File Path:** `backend/src/api/routes/admin/bookings.py`
**Auth:** Bearer Token (Admin role required)

### 16.1 List All Bookings

| Field | Value |
|-------|-------|
| **API Name** | Admin List Bookings |
| **Method** | `GET` |
| **Path** | `/api/admin/bookings` |
| **Auth** | Bearer Token (Admin) |
| **Description** | List all bookings across all users with comprehensive filters. |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Items per page (max 100) |
| `status` | string | - | confirmed, pending, cancelled |
| `payment_status` | string | - | paid, pending, failed, refunded |
| `event_id` | int | - | Filter by event |
| `user_id` | int | - | Filter by user |
| `search` | string | - | Search booking number |
| `date_from` | date | - | From date |
| `date_to` | date | - | To date |

**Response (200 OK):** `BookingListResponse`

---

### 16.2 Booking Stats

| Field | Value |
|-------|-------|
| **API Name** | Admin Booking Stats |
| **Method** | `GET` |
| **Path** | `/api/admin/bookings/stats` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Get booking statistics. Optionally filter by event. |

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `event_id` | int | Optional event filter |

**Response (200 OK):**
```json
{
  "total": 500,
  "confirmed": 420,
  "pending": 30,
  "cancelled": 50,
  "revenue": 2500000.00,
  "ticketsSold": 1200
}
```

---

### 16.3 Sales Analytics

| Field | Value |
|-------|-------|
| **API Name** | Admin Sales Analytics |
| **Method** | `GET` |
| **Path** | `/api/admin/bookings/analytics` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Get sales analytics with daily breakdown for a given period. |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `period` | string | 7d | 7d, 30d, 90d, or 1y |
| `event_id` | int | - | Optional event filter |

**Response (200 OK):** `SalesAnalyticsResponse`

---

### 16.4 Top Events

| Field | Value |
|-------|-------|
| **API Name** | Admin Top Events |
| **Method** | `GET` |
| **Path** | `/api/admin/bookings/top-events` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Get top events by revenue. |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 10 | Number of events (max 50) |
| `period` | string | 30d | 7d, 30d, 90d, 1y, or all |

**Response (200 OK):** `TopEventsResponse`

---

### 16.5 Get Booking Details (Admin)

| Field | Value |
|-------|-------|
| **API Name** | Admin Get Booking |
| **Method** | `GET` |
| **Path** | `/api/admin/bookings/{booking_id}` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Get detailed booking information including user and payment details. |

**Response (200 OK):** `AdminBookingResponse`

---

### 16.6 Event Attendees

| Field | Value |
|-------|-------|
| **API Name** | Admin Event Attendees |
| **Method** | `GET` |
| **Path** | `/api/admin/bookings/event/{event_id}/attendees` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Get attendee list for an event with check-in status. |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 50 | Items per page (max 200) |
| `search` | string | - | Search attendees |

**Response (200 OK):**
```json
{
  "attendees": [
    {
      "id": 1,
      "bookingNumber": "BK-20260219-ABC123",
      "userEmail": "john@example.com",
      "userName": "John Doe",
      "eventTitle": "Music Festival 2026",
      "amount": 10000.00,
      "status": "confirmed",
      "paymentStatus": "paid",
      "ticketCount": 2,
      "createdAt": "2026-02-19T10:05:00"
    }
  ],
  "total": 420,
  "page": 1,
  "pageSize": 50
}
```

---

## 17. Admin - Activity Logs

**File Path:** `backend/src/api/routes/admin/logs.py`
**Auth:** Bearer Token (Admin role required)

### 17.1 List Activity Logs

| Field | Value |
|-------|-------|
| **API Name** | Admin List Logs |
| **Method** | `GET` |
| **Path** | `/api/admin/logs` |
| **Auth** | Bearer Token (Admin) |
| **Description** | List admin activity logs with filters and pagination. |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Items per page |
| `admin_id` | int | - | Filter by admin |
| `action` | string | - | Filter by action type |
| `entity_type` | string | - | Filter by entity type |
| `start_date` | datetime | - | From date |
| `end_date` | datetime | - | To date |

**Response (200 OK):**
```json
{
  "logs": [
    {
      "id": 1,
      "adminId": 1,
      "adminUsername": "admin",
      "action": "create_event",
      "entityType": "event",
      "entityId": 5,
      "details": { "title": "Music Festival 2026" },
      "ipAddress": "192.168.1.1",
      "createdAt": "2026-02-19T10:00:00"
    }
  ],
  "total": 250,
  "page": 1,
  "pageSize": 20
}
```

---

### 17.2 Get Activity Log Details

| Field | Value |
|-------|-------|
| **API Name** | Admin Get Log |
| **Method** | `GET` |
| **Path** | `/api/admin/logs/{log_id}` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Get details of a specific activity log entry. |

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `log_id` | int | Log entry ID |

**Response (200 OK):** Single `AdminActivityLogView` object.

---

## 18. Admin - Dashboard

**File Path:** `backend/src/api/routes/admin/dashboard.py`
**Auth:** Bearer Token (Admin role required)

### 18.1 Dashboard Overview

| Field | Value |
|-------|-------|
| **API Name** | Admin Dashboard Overview |
| **Method** | `GET` |
| **Path** | `/api/admin/dashboard/overview` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Get comprehensive dashboard stats including users, events, bookings, revenue, and growth. |

**Response (200 OK):**
```json
{
  "users": {
    "total": 1500,
    "today": 12,
    "thisWeek": 85,
    "thisMonth": 320
  },
  "events": {
    "total": 25,
    "active": 15,
    "completed": 5,
    "upcoming": 5
  },
  "bookings": {
    "total": 500,
    "today": 25,
    "thisWeek": 150,
    "thisMonth": 420
  },
  "revenue": {
    "total": 2500000.00,
    "today": 125000.00,
    "thisWeek": 750000.00,
    "thisMonth": 2100000.00
  },
  "tickets": {
    "total": 1200,
    "today": 50,
    "thisWeek": 300,
    "thisMonth": 950
  },
  "growth": {
    "usersPercent": 12.5,
    "bookingsPercent": 8.3,
    "revenuePercent": 15.2
  }
}
```

---

### 18.2 Revenue Chart

| Field | Value |
|-------|-------|
| **API Name** | Admin Revenue Chart |
| **Method** | `GET` |
| **Path** | `/api/admin/dashboard/revenue-chart` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Get daily revenue data for chart rendering. |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `period` | string | week | week, month, or quarter |

**Response (200 OK):**
```json
{
  "data": [
    {
      "date": "2026-02-13",
      "revenue": 125000.00,
      "bookings": 25
    },
    {
      "date": "2026-02-14",
      "revenue": 150000.00,
      "bookings": 30
    }
  ]
}
```

---

### 18.3 Recent Bookings

| Field | Value |
|-------|-------|
| **API Name** | Admin Recent Bookings |
| **Method** | `GET` |
| **Path** | `/api/admin/dashboard/recent-bookings` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Get recent bookings for the dashboard. |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 10 | Number of bookings (max 50) |

**Response (200 OK):**
```json
{
  "bookings": [
    {
      "id": 500,
      "bookingNumber": "BK-20260219-XYZ789",
      "userEmail": "user@example.com",
      "userName": "Jane Smith",
      "eventTitle": "Music Festival 2026",
      "amount": 5000.00,
      "status": "confirmed",
      "paymentStatus": "paid",
      "ticketCount": 1,
      "createdAt": "2026-02-19T09:30:00"
    }
  ]
}
```

---

### 18.4 Upcoming Events

| Field | Value |
|-------|-------|
| **API Name** | Admin Upcoming Events |
| **Method** | `GET` |
| **Path** | `/api/admin/dashboard/upcoming-events` |
| **Auth** | Bearer Token (Admin) |
| **Description** | Get upcoming events with booking/ticket counts for the dashboard. |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 5 | Number of events (max 20) |

**Response (200 OK):**
```json
{
  "events": [
    {
      "id": 1,
      "title": "Music Festival 2026",
      "eventDate": "2026-03-15T18:00:00",
      "status": "published",
      "totalSeats": 5000,
      "availableSeats": 3200,
      "bookings": 420,
      "ticketsSold": 1800
    }
  ]
}
```

---

## 19. Accounts (Legacy)

**File Path:** `backend/src/api/routes/account.py`

> **Note:** These are legacy endpoints primarily for development/debugging. Use the Auth and User endpoints for production.

### 19.1 List All Accounts

| Field | Value |
|-------|-------|
| **API Name** | List Accounts |
| **Method** | `GET` |
| **Path** | `/api/accounts` |
| **Auth** | None |
| **Description** | List all accounts (development endpoint). |

**Response (200 OK):** `list[AccountInResponse]`

---

### 19.2 Get Account by ID

| Field | Value |
|-------|-------|
| **API Name** | Get Account |
| **Method** | `GET` |
| **Path** | `/api/accounts/{id}` |
| **Auth** | None |
| **Description** | Get account by ID. |

**Response (200 OK):** `AccountInResponse`

---

### 19.3 Update Account

| Field | Value |
|-------|-------|
| **API Name** | Update Account |
| **Method** | `PATCH` |
| **Path** | `/api/accounts/{id}` |
| **Auth** | None |
| **Description** | Update account via query parameters. |

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `query_id` | int | Account ID |
| `update_username` | string | New username |
| `update_email` | string | New email |
| `update_password` | string | New password |

**Response (200 OK):** `AccountInResponse`

---

### 19.4 Delete Account

| Field | Value |
|-------|-------|
| **API Name** | Delete Account |
| **Method** | `DELETE` |
| **Path** | `/api/accounts` |
| **Auth** | None |
| **Description** | Delete an account. |

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | int | Account ID to delete |

**Response (200 OK):**
```json
{
  "notification": "Account deleted"
}
```

---

## API Quick Reference

| # | API Name | Method | Path | Auth |
|---|----------|--------|------|------|
| **Authentication** | | | | |
| 1 | Sign Up | `POST` | `/api/auth/signup` | No |
| 2 | Sign In | `POST` | `/api/auth/signin` | No |
| 3 | Send Email OTP | `POST` | `/api/auth/email-otp/send` | No |
| 4 | Verify Email OTP | `POST` | `/api/auth/email-otp/verify` | No |
| **User Profile** | | | | |
| 5 | Get Profile | `GET` | `/api/users/me` | User |
| 6 | Update Profile | `PATCH` | `/api/users/me` | User |
| 7 | Send Phone OTP | `POST` | `/api/users/me/verify-phone` | User |
| 8 | Confirm Phone | `POST` | `/api/users/me/verify-phone/confirm` | User |
| 9 | Send Email OTP | `POST` | `/api/users/me/verify-email` | User |
| 10 | Confirm Email | `POST` | `/api/users/me/verify-email/confirm` | User |
| **Events** | | | | |
| 11 | List Events | `GET` | `/api/events` | No |
| 12 | Search Events | `GET` | `/api/events/search` | No |
| 13 | Upcoming Events | `GET` | `/api/events/upcoming` | No |
| 14 | Event Categories (Enum) | `GET` | `/api/events/categories` | No |
| 15 | Get Event | `GET` | `/api/events/{event_id_or_slug}` | No |
| 16 | Get Seat Categories | `GET` | `/api/events/{event_id}/categories` | No |
| 17 | Get Seats | `GET` | `/api/events/{event_id}/seats` | No |
| **Cart** | | | | |
| 18 | Create/Get Cart | `POST` | `/api/cart` | User |
| 19 | Add Item | `POST` | `/api/cart/items` | User |
| 20 | Update Item | `PATCH` | `/api/cart/items/{item_id}` | User |
| 21 | Remove Item | `DELETE` | `/api/cart/items/{item_id}` | User |
| 22 | Validate Cart | `GET` | `/api/cart/validate` | User |
| 23 | Checkout | `POST` | `/api/cart/checkout` | User |
| 24 | Current Cart | `GET` | `/api/cart/current` | User |
| 25 | Clear Cart | `DELETE` | `/api/cart/clear` | User |
| 26 | Cart Count | `GET` | `/api/cart/count` | User |
| **Bookings** | | | | |
| 27 | List Bookings | `GET` | `/api/users/me/bookings` | User |
| 28 | Get Booking | `GET` | `/api/bookings/{booking_id}` | User |
| 29 | Get Booking by Number | `GET` | `/api/bookings/number/{booking_number}` | User |
| 30 | Cancel Booking | `POST` | `/api/bookings/{booking_id}/cancel` | User |
| **Payments** | | | | |
| 31 | Create Order | `POST` | `/api/payments/create-order` | User |
| 32 | Verify Payment | `POST` | `/api/payments/verify` | User |
| 33 | Webhook | `POST` | `/api/payments/webhook` | Webhook |
| 34 | Get Payment | `GET` | `/api/payments/{payment_id}` | User |
| 35 | Cancel Pending Booking | `POST` | `/api/payments/booking/{booking_id}/cancel` | User |
| 36 | Payment Status | `GET` | `/api/payments/booking/{booking_id}/status` | User |
| **Tickets** | | | | |
| 37 | Get Ticket | `GET` | `/api/tickets/{ticket_id}` | User |
| 38 | Download Ticket PDF | `GET` | `/api/tickets/{ticket_id}/download` | User |
| 39 | Mark Used | `POST` | `/api/tickets/mark-used` | Admin |
| 40 | Transfer | `POST` | `/api/tickets/{ticket_id}/transfer` | User |
| 41 | Claim Transfer | `POST` | `/api/tickets/claim` | User |
| 42 | Cancel Transfer | `POST` | `/api/tickets/transfers/{transfer_id}/cancel` | User |
| 43 | Transfer History | `GET` | `/api/tickets/transfers/history` | User |
| 44 | Get Booking Tickets | `GET` | `/api/tickets/booking/{booking_id}` | User |
| **Queue** | | | | |
| 45 | Join Queue | `POST` | `/api/queue/{event_id}/join` | User |
| 46 | Get Position | `GET` | `/api/queue/{event_id}/position` | User |
| 47 | Queue Status | `GET` | `/api/queue/{event_id}/status` | No |
| 48 | Leave Queue | `DELETE` | `/api/queue/{event_id}/leave` | User |
| **Wishlist** | | | | |
| 49 | Get Wishlist | `GET` | `/api/users/me/wishlist` | User |
| 50 | Add to Wishlist | `POST` | `/api/users/me/wishlist/{event_id}` | User |
| 51 | Remove from Wishlist | `DELETE` | `/api/users/me/wishlist/{event_id}` | User |
| 52 | Check Wishlist | `GET` | `/api/users/me/wishlist/{event_id}/check` | User |
| **Notifications** | | | | |
| 53 | Get Preferences | `GET` | `/api/users/me/notifications/preferences` | User |
| 54 | Update Preferences | `PATCH` | `/api/users/me/notifications/preferences` | User |
| **WebSocket** | | | | |
| 55 | Queue Updates | `WS` | `/api/ws/queue/{event_id}?token=<jwt>` | JWT |
| **Admin - Users** | | | | |
| 56 | List Users | `GET` | `/api/admin/users` | Admin |
| 57 | User Stats | `GET` | `/api/admin/users/stats` | Admin |
| 58 | Get User | `GET` | `/api/admin/users/{user_id}` | Admin |
| 59 | Block User | `POST` | `/api/admin/users/{user_id}/block` | Admin |
| 60 | Unblock User | `POST` | `/api/admin/users/{user_id}/unblock` | Admin |
| **Admin - Events** | | | | |
| 61 | List Events | `GET` | `/api/admin/events` | Admin |
| 62 | Create Event | `POST` | `/api/admin/events` | Admin |
| 63 | Event Stats | `GET` | `/api/admin/events/stats` | Admin |
| 64 | Get Event | `GET` | `/api/admin/events/{event_id}` | Admin |
| 65 | Update Event | `PATCH` | `/api/admin/events/{event_id}` | Admin |
| 66 | Publish Event | `POST` | `/api/admin/events/{event_id}/publish` | Admin |
| 67 | Cancel Event | `POST` | `/api/admin/events/{event_id}/cancel` | Admin |
| 68 | Reactivate Event | `POST` | `/api/admin/events/{event_id}/reactivate` | Admin |
| 69 | Delete Event | `DELETE` | `/api/admin/events/{event_id}` | Admin |
| 70 | List Categories | `GET` | `/api/admin/events/{event_id}/categories` | Admin |
| 71 | Create Category | `POST` | `/api/admin/events/{event_id}/categories` | Admin |
| 72 | Update Category | `PATCH` | `/api/admin/events/categories/{category_id}` | Admin |
| 73 | Delete Category | `DELETE` | `/api/admin/events/categories/{category_id}` | Admin |
| **Admin - Venues** | | | | |
| 74 | List Venues | `GET` | `/api/admin/venues` | Admin |
| 75 | All Venues | `GET` | `/api/admin/venues/all` | Admin |
| 76 | Create Venue | `POST` | `/api/admin/venues` | Admin |
| 77 | Get Venue | `GET` | `/api/admin/venues/{venue_id}` | Admin |
| 78 | Update Venue | `PATCH` | `/api/admin/venues/{venue_id}` | Admin |
| 79 | Delete Venue | `DELETE` | `/api/admin/venues/{venue_id}` | Admin |
| **Admin - Seats** | | | | |
| 80 | List Seats | `GET` | `/api/admin/seats/event/{event_id}` | Admin |
| 81 | Seat Counts | `GET` | `/api/admin/seats/event/{event_id}/counts` | Admin |
| 82 | Create Seat | `POST` | `/api/admin/seats/event/{event_id}` | Admin |
| 83 | Bulk Create | `POST` | `/api/admin/seats/event/{event_id}/bulk` | Admin |
| 84 | Get Seat | `GET` | `/api/admin/seats/{seat_id}` | Admin |
| 85 | Update Seat | `PATCH` | `/api/admin/seats/{seat_id}` | Admin |
| 86 | Block Seat | `POST` | `/api/admin/seats/{seat_id}/block` | Admin |
| 87 | Unblock Seat | `POST` | `/api/admin/seats/{seat_id}/unblock` | Admin |
| 88 | Release Seat | `POST` | `/api/admin/seats/{seat_id}/release` | Admin |
| 89 | Delete Seat | `DELETE` | `/api/admin/seats/{seat_id}` | Admin |
| 90 | Release Expired | `POST` | `/api/admin/seats/release-expired` | Admin |
| **Admin - Bookings** | | | | |
| 91 | List Bookings | `GET` | `/api/admin/bookings` | Admin |
| 92 | Booking Stats | `GET` | `/api/admin/bookings/stats` | Admin |
| 93 | Sales Analytics | `GET` | `/api/admin/bookings/analytics` | Admin |
| 94 | Top Events | `GET` | `/api/admin/bookings/top-events` | Admin |
| 95 | Get Booking | `GET` | `/api/admin/bookings/{booking_id}` | Admin |
| 96 | Event Attendees | `GET` | `/api/admin/bookings/event/{event_id}/attendees` | Admin |
| **Admin - Logs** | | | | |
| 97 | List Logs | `GET` | `/api/admin/logs` | Admin |
| 98 | Get Log | `GET` | `/api/admin/logs/{log_id}` | Admin |
| **Admin - Dashboard** | | | | |
| 99 | Overview | `GET` | `/api/admin/dashboard/overview` | Admin |
| 100 | Revenue Chart | `GET` | `/api/admin/dashboard/revenue-chart` | Admin |
| 101 | Recent Bookings | `GET` | `/api/admin/dashboard/recent-bookings` | Admin |
| 102 | Upcoming Events | `GET` | `/api/admin/dashboard/upcoming-events` | Admin |

---

## Error Response Format

All error responses follow this standard format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `400` - Bad Request (validation error, business logic error)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions, e.g., non-admin accessing admin routes)
- `404` - Not Found (resource doesn't exist)
- `422` - Unprocessable Entity (Pydantic validation failure)

---

## Authentication Guide

1. **Sign up** using `POST /api/auth/signup` or use **Email OTP flow** (`send` then `verify`)
2. Copy the `token` from the response
3. Add to Postman: `Authorization` header as `Bearer <token>`
4. All authenticated endpoints require this header

**Admin Access:** The admin account is seeded during first startup. Use admin credentials to sign in and access `/api/admin/*` endpoints.

---

## Booking & Payment Flow

The complete ticket booking flow works as follows:

```
1. Browse Events          GET  /api/events
2. View Event Details     GET  /api/events/{event_id}
3. View Seat Categories   GET  /api/events/{event_id}/categories
4. View Available Seats   GET  /api/events/{event_id}/seats
        │
        ▼
5. Create Cart            POST /api/cart                    { eventId }
6. Add Items to Cart      POST /api/cart/items              { eventId, seatCategoryId, quantity, seatIds? }
   (seats get locked for 7 min, cart expires in 15 min)
7. Validate Cart          GET  /api/cart/validate
        │
        ▼
8. Checkout               POST /api/cart/checkout           { contactEmail?, contactPhone? }
   (converts cart → booking with status "pending", generates ticket numbers)
        │
        ▼
9. Create Payment Order   POST /api/payments/create-order   { bookingId }
   (returns Razorpay order details for frontend checkout widget)
        │
        ▼
10. [Frontend opens Razorpay checkout]
        │
        ▼
11. Verify Payment        POST /api/payments/verify         { razorpayOrderId, razorpayPaymentId, razorpaySignature }
    (confirms payment, sends email confirmation)
        │
        ▼
12. View Tickets          GET  /api/tickets/booking/{booking_id}
13. Download Ticket PDF   GET  /api/tickets/{ticket_id}/download
```

**Alternative paths:**
- **Cancel before payment:** `POST /api/payments/booking/{booking_id}/cancel` (releases seats)
- **Cancel after payment:** `POST /api/bookings/{booking_id}/cancel`
- **Check payment status:** `GET /api/payments/booking/{booking_id}/status`
- **Transfer ticket:** `POST /api/tickets/{ticket_id}/transfer`
- **Webhook (async):** Razorpay sends `POST /api/payments/webhook` for payment.captured/failed events
