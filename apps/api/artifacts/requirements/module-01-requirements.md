# SkillSwap - Extracted Requirements Matrix (Module 01 - Resolved)

## Categorized Requirements Matrix

### 1. Learner Requirements
| ID | Requirement | Type | Stakeholder | Source | Confidence |
|---|---|---|---|---|---|
| REQ-L01 | Learners can browse and search providers by category | Functional | Learner | P1 (Explicit) | High |
| REQ-L02 | Search queries must return results under 200ms latency ("feel instant") | Quality Attribute | Learner | P1 (Explicit) | High |
| REQ-L03 | View detailed provider profiles including ratings and reviews | Functional | Learner | P1 (Explicit) | High |
| REQ-L04 | Select and book available time slots with conflict prevention | Functional | Learner | P1 (Explicit) | High |
| REQ-L05 | Execute payment through integrated platform payment gateway | Functional | Learner | P1 (Explicit) | High |
| REQ-L06 | Receive automated booking confirmation emails upon payment | Functional | Learner | P1 (Explicit) | High |
| REQ-L07 | Cancel booked sessions with platform baseline 24h refund rule + provider custom policy hierarchy applied | Functional | Learner | P1 (Updated Clarification) | High |

### 2. Provider Requirements
| ID | Requirement | Type | Stakeholder | Source | Confidence |
|---|---|---|---|---|---|
| REQ-P01 | Set and manage custom availability schedules and time slot lengths | Functional | Provider | P2 (Explicit) | High |
| REQ-P02 | Set custom pricing, service descriptions, and cancellation policy tier | Functional | Provider | P2 (Explicit) | High |
| REQ-P03 | View dashboard showing upcoming bookings, gross earnings, and reviews | Functional | Provider | P2 (Explicit) | High |
| REQ-P04 | Flag no-show users to platform operations | Functional | Provider | P2 (Explicit) | High |
| REQ-P05 | Submit verification documentation during provider onboarding vetting | Functional | Provider | P2 (Explicit) | High |

### 3. Platform & Operations Requirements
| ID | Requirement | Type | Stakeholder | Source | Confidence |
|---|---|---|---|---|---|
| REQ-O01 | Automatically calculate and deduct 15% platform commission on provider earnings | Constraint | Platform | P2 (Explicit) | High |
| REQ-O02 | Admin workflow for reviewing and approving new provider registrations | Functional | Platform | P3 (Explicit) | High |
| REQ-O03 | Dispute resolution system for handling learner-provider booking disputes | Functional | Platform | P3 (Explicit) | High |
| REQ-O04 | System architecture supports scaling to 5 cities within 6 months without rebuild | Quality Attribute / Scalability | Platform | P3 (Explicit) | High |
| REQ-O05 | Operational analytics to track page views, conversion rates, and booking metrics | Quality Attribute / Observability | Platform | P3 (Explicit) | High |
| REQ-O06 | Secure User/Provider Authentication (JWT auth, RBAC roles) | Functional | Platform | Implicit (Silence Pass) | Medium |

---

## Cancellation Policy Contradiction Resolution & Priority Rule

- **Contradiction Identified**: Original P1/P2 specified custom provider policies, whereas Ops clarification specified universal 100% refund within 24h of booking.
- **Resolved Business Priority Hierarchy**:
  1. Platform Baseline: All cancellations made within 24 hours of booking receive a 100% full refund (platform guarantee).
  2. Provider Custom Policy: Applies to cancellations made *after* 24 hours from booking but prior to session start (e.g., 50% partial refund vs 0% non-refundable).
  3. No-Show Flagging: Overrides refunds if provider flags user for no-show after session window passes.
