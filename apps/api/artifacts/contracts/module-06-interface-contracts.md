# Module 06: Interface Contracts Specification

## Contract 1: Booking Service (Stream 2) <-> Availability Service (Stream 1)

### Shared Identifiers & Types
- `provider_id`: String (UUIDv4)
- `slot_id`: String (UUIDv4)
- `user_id`: String (UUIDv4)
- `datetime`: String ISO 8601 UTC (e.g. `"2026-09-01T10:00:00Z"`)

### Availability API (Exposed by Stream 1)
- **Endpoint**: `GET /api/providers/:id/slots`
- **Response 200 OK**:
  ```json
  {
    "provider_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "slots": [
      {
        "slot_id": "c7a8b9c0-1d2e-3f4a-5b6c-7d8e9f0a1b2c",
        "start_time": "2026-09-01T10:00:00Z",
        "end_time": "2026-09-01T11:00:00Z",
        "status": "open"
      }
    ]
  }
  ```

### Booking API (Exposed by Stream 2)
- **Endpoint**: `POST /api/bookings`
- **Request Body**:
  ```json
  {
    "provider_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "slot_id": "c7a8b9c0-1d2e-3f4a-5b6c-7d8e9f0a1b2c",
    "learner_email": "john@example.com",
    "notes": "Intro session"
  }
  ```
- **Response 201 Created**:
  ```json
  {
    "booking_id": "f1e2d3c4-b5a6-7f8e-9d0c-1b2a3f4e5d6c",
    "status": "confirmed",
    "provider_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "slot_id": "c7a8b9c0-1d2e-3f4a-5b6c-7d8e9f0a1b2c",
    "created_at": "2026-08-26T10:20:00Z"
  }
  ```

---
*Created for SkillSwap Execution Planning — Module 06.*
