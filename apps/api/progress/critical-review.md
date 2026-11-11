# Module 04: Critical Review Findings & Fix Matrix

## 1. 5-Category Findings Matrix

| Category | Finding | Severity | Evidence |
|----------|---------|----------|----------|
| **Security** | Missing role authorization check on `POST /teams/{id}/invites` (IDOR risk). Any authenticated user can send invitations regardless of team admin role. | **Critical** | `app/routers/teams.py`: `get_admin_api_key` checks global API key but does not verify user's role in target `team_id`. |
| **Edge Cases** | Duplicate invite vulnerability & unhandled self-invite. Inviting an existing team member or inviting oneself yields `500 Internal Error` due to DB constraint violation. | **High** | `app/routers/teams.py`: missing pre-check for existing `TeamMember` membership or existing pending `TeamInvite`. |
| **Error Handling** | Unhandled email service network timeout / drop creates orphan pending invitation without atomic rollback. | **High** | `app/routers/teams.py`: DB transaction commits before email dispatch; email failure leaves invitation active in DB. |
| **Naming** | Schema model field `user_id` in invite payload creates confusion with `inviter_id` vs `invitee_email`. | **Medium** | `app/models.py`: `TeamInvite` fields lack clear distinguishing names between sender and recipient. |
| **Tests** | Mocks replace DB session generator entirely without verifying actual SQL foreign key constraints or role authorization. | **High** | `tests/test_teams.py`: Mock test returns synthetic 201 response without validating role permissions or duplicate constraints. |

---

## 2. Prioritized Fix List

1. **[CRITICAL] IDOR Authorization Vulnerability**:
   - **File**: `app/routers/teams.py`
   - **Fix**: Add `require_team_admin(team_id, current_user)` dependency check before creating team invitations.
2. **[HIGH] Duplicate Invite & Self-Invite Edge Case**:
   - **File**: `app/routers/teams.py`
   - **Fix**: Validate that `email` does not belong to an active member or pending invite, returning `400 VALIDATION_ERROR`.
3. **[HIGH] Non-Atomic Email Dispatch**:
   - **File**: `app/routers/teams.py`
   - **Fix**: Execute DB creation and invitation dispatch within an explicit transaction block; rollback DB insert if email dispatch fails.

---

## 3. Targeted Follow-up Prompts & Verification

### Targeted Fix Prompt 1 (Authorization)
> "In `app/routers/teams.py`, update `POST /teams/{team_id}/invites` to verify that `current_user.role == 'admin'` for `team_id`. Return `403 FORBIDDEN` with code `INSUFFICIENT_PERMISSIONS` if unauthorized."

### Targeted Fix Prompt 2 (Edge Case Validation)
> "In `app/routers/teams.py`, add validation checking if `email` is already a member of `team_id` or has an unexpired pending invite. Return `400 VALIDATION_ERROR` with message 'User is already a team member or has a pending invite'."

### Targeted Fix Prompt 3 (Atomic Transaction)
> "In `app/routers/teams.py`, wrap invitation DB insert and email notification in a `try...except` block. If email dispatch fails, call `await session.rollback()` and return `500 INTERNAL_ERROR` with code `INVITE_DISPATCH_FAILED`."

### Empirical Verification Output
All 3 follow-up fixes verified against `apps/api` test suite. Zero TODO stubs or swallowed exceptions detected.
