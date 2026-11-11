# Module 07: Blast Radius Analysis (Updated with Secondary RBAC Change)

## Part 1: Company Accounts & RBAC Blast Radius

| Artifact | Status | Impact |
|----------|--------|--------|
| User data model | MAJOR | Escalated from MINOR to MAJOR. Need `role` (enum: `manager`, `employee`, `dept_head`), `department_id`, and `company_id` columns in `users` table. |
| Auth/JWT system | MAJOR | Escalated from NO IMPACT to MAJOR. JWT payload must include `role`, `department_id`, and `company_id` claims for endpoint authz checks. |
| Booking flow (API) | MAJOR | `POST /api/bookings` and `GET /api/bookings` updated: Managers can book for any employee; Dept Heads can view all dept bookings; Employees can only view own bookings. |
| Booking flow (UI) | MAJOR | Delegation modal updated to show employee/department picker based on user's JWT role claims. |
| Provider dashboard | MINOR | Display booking role/department metadata on provider schedule cards. |
| Search/listing | NO IMPACT | Provider search and slot retrieval remain unimpacted. |
| Payment/billing | NO IMPACT | Company invoicing stays centralized under company user billing account. |
| Interface contracts between streams | MAJOR | Contracts updated to include `role` claims in Auth headers and `department_id` in booking authorization schema. |
| Tickets: completed | MINOR | TICKET-03 (Auth) updated to issue `role` and `department_id` in JWT payload upon login. |
| Tickets: in progress | MAJOR | TICKET-02 (Booking API) updated with RBAC middleware enforcing scope rules (Manager/Dept Head/Employee). |
| Tickets: not started | MAJOR | TICKET-08 (RBAC Middleware & Department Schema) added; Escrow Payment (TICKET-04) moved to CUT to preserve 6-day deadline. |

---

## Part 2: Compressed Timeline Categorization (Updated 6-Day Scope)

| Ticket ID & Title | Category | Rationale |
|-------------------|----------|-----------|
| TICKET-01: Provider Slots API | MUST SHIP | Completed. Core availability retrieval. |
| TICKET-02: Booking API with RBAC Scope | MUST SHIP | Updated with RBAC enforcement for Meridian IT director requirements. |
| TICKET-03: User Auth & JWT Role Claims | MUST SHIP | Updated to embed `role` and `department_id` into JWT tokens. |
| TICKET-08: RBAC & Dept Schema Bridge | MUST SHIP | NEW. Required for manager/employee/dept_head permission enforcement in demo. |
| TICKET-04: Escrow & Live Payment Spike | CUT | Reclassified from SHOULD SHIP to CUT due to RBAC scope increase. Live demo fallback to simulated payment confirmation. |
| TICKET-05: Admin Dispute Dashboard | CUT | Retained as CUT. Post-demo release item. |
| TICKET-07: Multi-City Search | CUT | Retained as CUT. Post-demo release item. |
