# TICKET-01: Seed Database with Test Provider & Service Data

## 1. Title
Seed Database with 3 Test Providers and Initial Service Listings [AI-Ready Bar]

## 2. Context
Slice 1 requires an ultra-thin browse and booking user experience without waiting for a full provider dashboard UI. Seeding deterministic test provider profiles enables instant frontend rendering and manual end-to-end verification.

## 3. Scope
Create a database seeding script (`src/db/seeds/providers.seed.ts` or SQL migration) that populates 3 distinct provider profiles, 3 service listings, and 9 open time slots.

## 4. Interface Contract
- **Database Schema Entities**:
  - `User/Provider`: `id` (UUIDv4), `name` (string), `email` (string), `role` ("provider"), `rating` (float 0.0-5.0).
  - `Service`: `id` (UUIDv4), `provider_id` (UUIDv4), `title` (string), `hourly_rate` (integer cents), `category` (string).
  - `Slot`: `id` (UUIDv4), `service_id` (UUIDv4), `start_time` (ISO8601), `end_time` (ISO8601), `status` ("open" | "booked").
- **Seed Data Set**:
  1. Provider 1: "Alice Chen", Category: "Web Development", Rating: 4.9.
  2. Provider 2: "Bob Smith", Category: "UI/UX Design", Rating: 4.8.
  3. Provider 3: "Carol Vance", Category: "Data Science", Rating: 5.0.

## 5. Acceptance Criteria
- **Given** an empty database instance,
- **When** the seeding command `npm run db:seed` is executed,
- **Then** exactly 3 provider records, 3 service records, and 9 open time slots are inserted into the database.
- **Given** existing seeded database data,
- **When** re-running `npm run db:seed`,
- **Then** the script executes idempotently using `ON CONFLICT DO NOTHING` or upserts without throwing primary key duplicate errors.

## 6. Constraints
- Must execute using Knex.js / Prisma ORM / SQL query runner configured in the repository.
- UUIDs must be valid v4 UUID strings.
- All monetary amounts must be stored as integers in cents (e.g., $50/hr -> `5000`).

## 7. Anti-Scope
- No REST endpoint implementation for seeding trigger.
- No user password hashing required for seeded test providers.
- No real Stripe account linking.
