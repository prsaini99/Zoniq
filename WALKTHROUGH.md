# Platform Walkthrough - Event Booking & Ticketing System

A detailed guide to understand the codebase, set it up locally, and explore every feature.

---

## Table of Contents

1. [Platform Overview](#1-platform-overview)
2. [Architecture & Tech Stack](#2-architecture--tech-stack)
3. [Project Structure](#3-project-structure)
4. [Local Setup](#4-local-setup)
   - [Option A: Docker (Recommended)](#option-a-docker-recommended)
   - [Option B: Manual Setup (Without Docker)](#option-b-manual-setup-without-docker)
5. [Configuration Deep Dive](#5-configuration-deep-dive)
6. [Database Schema & Models](#6-database-schema--models)
7. [Feature Walkthrough](#7-feature-walkthrough)
   - [7.1 Authentication & Users](#71-authentication--users)
   - [7.2 Events & Venues](#72-events--venues)
   - [7.3 Seat Management](#73-seat-management)
   - [7.4 Cart System](#74-cart-system)
   - [7.5 Booking Flow](#75-booking-flow)
   - [7.6 Payment Integration (Razorpay)](#76-payment-integration-razorpay)
   - [7.7 Ticket System](#77-ticket-system)
   - [7.8 Virtual Queue System](#78-virtual-queue-system)
   - [7.9 Notifications & Email](#79-notifications--email)
   - [7.10 Wishlist](#710-wishlist)
   - [7.11 Admin Panel](#711-admin-panel)
8. [End-to-End Booking Flow](#8-end-to-end-booking-flow)
9. [Code Patterns & Conventions](#9-code-patterns--conventions)
10. [Testing](#10-testing)
11. [Deployment](#11-deployment)
12. [Where to Continue](#12-where-to-continue)

---

## 1. Platform Overview

This is a **full-stack event booking and ticketing platform** (think BookMyShow / Eventbrite) built with FastAPI. Users can browse events, select seats, book tickets, pay via Razorpay, and receive PDF tickets by email.

**What it does:**
- Users sign up via email OTP or password, browse published events
- Events have venues, seat categories (VIP, General, etc.), and individual seats
- Users add tickets to a cart with seat locking, then checkout to create a booking
- Payments are processed through Razorpay (Indian payment gateway)
- PDF tickets are generated and emailed after payment
- High-demand events use a virtual queue with WebSocket real-time updates
- Users can transfer tickets to others via email
- Admins manage events, venues, users, and view analytics

---

## 2. Architecture & Tech Stack

```
┌─────────────┐     ┌──────────────────────────────────────────────────┐
│   Frontend   │────▶│                   Backend (FastAPI)              │
│  (Next.js)   │     │                                                  │
│  Port: 3000  │     │  Routes → Services → CRUD Repos → Database      │
└─────────────┘     │                                                  │
                     │  Background Workers (Queue Processor)            │
                     │  WebSocket Manager (Real-time Queue Updates)     │
                     │  Port: 8000 (local) / 8001 (Docker)             │
                     └──────────────┬──────────────┬───────────────────┘
                                    │              │
                            ┌───────▼──────┐  ┌───▼────────┐
                            │  PostgreSQL   │  │  Razorpay   │
                            │  (AsyncPG)    │  │  (Payments) │
                            │  Port: 5432   │  └────────────┘
                            └──────────────┘
```

**Core Stack:**
| Layer | Technology |
|-------|-----------|
| Framework | FastAPI (async Python) |
| Database | PostgreSQL with AsyncPG driver |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Auth | JWT (HS256) with two-layer password hashing (Bcrypt + Argon2) |
| Payments | Razorpay SDK |
| Email | aiosmtplib + Jinja2 templates |
| PDF Generation | ReportLab |
| Real-time | WebSocket (native FastAPI) |
| Containerization | Docker + Docker Compose |
| Frontend | Next.js (separate container) |

---

## 3. Project Structure

```
FastAPI-Backend-Template/
├── .env                              # Environment variables (create from .env.example)
├── .env.example                      # Template for env vars
├── docker-compose.yaml               # Dev: PostgreSQL + Adminer + Backend
├── docker-compose.prod.yaml          # Prod: + Nginx + Frontend
├── deploy.sh                         # One-click deployment script
│
├── backend/
│   ├── Dockerfile
│   ├── entrypoint.sh                 # Waits for DB → runs migrations → seeds admin
│   ├── requirements.txt              # Python dependencies
│   ├── alembic.ini                   # Migration config
│   │
│   └── src/
│       ├── main.py                   # App entry point (CORS, routers, lifecycle)
│       │
│       ├── config/
│       │   ├── manager.py            # Settings factory (DEV/STAGE/PROD)
│       │   ├── events.py             # Startup: DB init, queue processor start
│       │   └── settings/
│       │       ├── base.py           # All env vars defined here
│       │       ├── development.py    # DEBUG=True
│       │       ├── staging.py        # DEBUG=True, STAGE env
│       │       └── production.py     # DEBUG=False
│       │
│       ├── api/
│       │   ├── endpoints.py          # Router registration (all routes aggregated)
│       │   ├── dependencies/
│       │   │   ├── auth.py           # get_current_user, require_admin
│       │   │   ├── session.py        # Async DB session dependency
│       │   │   └── repository.py     # Generic CRUD repo factory
│       │   └── routes/
│       │       ├── authentication.py # Signup, signin, email OTP
│       │       ├── users.py          # Profile, phone/email verification
│       │       ├── events.py         # Public event browsing
│       │       ├── cart.py           # Cart CRUD + checkout
│       │       ├── bookings.py       # User bookings
│       │       ├── payments.py       # Razorpay order/verify/webhook
│       │       ├── tickets.py        # Ticket details, PDF, transfers
│       │       ├── queue.py          # Virtual queue join/leave/status
│       │       ├── wishlist.py       # Event wishlist
│       │       ├── notifications.py  # Notification preferences
│       │       ├── websocket.py      # WebSocket for queue updates
│       │       ├── account.py        # Legacy CRUD endpoints
│       │       └── admin/
│       │           ├── users.py      # Block/unblock, stats
│       │           ├── events.py     # Create/publish/cancel events
│       │           ├── venues.py     # Venue management
│       │           ├── seats.py      # Seat CRUD, bulk create
│       │           ├── bookings.py   # View bookings, analytics
│       │           ├── logs.py       # Admin activity logs
│       │           └── dashboard.py  # Overview, charts, recent activity
│       │
│       ├── models/
│       │   ├── db/                   # SQLAlchemy table models
│       │   │   ├── account.py        # User accounts with roles
│       │   │   ├── event.py          # Events with full-text search
│       │   │   ├── venue.py          # Venues with capacity
│       │   │   ├── seat_category.py  # Pricing tiers (VIP, General, etc.)
│       │   │   ├── seat.py           # Individual seats with lock mechanism
│       │   │   ├── cart.py           # Cart + CartItem with expiry
│       │   │   ├── booking.py        # Booking + BookingItem with tickets
│       │   │   ├── payment.py        # Razorpay payment records
│       │   │   ├── queue_entry.py    # Virtual queue entries
│       │   │   ├── ticket_transfer.py # Ticket transfer tokens
│       │   │   ├── notification_preference.py  # Email preferences
│       │   │   ├── wishlist.py       # User event wishlist
│       │   │   ├── otp.py           # OTP codes for verification
│       │   │   └── admin_activity_log.py  # Admin audit trail
│       │   └── schemas/              # Pydantic request/response models
│       │       ├── base.py           # BaseSchemaModel (camelCase aliases)
│       │       ├── account.py, booking.py, cart.py, event.py, ...
│       │
│       ├── repository/
│       │   ├── database.py           # AsyncDatabase class (engine + session)
│       │   ├── events.py             # DB lifecycle (init tables, seed admin)
│       │   ├── table.py              # SQLAlchemy Base class
│       │   ├── base.py               # Table registration for Alembic
│       │   ├── migrations/           # Alembic migration versions
│       │   └── crud/                 # CRUD repositories
│       │       ├── base.py           # BaseCRUDRepository
│       │       ├── account.py        # User operations
│       │       ├── event.py          # Event operations + full-text search
│       │       ├── cart.py           # Cart with seat locking
│       │       ├── booking.py        # Booking from cart
│       │       ├── payment.py        # Payment tracking
│       │       ├── seat.py           # Seat status management
│       │       ├── queue.py          # Queue operations (FOR UPDATE SKIP LOCKED)
│       │       └── ...
│       │
│       ├── services/
│       │   ├── email_service.py      # Async SMTP with Jinja2 templates
│       │   ├── otp_service.py        # OTP generation (6-digit, 10-min expiry)
│       │   ├── ticket_service.py     # PDF ticket generation (ReportLab)
│       │   ├── razorpay_service.py   # Razorpay API wrapper
│       │   ├── queue_service.py      # Queue logic (join, process, positions)
│       │   ├── websocket_manager.py  # WebSocket connection manager
│       │   ├── notification_service.py  # Preference-aware notifications
│       │   ├── msg91_service.py      # SMS OTP provider
│       │   └── admin_log_service.py  # Admin audit logging
│       │
│       ├── securities/
│       │   ├── hashing/
│       │   │   ├── hash.py           # Bcrypt (layer 1) + Argon2 (layer 2)
│       │   │   └── password.py       # Password generator wrapper
│       │   ├── authorizations/
│       │   │   └── jwt.py            # JWT token generation & validation
│       │   └── verifications/
│       │       └── credentials.py    # Username/email availability checks
│       │
│       ├── seeders/
│       │   └── seed_admin.py         # Creates admin user on first startup
│       │
│       ├── workers/
│       │   └── queue_processor.py    # Background worker (processes queues every 5s)
│       │
│       ├── templates/email/          # Jinja2 email templates (HTML)
│       │   ├── base.html, welcome.html, otp_verification.html, ...
│       │
│       └── utilities/                # Exceptions, formatters, messages
│
├── frontend/                         # Next.js app (separate)
│   ├── Dockerfile
│   └── ...
│
└── nginx/                            # Reverse proxy config (production)
    └── nginx.conf
```

---

## 4. Local Setup

### Prerequisites

- **Docker & Docker Compose** (recommended)
- OR: **Python 3.11+**, **PostgreSQL 14+**
- **Git**

---

### Option A: Docker (Recommended)

This is the fastest way. Docker Compose spins up PostgreSQL, Adminer (DB editor), and the backend in one command.

**Step 1: Clone the repository**
```bash
git clone <repo-url> FastAPI-Backend-Template
cd FastAPI-Backend-Template
```

**Step 2: Create your `.env` file**
```bash
cp .env.example .env
```

**Step 3: Edit `.env` with your values**

The critical variables to set:
```env
# Keep these for Docker setup
ENVIRONMENT=DEV
DEBUG=True
POSTGRES_HOST=db                      # "db" is the Docker service name
POSTGRES_DB=zoniq_db
POSTGRES_USERNAME=postgres
POSTGRES_PASSWORD=your-strong-password
POSTGRES_PORT=5432

# Admin account (created on first startup)
ADMIN_EMAIL=admin@yourapp.com
ADMIN_PASSWORD=admin123!
ADMIN_USERNAME=admin

# JWT (change in production)
JWT_SECRET_KEY=your-super-secret-jwt-key
JWT_SUBJECT=zoniq-access
JWT_TOKEN_PREFIX=Bearer
JWT_ALGORITHM=HS256
JWT_MIN=60
JWT_HOUR=24
JWT_DAY=7

# Hashing
HASHING_ALGORITHM_LAYER_1=bcrypt
HASHING_ALGORITHM_LAYER_2=argon2
HASHING_SALT=your-random-salt

# Razorpay (get test keys from https://dashboard.razorpay.com/app/keys)
RAZORPAY_KEY_ID=rzp_test_xxxx
RAZORPAY_KEY_SECRET=your-razorpay-secret

# SMTP Email (optional - emails will fail silently without this)
SMTP_HOST=smtp.titan.email
SMTP_PORT=587
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-smtp-password
SMTP_USE_TLS=True
FROM_EMAIL=your-email@example.com
FROM_NAME=YourApp

# Frontend
FRONTEND_URL=http://localhost:3000
```

**Step 4: Make the entrypoint executable & start Docker**
```bash
chmod +x backend/entrypoint.sh
docker-compose up --build
```

**Step 5: Verify it's running**

| Service | URL |
|---------|-----|
| Backend API Docs (Swagger) | http://localhost:8001/docs |
| Backend ReDoc | http://localhost:8001/redoc |
| Database Editor (Adminer) | http://localhost:8081 |
| PostgreSQL (direct) | `localhost:5433` |

**What happens on startup:**
1. PostgreSQL starts → data persisted in `postgresql_db_data` volume
2. Backend waits for PostgreSQL to be ready (netcat check)
3. Alembic runs `upgrade head` → creates all database tables
4. Admin user is seeded (from `.env` credentials)
5. Uvicorn starts with hot-reload enabled
6. Queue processor background worker starts

**Adminer login (DB Editor):**
- System: PostgreSQL
- Server: `db`
- Username: from your `.env` `POSTGRES_USERNAME`
- Password: from your `.env` `POSTGRES_PASSWORD`
- Database: from your `.env` `POSTGRES_DB`

---

### Option B: Manual Setup (Without Docker)

**Step 1: Install PostgreSQL**

Make sure PostgreSQL is installed and running locally.

```bash
# macOS (Homebrew)
brew install postgresql@15
brew services start postgresql@15

# Create the database
createdb zoniq_db
```

**Step 2: Clone & set up Python environment**
```bash
git clone <repo-url> FastAPI-Backend-Template
cd FastAPI-Backend-Template

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate    # macOS/Linux
# or: venv\Scripts\activate  # Windows

# Install dependencies
cd backend
pip install -r requirements.txt
```

**Step 3: Create `.env` in the project root**
```bash
cp .env.example .env
```

Edit `.env` - the key difference from Docker:
```env
POSTGRES_HOST=localhost               # "localhost" instead of "db"
POSTGRES_PORT=5432                    # 5432 directly (not 5433)
POSTGRES_USERNAME=your-local-pg-user  # your local PostgreSQL user
```

**Step 4: Run database migrations**
```bash
cd backend
alembic upgrade head
```

**Step 5: Seed the admin user**
```bash
python -m src.seeders.seed_admin
```

**Step 6: Start the server**
```bash
uvicorn src.main:backend_app --reload --host 127.0.0.1 --port 8000
```

**Step 7: Verify**
- API Docs: http://localhost:8000/docs

---

## 5. Configuration Deep Dive

### Environment-Based Settings

The app uses a **settings factory** pattern (`backend/src/config/manager.py`):

```
ENVIRONMENT=DEV  → BackendDevSettings  (DEBUG=True)
ENVIRONMENT=STAGE → BackendStageSettings (DEBUG=True)
ENVIRONMENT=PROD  → BackendProdSettings (DEBUG=False)
```

All settings inherit from `BackendBaseSettings` (`backend/src/config/settings/base.py`) which reads from `.env`.

### Key Configuration Values

| Setting | Default | Description |
|---------|---------|-------------|
| `API_PREFIX` | `/api` | All routes are prefixed with this |
| `DOCS_URL` | `/docs` | Swagger UI path |
| `JWT_MIN` / `JWT_HOUR` / `JWT_DAY` | 60 / 24 / 7 | Token expiry calculation |
| `DB_POOL_SIZE` | 10 | PostgreSQL connection pool |
| `ALLOWED_ORIGINS` | `localhost:3000`, `localhost:5173` | CORS origins |

### App Startup Flow

```
main.py
  └── initialize_backend_application()
        ├── Create FastAPI app with settings
        ├── Add CORS middleware
        ├── Register startup event handler
        │     ├── Initialize DB connection
        │     ├── Create tables (if needed)
        │     ├── Seed admin user
        │     └── Start queue processor (background worker)
        ├── Register shutdown event handler
        │     ├── Stop queue processor
        │     └── Dispose DB connection
        └── Include API router (prefix=/api)
              └── endpoints.py aggregates all route files
```

---

## 6. Database Schema & Models

### Entity Relationship Overview

```
Account (User)
  ├── has many → Booking → has many → BookingItem (ticket)
  ├── has many → Cart → has many → CartItem
  ├── has many → Payment
  ├── has many → QueueEntry
  ├── has many → Wishlist
  ├── has many → TicketTransfer (from_user)
  ├── has one  → NotificationPreference
  └── has many → OTPCode

Event
  ├── belongs to → Venue
  ├── has many → SeatCategory → has many → Seat
  ├── has many → Booking
  ├── has many → Cart
  └── has many → QueueEntry

Venue
  └── has many → Event
```

### Key Models

**Account** (`account` table)
- Two-layer password hashing: Bcrypt (salt) → Argon2 (password+salt)
- Roles: `user` (default), `admin`
- Flags: `is_verified`, `is_active`, `is_blocked`, `is_phone_verified`

**Event** (`event` table)
- Status lifecycle: `draft` → `published` → `completed` / `cancelled` / `soldout`
- PostgreSQL full-text search via `search_vector` column (TSVECTOR)
- Queue configuration: `queue_enabled`, `queue_batch_size`, `queue_processing_minutes`
- Property `is_booking_open`: checks status + booking dates + available seats

**Seat** (`seat` table)
- Status: `available` → `locked` (7 min) → `booked`
- Lock fields: `locked_until`, `locked_by` (user ID)
- Supports assigned seating (specific seat) and general admission (quantity-based)

**Cart** (`cart` + `cart_item` tables)
- Auto-expires after 15 minutes
- Status: `active` → `converted` (on checkout) / `abandoned` / `expired`
- CartItem stores `seat_ids` (JSON array) for assigned seating

**Booking** (`booking` + `booking_item` tables)
- Generated booking number: `ZNQ-20260219-A1B2C3`
- Each BookingItem gets a unique ticket number: `TKT-A1B2C3D4`
- Status: `pending` → `confirmed` (after payment) / `cancelled`

**Payment** (`payment` table)
- Tracks Razorpay order ID, payment ID, signature
- Amount stored in **paise** (1 INR = 100 paise)
- Status: `created` → `captured` / `failed` / `refunded`

---

## 7. Feature Walkthrough

### 7.1 Authentication & Users

**File:** `backend/src/api/routes/authentication.py`

**Two authentication methods:**

1. **Password-based signup/signin:**
   - `POST /api/auth/signup` - Register with username, email, password + email OTP
   - `POST /api/auth/signin` - Login with username + email + password

2. **Email OTP (passwordless):**
   - `POST /api/auth/email-otp/send` - Send 6-digit OTP to email
   - `POST /api/auth/email-otp/verify` - Verify OTP → auto-login or auto-register

**How it works:**
- On signup, the email OTP must be verified first (anti-spam)
- JWT tokens are issued on successful auth
- Token contains: `username`, `email`, `role`
- The `get_current_user` dependency extracts the user from the Bearer token on every request
- Blocked users get a 403 response

**User profile** (`backend/src/api/routes/users.py`):
- View/update profile
- Phone verification via OTP (MSG91 integration)
- Email verification via OTP

---

### 7.2 Events & Venues

**File:** `backend/src/api/routes/events.py` (public) + `admin/events.py` (admin)

**Public endpoints:**
- List events with filters (category, city, date range, price range)
- Full-text search with PostgreSQL TSVECTOR (title weighted highest)
- Get event details including seat categories
- Get seat availability map

**Admin event lifecycle:**
```
Admin creates event (status: draft)
    │
    ▼
Admin adds venue, seat categories, seats
    │
    ▼
Admin publishes event (status: published)
    │
    ▼
Users can book (between booking_start_date and booking_end_date)
    │
    ▼
Event completes / gets cancelled / sells out
```

**Event categories:** concert, sports, theater, comedy, conference, workshop, festival, exhibition, other

**Venues** (`admin/venues.py`):
- CRUD for venues with address, capacity, contact info
- JSON `seat_map_config` for flexible seating layouts
- Each venue can host multiple events

---

### 7.3 Seat Management

**File:** `backend/src/api/routes/admin/seats.py`

**Two seating modes:**

1. **Assigned seating** - Specific seats with row/section/number (e.g., "A-1", "B-12")
   - Users select specific seats on a map
   - Seats have `position_x`, `position_y` for rendering

2. **General admission** - Quantity-based, no specific seat assignment
   - Users just pick a quantity from a category
   - Tracked via `available_seats` counter on SeatCategory

**Seat lifecycle:**
```
AVAILABLE → LOCKED (user adds to cart, 7-minute hold)
    │           │
    │           ├── Lock expires → AVAILABLE (auto-released)
    │           │
    │           └── Checkout succeeds → BOOKED
    │
    └── Admin blocks → BLOCKED (maintenance, etc.)
```

**Admin seat operations:**
- Create individual seats or bulk create (e.g., "Create rows A-Z with 20 seats each")
- Block/unblock seats
- Release expired locks
- View seat counts by status

---

### 7.4 Cart System

**File:** `backend/src/api/routes/cart.py`

The cart is a **temporary holding area** with automatic expiry and seat locking.

**How it works:**
1. User creates a cart for a specific event → 15-minute timer starts
2. Adding items locks seats for 7 minutes (prevents double-booking)
3. Cart validates on checkout: checks event is still bookable, seats still available
4. Checkout converts cart → booking and marks cart as `converted`

**Key behaviors:**
- One active cart per user per event
- Cart auto-expires after 15 minutes (seats released back)
- Seat locks auto-expire after 7 minutes
- Adding items extends the cart expiry
- Abandoning/clearing a cart releases all locked seats
- Category already in cart? Must update quantity, not add again

**Endpoints:**
| Method | Path | What it does |
|--------|------|-------------|
| `POST` | `/api/cart` | Create or get existing cart for an event |
| `POST` | `/api/cart/items` | Add a seat category to cart |
| `PATCH` | `/api/cart/items/{id}` | Update quantity (general admission only) |
| `DELETE` | `/api/cart/items/{id}` | Remove item, release locked seats |
| `GET` | `/api/cart/validate` | Pre-checkout validation |
| `POST` | `/api/cart/checkout` | Convert cart → booking |
| `GET` | `/api/cart/current` | Get active cart (if any) |
| `DELETE` | `/api/cart/clear` | Abandon cart, release all seats |
| `GET` | `/api/cart/count` | Get item count in active cart |

---

### 7.5 Booking Flow

**File:** `backend/src/api/routes/bookings.py`

Bookings are created from cart checkout. Each booking:
- Gets a unique booking number (`ZNQ-YYYYMMDD-XXXXXX`)
- Has one BookingItem per ticket (each with unique ticket number `TKT-XXXXXXXX`)
- Snapshots pricing at booking time (price won't change if admin updates later)
- Starts with `payment_status: pending`

**Booking statuses:**
| Status | Meaning |
|--------|---------|
| `pending` | Created, awaiting payment |
| `confirmed` | Payment successful |
| `cancelled` | Cancelled by user or admin |
| `refunded` | Payment refunded |

---

### 7.6 Payment Integration (Razorpay)

**File:** `backend/src/api/routes/payments.py` + `backend/src/services/razorpay_service.py`

**Payment flow:**

```
1. Frontend calls POST /api/payments/create-order { bookingId }
   └── Backend creates Razorpay order → returns orderId, keyId, amount

2. Frontend opens Razorpay checkout widget with orderId + keyId
   └── User completes payment on Razorpay's UI

3. Frontend calls POST /api/payments/verify
   {
     razorpayOrderId,
     razorpayPaymentId,
     razorpaySignature
   }
   └── Backend verifies signature
   └── Updates payment record → updates booking status → sends confirmation email

4. (Async) Razorpay sends POST /api/payments/webhook
   └── Backup verification for payment.captured / payment.failed events
   └── Releases seats on payment failure
```

**Amount handling:** All amounts are stored in **paise** (1 INR = 100 paise). So ₹500 = 50000 paise.

**Webhook events handled:**
- `payment.captured` - Payment successful
- `payment.failed` - Payment failed → seats released
- `refund.created` / `refund.processed` - Refund tracking

**To test payments:** Get test API keys from https://dashboard.razorpay.com/app/keys

---

### 7.7 Ticket System

**File:** `backend/src/api/routes/tickets.py` + `backend/src/services/ticket_service.py`

**After payment, each BookingItem becomes a ticket:**
- Unique ticket number: `TKT-A1B2C3D4`
- Can be downloaded as a PDF (ReportLab-generated)
- Can be transferred to another user via email

**Ticket transfer flow:**
```
1. Owner calls POST /api/tickets/{id}/transfer { toEmail, message }
   └── Creates transfer record with unique token + 24h expiry

2. Recipient receives email with claim link

3. Recipient calls POST /api/tickets/claim { transferToken }
   └── Ticket ownership transfers to new user

4. Owner can cancel: POST /api/tickets/transfers/{id}/cancel
```

**Mark as used** (event entry):
- Admin calls `POST /api/tickets/mark-used { ticketNumber }`
- For QR code scanning at venue gates

---

### 7.8 Virtual Queue System

**File:** `backend/src/api/routes/queue.py` + `backend/src/services/queue_service.py` + `backend/src/workers/queue_processor.py`

For high-demand events, the queue system prevents server overload by batching users.

**How it works:**

```
1. Admin enables queue on event (queue_enabled=true, batch_size=50, processing_minutes=10)

2. User joins queue → gets position number
   └── Status: WAITING

3. Background worker runs every 5 seconds:
   ├── Moves next batch (e.g., 50 users) from WAITING → PROCESSING
   ├── Expires stale PROCESSING entries (exceeded their window)
   └── Sends WebSocket updates to all connected users

4. When user's status = PROCESSING:
   └── They have X minutes to complete checkout

5. After checkout: status → COMPLETED
   Or timeout: status → EXPIRED (slot opens for next user)
```

**WebSocket real-time updates:**
- Connect: `ws://localhost:8001/api/ws/queue/{event_id}?token=<jwt>`
- Receives position updates, status changes, and heartbeat messages
- Thread-safe connection manager handles per-event user connections

**Concurrency safety:**
- Queue uses `FOR UPDATE SKIP LOCKED` for batch processing (no double-processing)
- Position calculation is atomic

---

### 7.9 Notifications & Email

**File:** `backend/src/services/email_service.py` + `backend/src/api/routes/notifications.py`

**Email types sent:**
| Email | When |
|-------|------|
| Welcome | New user registers |
| OTP Verification | Login/signup OTP |
| Booking Confirmation | After checkout |
| Payment Confirmation | After successful payment |

**Email templates:** Jinja2 HTML templates in `backend/src/templates/email/`

**Notification preferences:** Users can toggle each email type:
- Booking confirmations
- Payment updates
- Ticket delivery
- Event reminders
- Event updates
- Transfer notifications
- Marketing emails (default: off)

The `notification_service.py` checks preferences before sending.

**SMTP configuration:** Uses aiosmtplib for async email delivery. Configure your SMTP provider in `.env` (Titan, Gmail, SendGrid, etc.).

---

### 7.10 Wishlist

**File:** `backend/src/api/routes/wishlist.py`

Simple event bookmarking:
- `POST /api/users/me/wishlist/{event_id}` - Add to wishlist
- `DELETE /api/users/me/wishlist/{event_id}` - Remove
- `GET /api/users/me/wishlist` - List all wishlisted events
- `GET /api/users/me/wishlist/{event_id}/check` - Check if wishlisted

Unique constraint per user+event prevents duplicates.

---

### 7.11 Admin Panel

**File:** `backend/src/api/routes/admin/`

All admin routes require the `require_admin` dependency (checks `role == "admin"`).

**Admin capabilities:**

| Area | What admins can do |
|------|--------------------|
| **Users** | List users (paginated), view stats, block/unblock users |
| **Events** | Full CRUD, publish/cancel/reactivate, manage seat categories |
| **Venues** | Full CRUD, capacity management |
| **Seats** | Create (single/bulk), block/unblock, release expired locks |
| **Bookings** | View all bookings, stats, sales analytics, top events, attendee lists |
| **Logs** | View admin activity audit trail (all admin actions are logged) |
| **Dashboard** | Overview stats, revenue chart, recent bookings, upcoming events |

**Admin activity logging:** Every admin action is recorded in `admin_activity_log` with:
- Who did it (admin ID)
- What they did (action enum)
- Which entity was affected
- IP address
- Timestamp

---

## 8. End-to-End Booking Flow

Here's the complete flow a user goes through to book a ticket, with exact API calls:

```
STEP 1: AUTHENTICATION
──────────────────────
POST /api/auth/email-otp/send
  → { "email": "user@example.com" }

POST /api/auth/email-otp/verify
  → { "email": "user@example.com", "code": "123456" }
  ← { "id": 1, "authorizedAccount": { "token": "eyJ..." } }

Save the token. Use it as: Authorization: Bearer eyJ...


STEP 2: BROWSE EVENTS
──────────────────────
GET /api/events?category=music&city=Mumbai
  ← List of published events

GET /api/events/42
  ← Full event details with venue, dates, seat info


STEP 3: VIEW SEATS
──────────────────
GET /api/events/42/categories
  ← Seat categories with prices (VIP: ₹5000, General: ₹1000)

GET /api/events/42/seats
  ← Seat map with availability status


STEP 4: ADD TO CART
───────────────────
POST /api/cart/items
  → { "eventId": 42, "seatCategoryId": 1, "quantity": 2, "seatIds": [101, 102] }
  ← Cart response with items, total, expiry timer

Seats 101 & 102 are now LOCKED for 7 minutes.
Cart expires in 15 minutes.


STEP 5: VALIDATE & CHECKOUT
────────────────────────────
GET /api/cart/validate
  ← { "isValid": true, "errors": [], "warnings": [] }

POST /api/cart/checkout
  → { "contactEmail": "user@example.com" }
  ← Booking created (status: pending, paymentStatus: pending)
     Booking number: ZNQ-20260219-A1B2C3
     2 tickets generated: TKT-XXXX, TKT-YYYY


STEP 6: PAY
────────────
POST /api/payments/create-order
  → { "bookingId": 1 }
  ← { "orderId": "order_xxx", "amount": 1000000, "keyId": "rzp_test_xxx" }

[Frontend opens Razorpay checkout widget]
[User pays via UPI/Card/NetBanking]

POST /api/payments/verify
  → { "razorpayOrderId": "order_xxx", "razorpayPaymentId": "pay_xxx", "razorpaySignature": "sig_xxx" }
  ← { "success": true, "bookingNumber": "ZNQ-20260219-A1B2C3" }

Booking status → confirmed. Payment confirmation email sent.


STEP 7: VIEW TICKETS
─────────────────────
GET /api/tickets/booking/1
  ← List of ticket objects

GET /api/tickets/5/download
  ← PDF ticket file download
```

---

## 9. Code Patterns & Conventions

### Repository Pattern
Every database operation goes through a CRUD repository class:
```
Route Handler → depends on → CRUDRepository → uses → AsyncSession → PostgreSQL
```

All repos inherit from `BaseCRUDRepository` which holds the async session.

### Dependency Injection
FastAPI's `Depends()` is used everywhere:
```python
@router.get("/bookings")
async def list_bookings(
    current_user: Account = Depends(get_current_user),          # Auth
    booking_repo: BookingCRUDRepository = Depends(get_repository(repo_type=BookingCRUDRepository)),  # DB
):
```

### Schema Conventions
- All Pydantic schemas inherit `BaseSchemaModel` from `models/schemas/base.py`
- **camelCase conversion** is automatic: `booking_number` in Python → `bookingNumber` in JSON
- `from_attributes=True` allows direct SQLAlchemy model → Pydantic conversion

### Error Handling
- Custom exceptions: `EntityDoesNotExist`, `EntityAlreadyExists`, `PasswordDoesNotMatch`
- HTTP exceptions raised directly in route handlers
- Standard error format: `{ "detail": "Error message" }`

### Async Everything
- All database queries use `await` with AsyncPG
- Email sending is async (aiosmtplib)
- HTTP calls are async (httpx)
- Background workers use `asyncio.create_task`

---

## 10. Testing

Tests are in `backend/tests/` organized by type:

```
tests/
├── conftest.py              # Test fixtures, async client setup
├── unit_tests/              # Individual function tests
├── integration_tests/       # API endpoint tests
├── end_to_end_tests/        # Full flow tests
└── security_tests/          # Auth & permission tests
```

**Run tests:**
```bash
# Local
cd backend
pytest

# Docker
docker exec backend_app pytest

# With coverage
pytest --cov=src --cov-report=html
```

**Configuration:** In `backend/pyproject.toml` - targets 63% minimum coverage.

---

## 11. Deployment

### Production (Docker)

```bash
# 1. Set up .env with production values
#    - Strong passwords
#    - ENVIRONMENT=PROD, DEBUG=False
#    - Real Razorpay keys
#    - Real SMTP credentials

# 2. Deploy
chmod +x deploy.sh
./deploy.sh

# Or manually:
docker compose -f docker-compose.prod.yaml up -d --build
```

Production adds:
- Nginx reverse proxy
- Frontend container
- Health checks on all services
- Auto-restart policies
- No host port mapping (Nginx handles routing)

### SSL/HTTPS
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

See `DEPLOYMENT.md` for the full AWS EC2 deployment guide.

---

## 12. Where to Continue

Here are the areas you can build on:

### Ready to Use (Fully Implemented)
- Authentication (password + email OTP)
- Event CRUD with full-text search
- Venue management
- Seat categories and individual seat management
- Cart system with seat locking and expiry
- Checkout → Booking creation
- Razorpay payment integration (create order, verify, webhook)
- PDF ticket generation and download
- Ticket transfers
- Virtual queue with WebSocket
- Admin dashboard with analytics
- Email notifications with preferences
- Wishlist

### Areas to Extend
- **Frontend:** The Next.js frontend exists but needs to be connected to all backend APIs
- **SMS OTP:** MSG91 integration is scaffolded but uses mock in dev mode
- **Refund flow:** Schema exists (`RefundRequest`/`RefundResponse`) but no route endpoint yet
- **Promo codes:** Fields exist on booking model but feature was removed (can be re-added)
- **Event reminders:** Notification preference exists but no scheduled job sends reminders
- **Search improvements:** Full-text search works but could add filters for upcoming/trending
- **Seat map rendering:** Backend serves seat coordinates (`position_x`, `position_y`) - frontend needs to render the interactive map
- **Analytics expansion:** Basic stats exist - can add date range filtering, export to CSV
- **Rate limiting:** Not implemented yet - consider adding for auth endpoints
- **Caching:** No Redis cache layer - could add for event listings, seat counts
- **File uploads:** Event images use URL fields - could add S3/Cloudinary upload

### Database Migrations
When you modify models, generate a new migration:
```bash
# Docker
docker exec backend_app alembic revision --autogenerate -m "describe your change"
docker exec backend_app alembic upgrade head

# Local
cd backend
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

---

*For API endpoint details, payloads, and responses, see [API_DOCUMENTATION.md](./API_DOCUMENTATION.md).*
