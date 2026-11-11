# TICKET-03: GET /api/providers/:id/slots — List Available Time Slots

## 1. Title
GET /api/providers/:id/slots — Retrieve Open Schedule Time Slots [AI-Ready Bar]

## 2. Context
When a learner views a provider's detailed profile, they need to inspect open calendar time slots to choose an appointment.

## 3. Scope
Implement HTTP GET endpoint `/api/providers/:id/slots` returning all unbooked time slots associated with a provider.

## 4. Interface Contract
- **Request**: `GET /api/providers/:id/slots`
- **Success Response (200 OK)**:
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
- **Error Response (404 Not Found)**:
  ```json
  {
    "error": "Provider not found"
  }
  ```

## 5. Acceptance Criteria
- **Given** a valid provider UUID with open time slots,
- **When** `GET /api/providers/:id/slots` is called,
- **Then** status code `200 OK` is returned with only slots where `status == "open"`.
- **Given** a non-existent provider UUID,
- **When** `GET /api/providers/invalid-id/slots` is called,
- **Then** status code `404 Not Found` is returned.

## 6. Constraints
- Must filter out slots where `status == "booked"`.
- Timestamps must adhere to ISO 8601 UTC format.

## 7. Anti-Scope
- No slot creation or modification logic.
- No timezone conversion on server side (returns UTC).
