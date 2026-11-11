# Module 07: Updated Execution Plan (Post-RBAC Adaptation)

## 1. Preserved & Patched Tickets
- **TICKET-01: Provider Slots API**: Status `COMPLETED`. Slot retrieval logic remains unchanged.
- **TICKET-03: User Auth & JWT Claims**: Status `PATCHED`. Updated login handler to embed `role` (`manager`, `employee`, `dept_head`) and `department_id` claims in JWT payload.

---

## 2. Modified Tickets
- **TICKET-02: Booking Transaction API with RBAC Enforcement**
  - **Modification**: Added role-based access control middleware. Enforced rules: Managers can initiate delegated bookings for any employee; Dept Heads can query all department bookings; Employees can only access own bookings.
  - **Status**: `IN_PROGRESS` (85% complete).

---

## 3. Cut Tickets (Descoped for 6-Day Target)
- **TICKET-04: Escrow & Live Payment Integration**: Reclassified to `CUT` to accommodate mandatory RBAC work within the 6-day window. Live demo will use simulated payment confirmation.
- **TICKET-05: Admin Dispute Dashboard**: Retained as `CUT`. Post-demo sprint delivery.
- **TICKET-07: Multi-City & Advanced Search Filtering**: Retained as `CUT`. Post-demo sprint delivery.

---

## 4. Added Tickets
- **TICKET-08: RBAC Middleware & Department Schema Bridge**
  - **Scope**: Create lightweight `department` entity, add role/department columns to user model, and implement express RBAC authorization middleware.
  - **Estimate**: `M` (1.5 days).
