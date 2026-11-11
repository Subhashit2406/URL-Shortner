# TICKET-04: POST /api/bookings — Create Booking and Reserve Time Slot

## 1. Title
POST /api/bookings — Submit Instant Booking & Mark Slot Reserved [AI-Ready Bar]

## 2. Context
This is the core transaction in SkillSwap Slice 1. Learner chooses a provider slot and submits booking details.

## 3. Scope
Implement POST `/api/bookings` endpoint, validating slot availability, creating booking database record, and updating slot status to `booked`.

## 4. Interface Contract
- **Request Headers**:
  - `Content-Type: application/json`
  - `Idempotency-Key` (optional UUIDv4 header to prevent duplicate network submissions)
- **Request Body**:
  ```json
  {
    "provider_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "slot_id": "c7a8b9c0-1d2e-3f4a-5b6c-7d8e9f0a1b2c",
    "learner_name": "John Doe",
    "learner_email": "john@example.com",
    "notes": "Looking forward to learning CSS grid!"
  }
  ```
- **Success Response (201 Created)**:
  ```json
  {
    "booking_id": "f1e2d3c4-b5a6-7f8e-9d0c-1b2a3f4e5d6c",
    "status": "confirmed",
    "provider_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "slot_id": "c7a8b9c0-1d2e-3f4a-5b6c-7d8e9f0a1b2c",
    "learner_email": "john@example.com",
    "created_at": "2026-08-25T17:40:00Z"
  }
  ```
- **Error Responses**:
  - `400 Bad Request`: `{ "error": "slot_id and provider_id are required" }`
  - `404 Not Found`: `{ "error": "Selected time slot does not exist" }`
  - `409 Conflict`: `{ "error": "Selected time slot is already booked" }`
  - `500 Internal Server Error`: `{ "error": "Internal server error" }` (sanitized without raw stack traces)

## 5. Acceptance Criteria
- **Given** an open time slot,
- **When** POST `/api/bookings` is submitted with valid body,
- **Then** status `201 Created` is returned, a booking row is created, and the slot's status changes to `"booked"`.
- **Given** an already booked time slot,
- **When** POST `/api/bookings` is submitted for the same slot,
- **Then** status `409 Conflict` is returned and no duplicate booking row is created.
- **Given** an existing `Idempotency-Key` header on retry,
- **When** POST `/api/bookings` is re-sent,
- **Then** the original `201 Created` response is returned without creating a second booking.

## 6. Constraints
- Slot status update and booking insertion must occur inside a single atomic database transaction.
- Input fields `notes` and `learner_name` must be sanitized against HTML/XSS injection.
- Endpoint logging must emit structured JSON logs (`logger.info("booking_created", { booking_id, slot_id })`).
- Unexpected internal server exceptions must return sanitized `500` JSON without stack traces.

## 7. Anti-Scope
- No payment processing or credit card collection.
- No user authentication required for Slice 1 (explicitly deferred to Slice 2).
- No email notification dispatch.
