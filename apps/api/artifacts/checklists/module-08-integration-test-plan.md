# Module 08: Integration Test Plan

## Test 1: Cross-Component Delegated Booking Propagation
- **Components Involved**: User Auth Service, Provider Directory, Booking Transaction Service.
- **Pre-conditions / Setup**: Pre-seeded manager account (`manager@meridian.com`), provider slot `c7a8b9c0-1d2e-3f4a-5b6c-7d8e9f0a1b2c` set to `open`.
- **Execution Steps**:
  1. Authenticate manager to obtain JWT containing `role="manager"`.
  2. Query `GET /api/providers/:id/slots` to retrieve open slot.
  3. Send `POST /api/bookings` with `slot_id`, `booked_for_name="Sarah Miller"`, `booked_for_email="sarah@meridian.com"`.
- **Expected Result**: `201 Created` with valid `booking_id`; slot status transitions to `booked` on Provider Directory.
- **Contract Points Validated**: JWT auth header format, UUIDv4 field types, ISO UTC date formats.

---

## Test 2: RBAC Authorization Boundary Enforcement
- **Components Involved**: Auth Service, RBAC Authorization Middleware, Booking Service.
- **Pre-conditions / Setup**: Authenticated employee user (`employee@meridian.com`, `role="employee"`).
- **Execution Steps**:
  1. Send `POST /api/bookings` with `booked_for_name="Other User"` from `employee` account.
- **Expected Result**: `403 Forbidden` with error code `INSUFFICIENT_DELEGATION_PERMISSIONS`. Delegated booking disallowed for non-manager role.
- **Contract Points Validated**: RBAC role claim extraction from JWT and access control mapping.

---

## Test 3: Concurrent Slot Reservation Lock Test
- **Components Involved**: Booking Transaction Service, Database Locking Subsystem.
- **Pre-conditions / Setup**: Single open slot `c7a8b9c0-1d2e-3f4a-5b6c-7d8e9f0a1b2c`.
- **Execution Steps**:
  1. Dispatch two concurrent HTTP POST requests to `POST /api/bookings` for the identical slot.
- **Expected Result**: Exactly 1 request succeeds (`201 Created`), second request fails with `409 Conflict`. DB state remains consistent with 1 booking record.
- **Contract Points Validated**: Database transaction boundary and concurrency error payload.
