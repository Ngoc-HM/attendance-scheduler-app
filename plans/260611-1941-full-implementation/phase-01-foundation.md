# Phase 01 — Foundation

## Context Links
- Spec: `PROJECT_OVERVIEW.md` §5.1, §5.5, §7; Locked decisions 4,5,6,7.
- Files: `backend/app/models/{user,holiday}.py`, `backend/app/scheduler/{calendar_utils,domain}.py`, `backend/app/core/{config,bootstrap,database}.py`, `backend/alembic/`.

## Overview
- Priority: P1 (blocks everything).
- Status: ✅ COMPLETE (2026-06-11). Dev DB stamped 0001 + upgraded to 0002; 12/12 tests pass.
- Establish DB fields, week model, holiday semantics, config, and a migration strategy before any feature work.

## Key Insights
- Tables auto-create via `Base.metadata.create_all` (bootstrap.py:67). `create_all` does NOT ALTER existing tables → new columns on `users` won't appear on an existing DB.
- `alembic/` exists but `versions/` is empty (0 migrations).
- Holiday model currently documents "PH = OFF (X)". Locked decision #5 reverses this: PH = working day; holiday rows become premium-off markers only.
- `build_weeks` is Monday-anchored; decision #7 changes to 7-day blocks from day 1.
- `PersonInput` (domain.py) needs `carry_premium_off`.

## Requirements
Functional:
- `users` table gains `carry_premium_off` (int, default 0). `carry_comp`/`carry_streak` already exist.
- NEW `shift_change_requests` table (decision #8): id, requester_id FK users, work_date, kind enum('change_code','swap_with'), requested_code (nullable AttendanceCode), counterpart_user_id (nullable FK users), note, status (reuse LeaveStatus pending/approved/rejected), decided_by_id (nullable FK), decided_at, timestamps. Fixed-group strict-review flag derivable from requester role (no extra column).
- `calendar_utils.build_weeks` returns 7-day blocks anchored at day 1; helper for partial-block X target = `round(k/7*2)`.
- Holiday treated as a premium-off marker, NOT auto-pinned OFF.
- Config flags for solver weights/time limit centralized.

Non-functional: migrations reproducible; no data loss on existing dev DB.

## Architecture
Data flow: `users.carry_*` → `schedule_service` reads → `PersonInput` → engine. `holidays` → premium-off set → objectives (phase 04) + reports (phase 08). Week blocks → engine "2 X / block" + max-consecutive windows.

Migration strategy (DECISION): adopt **Alembic** as authoritative. Generate a baseline migration capturing current schema, then an incremental migration adding `carry_premium_off`. Keep `create_all` ONLY for the fresh-bootstrap path (empty DB); document that schema changes after this phase go through Alembic. This avoids silent column drift.

## Related Code Files
Modify:
- `backend/app/models/user.py` — add `carry_premium_off`.
- `backend/app/models/holiday.py` — docstring: premium-off marker, not OFF; optional `is_premium_off` stays implicit (every holiday row is a premium marker).
- `backend/app/scheduler/calendar_utils.py` — rewrite `build_weeks`; add `partial_block_off_target(block_len)`.
- `backend/app/scheduler/domain.py` — add `carry_premium_off: int = 0` to `PersonInput`; add `holidays: set[date]` + `premium_off_target`/weights fields to `SolverInput` (or pass via config).
- `backend/app/core/config.py` — solver settings (time limit, weights) if not present.
- `backend/app/core/bootstrap.py` — note create_all is fresh-DB only.

Create:
- `backend/app/models/shift_change_request.py` — ShiftChangeRequest model (decision #8); add `SwapKind` enum to enums.py.
- `backend/alembic/versions/0001_baseline.py` — baseline schema.
- `backend/alembic/versions/0002_add_carry_premium_off_and_shift_changes.py` — add users.carry_premium_off + shift_change_requests table.

Delete: none.

## Implementation Steps
1. Add `carry_premium_off` to `User`.
2. Add `carry_premium_off` to `PersonInput`; add `holidays: set[date]` to `SolverInput`.
2b. Create `ShiftChangeRequest` model + `SwapKind` enum; register in models `__init__`.
3. Rewrite `build_weeks(days)`: group by `(day.day - 1) // 7` → blocks 1-7, 8-14, 15-21, 22-28, 29-end.
4. Add `partial_block_off_target(block_len: int) -> int` returning `round(block_len/7*2)` (full block → 2).
5. Update `holiday.py` docstring per decision #5.
6. Configure Alembic `env.py` to import `Base.metadata`; verify `alembic.ini` URL pulls from settings.
7. `alembic revision --autogenerate -m baseline` → review → commit as `0001_baseline.py`.
8. `alembic revision --autogenerate -m add_carry_premium_off` → `0002_*`.
9. Run `alembic upgrade head` against dev DB; confirm column exists.

## Todo List
- [x] Add `carry_premium_off` to User model
- [x] Add `carry_premium_off` + `holidays` to domain dataclasses
- [x] Create ShiftChangeRequest model + SwapKind enum (decision #8)
- [x] Rewrite `build_weeks` to 7-day blocks
- [x] Add `partial_block_off_target` helper
- [x] Update holiday docstring (PH = working day)
- [x] Wire Alembic env.py to Base.metadata (was already wired)
- [x] Generate baseline (0001) + delta (0002) migrations
- [x] `alembic stamp 0001` + `upgrade head` succeeded on dev DB; fresh-DB path verified on tmp DB

## Success Criteria
- `alembic upgrade head` creates/updates schema with `users.carry_premium_off` present.
- `build_weeks([1..30 Jun])` → blocks `[1-7],[8-14],[15-21],[22-28],[29-30]`; `partial_block_off_target(2)==1`.
- Existing `test_calendar_utils.py` updated to new week semantics and passing.

## Risk Assessment
- Monday-anchored tests break (High likelihood, Low impact) → update tests in same phase; flag old expectations.
- Alembic autogenerate misses enum types / drift (Med/Med) → manually review baseline before commit.
- create_all vs Alembic double-management (Med/Med) → document create_all = fresh-DB only; CI uses Alembic.

## Security Considerations
- No new PII. `carry_*` are operational integers.

## Next Steps
Unblocks phases 02, 03, 04. Engine (04) consumes new week blocks + `holidays` + `carry_premium_off`.
