# Module 02 Diagnosis Notes: LinkOps Reading Logs Like a Story

## Bug 3: Log Level Misconfiguration (Missing Context for Errors)
- **Symptom**: Error logs (404, 500) appear in stdout without preceding request intake or response execution logs.
- **Hypothesis**: Hardcoded logger config level (`WARN`) overrides environment variable (`LOG_LEVEL=info`).
  - **Command**: `grep -rn "LOG_LEVEL" app/` & `grep -rn "logging.basicConfig" app/`
  - **Observation**: Logger config hardcoded level to `WARN` via short-circuit fallback `config.get('log_level') or os.getenv('LOG_LEVEL')`.
- **Fix**: Removed hardcoded `WARN` override and configured logger to respect `LOG_LEVEL` environment variable.
- **Verification proof**: Requests now produce complete JSON log timelines: `request_received` -> `processing` -> `response_sent`.

## Bug 4: Timestamp Timezone Mismatch (Midnight 404 Discrepancy)
- **Symptom**: Links created near midnight UTC temporarily return 404 for several hours before resolving cleanly.
- **Hypothesis**: Timezone mismatch between application UTC logger/query bounds and database server local time storage.
  - **Command**: `SELECT created_at FROM links WHERE short_code = 'xK9mQ';` vs Application UTC ISO string log
  - **Observation**: DB saved naive local timestamp while application queried with `created_at > NOW() AT TIME ZONE 'UTC'`, creating a 5-hour time window gap around UTC midnight.
- **Fix**: Normalized all application models, DB schema default values, and query filters to explicit UTC ISO-8601 timestamps.
- **Verification proof**: Verified created link timestamp in DB equals UTC log timestamp (`2025-01-15T23:58:00.000Z`).
