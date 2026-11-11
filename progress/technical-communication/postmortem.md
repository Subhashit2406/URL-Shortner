# Incident Postmortem: Silent Order Loss during OrderProcessor v2.14 Release

## Summary
On Wednesday, between 14:00 and 16:02 UTC (2 hours 2 minutes), `OrderProcessor` release v2.14 caused completed customer checkouts to silently drop orders without persisting them to the database or emitting confirmation emails, despite returning HTTP 200 OK responses to payment gateways and clients. Approximately 1,400 orders totaling $186,000 in revenue were affected. The incident was detected following customer escalation to support, escalated to the platform team after automated rollback scripts failed due to stale artifact paths, and resolved via manual rollback to v2.13 at 15:34 UTC. All 1,400 dropped orders were reconciled from payment processor logs and reprocessed by 16:02 UTC with zero revenue loss.

## Timeline

| Time (UTC) | Event / Observation | Impact / Phase |
| :--- | :--- | :--- |
| **14:00** | `OrderProcessor` v2.14 deployed to production. Release removed deprecated config field `warehouse_routing` following standard 6-month deprecation notice. | **Trigger** |
| **14:00–14:22** | Synthetic health checks and latency dashboards show 100% GREEN (HTTP 200 OK). Silent dropping of orders begins immediately. | **Silent Outage** |
| **14:22** | Customers report missing confirmation emails on social media. Customer support ticket volume increases. | **First Signal** |
| **14:23** | Customer Support flags issue in `#cs-escalations`. Triage assumes third-party email provider latency; no engineering investigation initiated. | **Escalation Delay** |
| **14:38** | Second wave of support tickets arrives; on-call engineer begins active investigation. | **Detection Start** |
| **14:42** | Monitoring dashboard inspection shows normal CPU, memory, latency, and 0% HTTP 5xx error rates. | **Diagnostic Ambiguity** |
| **14:55** | Direct DB query reveals 0 orders written since 14:00 UTC despite active payment captures. Severity elevated to SEV-1. | **Diagnosis** |
| **15:02** | On-call engineer identifies v2.14 config change as root trigger and initiates automated rollback. | **Mitigation Start** |
| **15:08** | Automated rollback script fails due to hardcoded legacy artifact path from infrastructure migration 4 months prior. | **Mitigation Failure** |
| **15:15** | On-call engineer escalates to Platform Engineering for emergency manual rollback. | **Escalation** |
| **15:34** | Platform team successfully completes manual deployment of v2.13. Order creation pipeline restored. | **Mitigation Completed** |
| **15:45** | Automated reconciliation worker script initiated to reconstruct lost orders from payment processor logs. | **Recovery** |
| **16:02** | All 1,400 dropped orders successfully reprocessed into DB and confirmation emails dispatched. Incident closed. | **Resolution** |

---

### Five-Whys Analysis
1. **Why were customer orders dropped while charges succeeded?**
   `OrderProcessor` returned HTTP 200 OK to checkout clients without persisting orders to the database.
2. **Why did `OrderProcessor` return HTTP 200 when database persistence failed?**
   The application caught missing configuration field exceptions in a generic top-level `try/except` block, logged the exception as `DEBUG`, and continued the HTTP response cycle.
3. **Why was the configuration field `warehouse_routing` missing in v2.14?**
   The field was removed during scheduled configuration cleanup, but v2.13 runtime code still depended on `warehouse_routing` for fulfillment routing logic.
4. **Why was this field dependency not detected in staging prior to production deploy?**
   Staging environment configuration schemas diverged from production and never contained the `warehouse_routing` field, masking runtime fallbacks during pre-release testing.
5. **Why did the outage persist for over 2 hours without automated detection or fast recovery?**
   Monitoring was restricted to HTTP status codes rather than business-transaction volume (orders per minute), and automated rollback automation had not been validated since the infrastructure migration.

---

## Root Cause(s)
1. **Defensive Anti-Pattern (Broad Exception Suppression):** The `OrderProcessor` codebase encapsulated order initialization in a generic catch-all `except Exception` block that swallowed missing configuration exceptions, downgraded error logging to `DEBUG`, and allowed request execution to report HTTP 200 success without validating transaction persistence.
2. **Telemetry & Black-Box Monitoring Deficit:** Production health probes and alerting relied exclusively on network metrics (HTTP 200 status codes, CPU/memory utilization, latency) rather than application payload validation or business-critical transaction counters (orders created per minute dropping below threshold).
3. **Staging & Production Configuration Schema Divergence:** Staging environments lacked schema alignment with production configuration files, preventing CI/CD validation tools and automated test suites from catching missing configuration dependencies prior to deployment.

---

## Contributing Factors
1. **Stale Rollback Automation:** Rollback scripts contained deprecated artifact storage paths from an infrastructure migration performed 4 months earlier. The rollback procedure was not integrated into routine CI/CD validation, extending recovery duration by 26 minutes while requiring manual Platform team intervention.
2. **Single-Metric Escalation Assumptions:** Initial customer escalations were categorized as email vendor delivery delays because monitoring dashboards reflected 100% HTTP 200 availability, delaying active engineering investigation by 15 minutes.
3. **Configuration Deprecation Pipeline Deficit:** Deprecation processes lacked automated cross-version compatibility checks between application code versions and environment configuration models.

---

## Action Items

| Item | Description | Owner (Role) | Target Deadline | Definition of Done |
| :--- | :--- | :--- | :--- | :--- |
| **ACT-01** | Replace broad `except Exception` blocks in `OrderProcessor` with explicit configuration validation and surface unhandled errors as HTTP 500. | API Lead | 2026-09-02 | PR merged with unit tests verifying HTTP 500 return and critical alert dispatch on missing config fields. |
| **ACT-02** | Implement business transaction metric `orders_created_total` and configure alert `OrderVolumeZero` firing when 0 orders are written over 5 consecutive minutes during operational hours. | Observability Lead | 2026-09-05 | Alerting rule deployed to Prometheus/Grafana, tested via synthetic zero-order staging simulation. |
| **ACT-03** | Automated continuous staging-to-production configuration schema parity check in CI/CD build pipeline. | DevOps Lead | 2026-09-10 | CI pipeline step fails builds automatically if production config schema keys diverge from staging schema. |
| **ACT-04** | Fix automated rollback script paths and add automated weekly zero-downtime rollback drill in staging. | Platform Lead | 2026-09-15 | Automated rollback succeeds in staging CI environment within <3 minutes without manual engineering intervention. |
| **ACT-05** | Update incident triage runbook with cross-validation playbook between CS ticket spikes and payment processor transaction logs. | Incident Response Lead | 2026-09-08 | Published runbook in `/docs/runbooks.md` updated with explicit verification commands for support escalations. |

---

## Lessons Learned
- **What Surprised Us:** HTTP status code monitoring alone is insufficient for verifying application health. A service can report 100% HTTP 200 success while failing 100% of core business operations.
- **What Worked Well:** Payment processor transaction logs provided complete auditability, enabling 100% automated financial and order recovery without revenue loss or double-charging.
- **What We Would Do Differently:** In the event of diagnostic ambiguity between HTTP health metrics and customer escalations, engineers will query backend persistence stores directly before assuming third-party vendor failure.
