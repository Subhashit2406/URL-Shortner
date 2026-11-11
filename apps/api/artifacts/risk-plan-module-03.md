# SkillSwap - Risk-Annotated Build Plan (Module 03)

## Part 1: Annotated Work Items (Risk Scores & Risk Types)

| Work Item ID | Title | Risk Score (1-5) | Primary Risk Type(s) | Justification |
|---|---|---|---|---|
| **WI-01** | User Auth & Roles | 1 | Dependency | Standard JWT/RBAC pattern (low novelty), but high dependency impact since all modules attach to user identity. |
| **WI-02** | Listings Data Model | 2 | Dependency / Scale | Schema design for provider profiles, categories, and city tags. Moderate scale risk if multi-city queries aren't indexed early. |
| **WI-03** | Provider Onboarding & Vetting | 3 | Novelty | Multi-step approval state machine (`pending_verification` -> `verified`). Moderate novelty in state transitions. |
| **WI-04** | Availability & Schedule Management | 4 | Novelty | Concurrency risk: preventing double-booking race conditions during simultaneous user slot selections. |
| **WI-05** | Instant Search Engine | 3 | Scale | High performance constraint ("feel instant" <200ms latency across 5 cities). Requires spatial/category query optimization. |
| **WI-06** | Booking Flow State Machine | 3 | Dependency | Core transaction state transitions (`pending` -> `confirmed` -> `cancelled`). High dependency for downstream payments. |
| **WI-07** | Payment & Escrow Processing | 5 | Integration / Business Blocker | Highest risk: third-party Stripe integration, webhook handlers, fund holds, 15% platform fee deduction, and refund API calls. |
| **WI-08** | Review & Rating System | 1 | None (Low Risk) | Standard CRUD operations (reviews & ratings). Low uncertainty. |
| **WI-09** | Notification Service | 1 | Integration (Low) | Standard email/webhook alerts. Soft dependency, easily stubbed during early development. |
| **WI-10** | Cancellation & Refund Engine | 4 | Novelty / Integration | Complex business rule hierarchy (24h 100% platform baseline vs provider policy fallback vs no-show override) + Stripe refund API call. |
| **WI-11** | Dispute Escalation System | 2 | Novelty (Low) | Admin manual payout override and evidence upload. Low technical risk. |
| **WI-12** | Admin Dashboard & Analytics | 2 | Scale (Low) | Aggregated platform statistics and provider approval UI. Low technical risk. |

---

## Top 3 Highest Risk Items & Types

1. **WI-07: Payment & Escrow Processing** — Risk Score: **5**, Type: **Integration / Business Blocker** (Stripe API, merchant account dependency).
2. **WI-04: Availability & Schedule Management** — Risk Score: **4**, Type: **Novelty** (Concurrency race condition prevention).
3. **WI-10: Cancellation & Refund Engine** — Risk Score: **4**, Type: **Novelty / Integration** (Multi-tier refund rules & Stripe refund API).

---

## Part 2: Numbered Risk-First Build Plan

1. **WI-01: User Auth & Roles** (Risk: 1, Dependency)
   - *Justification*: Required root dependency for all items. Unblocks user/provider identity creation.
2. **WI-02: Listings Data Model & Multi-City Schema** (Risk: 2, Dependency/Scale)
   - *Justification*: Must establish listing schema with multi-city indexes before testing search or booking flows.
3. **WI-07 (Spike First): Payment & Escrow Spike / Mock Provider** (Risk: 5, Integration)
   - *Justification*: Highest risk item. Executing a 2-hour technical spike on Stripe test API / mock provider interface immediately after Auth/Schema verifies webhook reception, fee splits, and tokenization before building UI.
4. **WI-04: Availability & Schedule Management** (Risk: 4, Novelty)
   - *Justification*: Second highest risk. Implements database slot locks to resolve concurrency race conditions before booking execution.
5. **WI-06: Booking Flow State Machine** (Risk: 3, Dependency)
   - *Justification*: Connects Availability to Payment. Required prerequisite for actual transactions and refund logic.
6. **WI-10: Cancellation & Refund Engine** (Risk: 4, Novelty/Integration)
   - *Justification*: Third highest risk. Retires multi-tier refund rules (24h platform baseline vs provider fallback) immediately after Booking & Payment.
7. **WI-05: Instant Search Engine (<200ms)** (Risk: 3, Scale)
   - *Justification*: Retires performance/latency scale risk for multi-city search once listing data model exists.
8. **WI-03: Provider Onboarding & Vetting** (Risk: 3, Novelty)
   - *Justification*: Implements provider verification workflow and state transitions.
9. **WI-08: Review & Rating System** (Risk: 1, Low Risk)
   - *Justification*: Standard CRUD post-booking feature. Low technical risk.
10. **WI-09: Notification Service** (Risk: 1, Integration)
    - *Justification*: Soft dependency. Wires email/webhook notifications to completed booking/cancellation events.
11. **WI-11: Dispute Escalation System** (Risk: 2, Low Risk)
    - *Justification*: Admin dispute resolution. Soft dependency on booking IDs.
12. **WI-12: Admin Dashboard & Analytics** (Risk: 2, Scale)
    - *Justification*: Endpoint for operational reporting and admin approval UI.

---

## Part 3: Business Blocker Mitigation Strategy (Mock Payment Gateway Interface)

- **External Business Blocker**: Client lacks a registered legal business entity and active Stripe merchant credentials.
- **Architectural Uncoupling Strategy**:
  1. Define a strict typescript interface `IPaymentGateway` with `charge()`, `holdEscrow()`, `releasePayout()`, and `refund()`.
  2. Implement `MockPaymentGateway` that simulates successful/failed card authorizations, webhook callbacks, and 15% platform commission calculations locally in memory/DB ledger.
  3. Proceed with WI-04 (Availability), WI-06 (Booking Flow), and WI-10 (Cancellation Engine) using `MockPaymentGateway`.
  4. Swap `MockPaymentGateway` with live `StripePaymentGateway` seamlessly once legal merchant onboarding completes.
