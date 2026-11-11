# TICKET-02: GET /api/providers — List Featured Providers

## 1. Title
GET /api/providers — Retrieve List of Service Providers [AI-Ready Bar]

## 2. Context
Allows anonymous learners on the homepage to view active service providers, their skill categories, average ratings, and starting hourly prices.

## 3. Scope
Implement a single HTTP GET endpoint at `/api/providers` returning a JSON list of providers with attached primary service metadata.

## 4. Interface Contract
- **Request**: `GET /api/providers`
  - Query params: `category` (optional string), `limit` (optional int, default 10, max 100).
- **Success Response (200 OK)**:
  ```json
  {
    "providers": [
      {
        "provider_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
        "name": "Alice Chen",
        "category": "Web Development",
        "rating": 4.9,
        "hourly_rate": 5000,
        "currency": "USD"
      }
    ]
  }
  ```
- **Error Response (400 Bad Request)**:
  ```json
  {
    "error": "Invalid query parameter 'limit'. Must be an integer <= 100."
  }
  ```

## 5. Acceptance Criteria
- **Given** seeded provider data in database,
- **When** a client sends `GET /api/providers`,
- **Then** the server responds with status code `200 OK` and a JSON array containing provider cards.
- **Given** a client specifies `GET /api/providers?category=Web%20Development`,
- **When** the query is processed,
- **Then** only providers matching the specified category are returned.

## 6. Constraints
- Must be non-blocking and return in <100ms.
- Must use standard Express router pattern under `src/routes/provider.routes.ts`.

## 7. Anti-Scope
- No authentication token required (Public Endpoint).
- No pagination cursor implementation (simple limit filter for Slice 1).
- No full-text fuzzy search engine integration.
