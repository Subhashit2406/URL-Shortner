# Module 07: Adaptation Note & PM Impact Statement (Updated with RBAC Scope)

## Executive Summary & PM Communication
Following Meridian IT's new requirement for role-based access (Managers booking for employees, Department Heads viewing department bookings, Employees restricted to personal bookings), we have updated our 6-day plan.

To accommodate RBAC authorization without risking our investor demo date, we are reclassifying live Stripe payment integration (TICKET-04) from SHOULD SHIP to CUT, using a simulated payment confirmation flow during the demo.

The demo will deliver complete individual booking, company delegation, AND role-based authorization (Manager, Department Head, Employee).

Action needed from you: confirm Meridian IT agrees to test with pre-seeded role credentials (`manager@meridian.com`, `depthead@meridian.com`) for the 6-day trial.
