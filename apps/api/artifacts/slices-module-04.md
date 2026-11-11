# SkillSwap - Vertical Slice Definitions (Module 04)

## Slice 1: Browse & Book Core Flow (Ultra-Thin Seeded Demand)
- **Scope**: Learner views 3 hardcoded providers, views 1 service profile, selects 1 time slot, submits booking, receives on-screen booking confirmation with reference ID. Booking record persists in SQLite/Postgres DB.
- **Anti-Scope**: No user authentication/registration (anonymous learner session), no payment processing or Stripe integration (booking is free), no email/webhook notifications, no category search/filtering, no provider-side UI or registration, no booking cancellation/modification, no review submissions, no multi-city geo sorting.
- **Dependencies**: None (First Slice).
- **Acceptance Criteria**:
  1. Open app homepage — see 3 provider cards (Name, Category, Rating).
  2. Click a provider card — navigate to profile showing 1 service description and 3 open time slots.
  3. Select a time slot and click "Confirm Booking".
  4. See confirmation screen displaying Booking Reference ID, Provider Name, Service Title, and Scheduled Time.
  5. Refresh browser — booking record remains persisted in database.
- **Estimated Complexity**: S (2 hours).

---

## Slice 1.5: Payment Proof-of-Concept Spike (Investor Demo Requirement)
- **Rationale**: Inserted in response to PM/Investor request to demonstrate payment flow by Friday without coupling payment risk directly into Slice 1 core booking UX.
- **Scope**: Standalone demo page (`/demo/payment-spike`) rendering a test Stripe Elements card checkout form, processing a dummy \$50 transaction using Stripe test credentials, and displaying a successful transaction receipt with Stripe charge ID.
- **Anti-Scope**: No integration into main booking workflow (isolated demo endpoint), no escrow hold calculations, no payout ledgering, no user account association.
- **Dependencies**: None (Runs parallel to Slice 1).
- **Estimated Complexity**: S (3 hours).

---

## Slice 2: Learner & Provider Authentication (Identity Slice)
- **Scope**: User registration and JWT authentication endpoints for Learners and Providers, RBAC token generation, protected booking routes, session login/logout UI.
- **Anti-Scope**: No password reset email flow, no OAuth/Google login, no multi-factor auth (MFA), no provider document upload during sign-up.
- **Dependencies**: Slice 1.
- **Acceptance Criteria**:
  1. Register a new user account with email/password and role (`Learner` or `Provider`).
  2. Log in with registered credentials — receive JWT access token.
  3. Attempt booking without token — receive 401 Unauthorized.
  4. Submit booking with valid Learner token — booking persists tied to `learner_id`.
- **Estimated Complexity**: S (3 hours).

---

## Slice 3: Provider Portal & Availability Management (Supply-Side Slice)
- **Scope**: Authenticated Provider dashboard allowing providers to create service listings, set custom pricing, configure weekly availability slots, and view incoming bookings.
- **Anti-Scope**: No admin document verification gating (providers can publish immediately in test mode), no Stripe payout account linking, no automated calendar sync (Google/Outlook calendar).
- **Dependencies**: Slice 2.
- **Acceptance Criteria**:
  1. Provider logs in and accesses Provider Portal (`/dashboard`).
  2. Provider creates a new service listing (Title, Description, Price per hour).
  3. Provider adds available time slots for the upcoming week.
  4. Learner views provider profile — newly added service and custom time slots appear live.
- **Estimated Complexity**: M (1 day).

---

## Slice 4: Instant Search & Multi-City Filtering (Scale & Discovery Slice)
- **Scope**: Search endpoint with category filter, city filter (5 target cities), query string search, indexed database query returning results under 200ms latency.
- **Anti-Scope**: No Elasticsearch/Meilisearch external cluster (uses PostgreSQL trigram/full-text indexing), no map view pin rendering, no auto-complete search suggestions.
- **Dependencies**: Slice 3.
- **Acceptance Criteria**:
  1. Type category "Web Development" and select city "Austin" in search bar.
  2. Submit search query — results return in under 200ms.
  3. Only Austin web development providers are displayed in search results list.
- **Estimated Complexity**: M (1.5 days).

---

## Slice 5: Payment Processing & Escrow Integration (Integration Slice)
- **Scope**: Integration with `IPaymentGateway` (Stripe / Mock Provider), pre-authorizing booking funds, deducting 15% platform fee, holding escrow funds until session completion.
- **Anti-Scope**: No automated payout payouts to provider bank accounts (manual admin trigger), no multi-currency support (USD only), no split payments.
- **Dependencies**: Slice 3, Slice 1.5.
- **Acceptance Criteria**:
  1. Learner selects booking time slot — prompted for card details.
  2. Submit payment — gateway authorizes funds, booking status transitions to `confirmed`.
  3. Verify payment ledger record — 85% allocated to provider balance, 15% allocated to platform fee ledger.
- **Estimated Complexity**: M (2 days).
