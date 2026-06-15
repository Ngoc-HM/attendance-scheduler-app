# Phase 06 — F-10 / F-11 / F-12 / F-13 Attendance, Sick Handling, Holidays

## Context Links
- Spec: §4.4 F-10, §4.5 F-11/F-12/F-13, §6 (sick), §9.1 (S = special-category). Locked decision #5 (PH = working day).
- Files: `backend/app/services/{attendance_service,holiday_service}.py`, `backend/app/api/v1/endpoints/{attendance,holidays}.py`, `backend/app/schemas/attendance.py`, `backend/app/models/{attendance,holiday}.py`.

## Overview
- Priority: P1. Depends on 01, 05.
- Record actual attendance per day; handle sick (S) with forced A/D backfill; admin leave-status updates; holiday CRUD as premium-off markers (NOT auto-off).

## Key Insights
- AttendanceRecord = ACTUAL (vs planned ShiftAssignment). One code/(user,day).
- F-10 sick: on S, a backfill A/D is required to cover the dropped shift. The just-sick person is prioritized/forced to do A/D if SOMEONE ELSE later goes sick (§6) — track "recently sick" ordering.
- F-13 + decision #5: holidays are working days; Holiday rows are premium-off markers consumed by premium-off objective (phase 04) + reports. Do NOT auto-set X.
- §9.1: S is health data — admin-only write/read, separate access path (phase 10 enforces; this phase keeps S in the same table but flags access).

## Requirements
Functional:
- F-11: upsert actual attendance cell (admin records, or seed from published schedule then adjust).
- F-12: admin updates leave/sick status (S, AL, X, etc.) for a (user,day).
- F-10: when admin sets S on a covered shift day, service flags the uncovered shift and suggests/forces an A/D backfill candidate; the sick person is queued as forced A/D for a subsequent sick event.
- F-13: holiday CRUD (create/list/delete). Holidays NOT pinned off.
- `actual_records_map(year, month)` for calc/reports.

Non-functional: S writes audit-logged; access restricted (phase 10).

## Architecture
Data flow: published ShiftAssignment → seed AttendanceRecord (planned=actual initially) → admin edits actuals → calc/reports read actuals. Sick handler: set S → find that day's shift coverage gap → pick backfill (prefer previously-sick queue) → propose A/D record. Holiday: list feeds `SolverInput.holidays` (premium-off only).

## Related Code Files
Modify:
- `backend/app/services/attendance_service.py` — upsert record, update status (F-12), sick handler (F-10), actual_records_map, seed-from-schedule.
- `backend/app/services/holiday_service.py` — CRUD; `holiday_dates(year, month)` for scheduler.
- `backend/app/api/v1/endpoints/attendance.py` — wire (record, update-status, sick) admin-guarded; user read-own.
- `backend/app/api/v1/endpoints/holidays.py` — wire CRUD admin-guarded.
- `backend/app/schemas/attendance.py` — record/update/sick-backfill schemas.

Create:
- `backend/app/services/sick_backfill.py` — backfill candidate selection + recently-sick queue logic (<200 LOC, testable).

Delete: none.

## Implementation Steps
1. `attendance_service.upsert_record` + `seed_from_schedule(year,month)` (copy published assignments to actuals).
2. `update_status` (F-12): admin sets code for (user,day) incl. S/AL/X.
3. `sick_backfill.py`: given S on (user,day), compute uncovered A/D shift; choose backfill (priority: people in recently-sick queue, then least-loaded); return proposal. Maintain recently-sick set per month.
4. Integrate sick handler into `update_status` when code==S.
5. `holiday_service` CRUD + `holiday_dates`.
6. `actual_records_map` for phases 07/08.
7. Wire endpoints + RBAC; audit S writes.

## Todo List
- [ ] upsert_record + seed_from_schedule
- [ ] update_status (F-12)
- [ ] sick_backfill candidate logic + recently-sick queue
- [ ] integrate sick handler (F-10)
- [ ] holiday CRUD + holiday_dates
- [ ] actual_records_map
- [ ] wire + guard endpoints; audit S

## Success Criteria
- Setting S on a shift day returns a backfill A/D proposal; second sick event forces the first sick person as A/D candidate.
- Holiday create does NOT change any assignment to X; holiday_dates returns the dates for premium-off.
- F-12 status update persists and is audit-logged for S.
- actual_records_map returns one code per (user,day).

## Risk Assessment
- Backfill picks unavailable person (Med/Med) → exclude off/leave/sick people; fall back to A/D slack suggestion.
- Holiday-as-working contradicts old docstring/tests (Med/Low) → update docs (phase 12) + tests.
- S leakage to non-admin (Low/High) → phase 10 enforces; keep S out of user-facing read paths here.

## Security Considerations
- S = special-category (§9.1): admin-only write+read, separate query path, no medical detail stored, audit every S write.

## Next Steps
Unblocks phase 07 (calc reads actuals), 08 (reports), 09 (attendance_page wiring).
