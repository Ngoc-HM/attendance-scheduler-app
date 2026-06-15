# Phase 03 — F-05 / F-06 Leaves + Shift-Change Requests (Registration, Windows, Approval, Conflict Priority)

## Context Links
- Spec: §4.3 / F-05, F-06, §5.4 #9, §6, §7 (registration windows).
- Files: `backend/app/services/leave_service.py`, `backend/app/api/v1/endpoints/leaves.py`, `backend/app/schemas/leave.py`, `backend/app/models/leave.py`, `backend/app/models/enums.py` (LeaveType/LeaveStatus).

## Overview
- Priority: P1 (produces approved-off cells, a scheduler input).
- Status: pending. Depends on 01.
- Leave registration with windows, admin approve/reject, conflict-priority tie-break.

## Key Insights
- Two buckets (enums exist): `monthly` (<5 consecutive days, register each month, close on 20th); `annual` (>=5 consecutive days, window opens prior-year Jan–Dec).
- REGISTRATION CYCLE (decision #10): during month M, days 1–20, users register for month M+1; closes end of day 20 (then day-20 autorun generates, phase 05).
- SHIFT-CHANGE REQUESTS (decision #8, spec §3): any user requests a change on an OWN cell of a published/draft schedule — `change_code` (new code for that day) or `swap_with` (exchange that day's codes with a colleague). Admin approves/rejects. M/T = routine; A1–A4 requests carry a `strict_review` flag in responses (admin may refuse per §3). Apply-to-schedule + hard-rule re-check happens via phase 05's `apply_shift_change` helper.
- Conflict priority (§5.4 #9 / §6): when multiple request same day → (a) higher `carry_comp` first, (b) ensure each keeps 2 X/week, (c) weekend pairing. Mostly resolved at approval time; engine has an optional soft term (phase 04).
- Sick (S) is NOT a leave request — admin records it via attendance (phase 06), GDPR §9.1.
- Approved leave maps to `approved_off` for the solver as OFF; concrete code (AL/CD) restored on persist.

## Requirements
Functional:
- Create leave request: auto-classify `monthly` vs `annual` by consecutive-day length (>=5 → annual).
- Enforce registration window: monthly closes day 20 (configurable); annual window = prior calendar year.
- Admin approve/reject (sets status, audit-logged in phase 10).
- Conflict resolver: given competing same-day requests, rank by carry_comp desc; expose ordering to admin (admin makes final call for fixed group, §3).
- `approved_off_map(year, month)` → `{user_id: {date: AttendanceCode}}` for the scheduler.
- On AL approval: decrement `users.annual_leave_balance` by the day count (simple counter, no complex accrual per F-14 note); restore on later rejection/cancel. Reject if balance insufficient (admin may override).
- Shift-change: create (own cell only), list own/all (admin), approve → calls phase-05 `apply_shift_change` (update assignment(s), re-check hard rules, return warnings), reject. Both kinds audit-logged (phase 10).

Non-functional: window checks return clear 4xx with reason; idempotent re-submit guarded.

## Architecture
Data flow: user submits → validate window + bucket → `LeaveRequest(pending)` → admin approves → status=approved → `approved_off_map` feeds `SolverInput.approved_off`. Conflict ranking is a read-time helper over pending requests for a date.

## Related Code Files
Modify:
- `backend/app/services/leave_service.py` — implement create/list/approve/reject + `approved_off_map` + window validation.
- `backend/app/api/v1/endpoints/leaves.py` — wire endpoints (submit own, list own/all, approve/reject admin).
- `backend/app/schemas/leave.py` — request/response schemas incl. classification + conflict-rank result.

Create:
- `backend/app/services/leave_windows.py` — pure window/bucket logic (days 1–20 of M for M+1; annual prior-year), <200 LOC, testable.
- `backend/app/services/leave_conflict_resolver.py` — ranking by carry_comp (and weekend/2-off hints), testable.
- `backend/app/services/shift_change_service.py` — create/list/approve/reject shift-change requests (decision #8), <200 LOC.
- `backend/app/api/v1/endpoints/shift_changes.py` — POST request, GET own/all, POST decide; register in router.
- `backend/app/schemas/shift_change.py` — request/response schemas incl. strict_review flag.

Delete: none.

## Implementation Steps
1. `leave_windows.py`: `classify(start,end)` → monthly/annual (consecutive span >=5 → annual); `is_window_open(type, today, target_month)` (monthly closes day 20; annual = prior year).
2. Implement `create_request`: validate window, classify, persist pending.
3. Implement `list_requests` (own vs all by role), `approve`, `reject`.
4. `leave_conflict_resolver.py`: `rank(requests, users)` by carry_comp desc; tie-break stable.
5. Implement `approved_off_map(db, year, month)`: approved requests → per-user per-date code (AL for annual, AL for monthly leave; CD handled in calc phase).
6. Wire endpoints with RBAC (user submits own; admin approves).
7. `shift_change_service`: create (validate own cell + schedule exists), list, approve (delegate apply to phase-05 helper; stub the call until 05 lands — service interface defined here), reject. `strict_review = requester.role.is_fixed`.
8. Wire `shift_changes` endpoints + schemas; decrement/restore `annual_leave_balance` on AL approve/reject.

## Todo List
- [ ] leave_windows: classify + window checks
- [ ] create_request with window enforcement
- [ ] list/approve/reject
- [ ] conflict resolver (carry_comp ranking)
- [ ] approved_off_map for scheduler
- [ ] shift_change_service (create/list/approve/reject + strict_review flag)
- [ ] shift_changes endpoints + schemas
- [ ] annual_leave_balance decrement/restore on AL decisions
- [ ] wire + guard endpoints

## Success Criteria
- 6-day request auto-classified `annual`; 3-day → `monthly`.
- Monthly request after day 20 for next month → rejected with window error.
- Approve flips status; `approved_off_map` includes the cells with AL code.
- Two same-day requests ranked by carry_comp (higher first).
- Monthly request submitted day 21 of M for M+1 → window error; day 1–20 → accepted.
- Shift-change: user creates request on own cell; A1–A4 request carries strict_review=true; approve updates assignment + returns re-check warnings (with phase 05); approved AL reduces annual_leave_balance.

## Risk Assessment
- Window edge cases (month rollover, leap, prior-year annual) (Med/Med) → unit-test boundaries.
- Conflict resolution disputes for fixed group (Med/Low) → admin override is final per §3; resolver is advisory.

## Security Considerations
- Users see only own requests (RBAC, phase 10). Approve/reject admin-only + audit.

## Next Steps
Unblocks phase 05 (approved_off input) and phase 09 (leaves_page wiring).
