# Phase 03 — Backend time-clock (check-in / check-out)

## Context Links
- Plan: [plan.md](plan.md) — independent (Wave 1, parallel with P01/P05)
- Model pattern: `backend/app/models/attendance.py`; router: `backend/app/api/v1/router.py`
- Deps: `backend/app/api/deps.py` (`ActiveUser`); audit: `audit_service.record`; migration pattern: `alembic/versions/0004_*.py`

## Overview
Priority P2. Status pending. Brand-new time-clock: employees record real
check-in / check-out **timestamps**. Timestamps ONLY — does NOT derive/alter the
admin attendance code grid (open Q e). One row per (user, day).

## Key Insights
- No existing time-clock; `AttendanceRecord` is a code grid, wrong shape for times → new table.
- Keep isolated: new model + service + endpoints; touches `router.py` (new sub-router) — sole owner of that edit among Wave-1 phases (P01/P05 don't touch router).
- Tests use SQLite create_all → new table auto-created; migration is Postgres prod parity.

## Requirements
- Model `TimeClockEntry`: `id`, `user_id` FK, `work_date`, `check_in_at` (tz-aware, nullable), `check_out_at` (nullable), `TimestampMixin`, unique `(user_id, work_date)`.
- `POST /attendance/clock/check-in` — own, today; set `check_in_at=now()` if null else 409 already_checked_in.
- `POST /attendance/clock/check-out` — own, today; requires prior check-in (409 if none), set `check_out_at=now()` (allow overwrite? no → 409 if already).
- `GET /attendance/clock/me?year&month` — own history (list).
- All audited.

## Architecture
Data in: authed user, server `now()` / `date.today()`. Transform: upsert row for (user, today), set the relevant timestamp. Data out: `TimeClockRead`. Admin grid untouched — decoupled from `AttendanceRecord`.

## Related Code Files
**Create:**
- `backend/app/models/time_clock.py` — `TimeClockEntry`.
- `backend/app/schemas/time_clock.py` — `TimeClockRead`.
- `backend/app/services/time_clock_service.py` — `check_in`, `check_out`, `list_month_for_user`.
- `backend/app/api/v1/endpoints/time_clock.py` — 3 routes (`ActiveUser`).
- `backend/alembic/versions/0006_add_time_clock_entries.py` — create table (down_revision `0005`).
**Modify:**
- `backend/app/models/__init__.py` — export `TimeClockEntry` (so create_all/metadata sees it).
- `backend/app/api/v1/router.py` — `include_router(time_clock.router, prefix="/attendance/clock", tags=["time-clock"])` (register BEFORE or after attendance; distinct prefix avoids path clash with `/attendance`).
- i18n `core/i18n.py` — `clock.already_checked_in`, `clock.not_checked_in`, `clock.already_checked_out`.

## Implementation Steps
1. Model with `DateTime(timezone=True)` columns + unique constraint `uq_time_clock_cell`.
2. Export in `models/__init__.py`.
3. Schemas `TimeClockRead`.
4. Service: `_get_or_create(db, user_id, day)`; `check_in` → 409 if `check_in_at` set; `check_out` → 409 if no check_in / already checked_out.
5. Endpoints under new router; audit each (`clock.check_in`/`clock.check_out`).
6. Register router with prefix `/attendance/clock`.
7. Migration 0006 `create_table`; `downgrade` `drop_table` (safe/reversible).
8. Compile import check.

## Todo List
- [ ] TimeClockEntry model + __init__ export
- [ ] schema TimeClockRead
- [ ] service check_in/check_out/list
- [ ] endpoints + router registration
- [ ] migration 0006 (up+down)
- [ ] i18n keys
- [ ] compile check

## Success Criteria
- Check-in sets `check_in_at`; second check-in → 409. Check-out requires check-in; sets `check_out_at`.
- `GET /clock/me` returns own month rows only; no other user's data.
- `alembic upgrade head`/`downgrade` create/drop table cleanly. Admin attendance grid unchanged.

## Risk Assessment
| Risk | L×I | Mitigation |
|------|-----|-----------|
| Prefix `/attendance/clock` shadowed by `/attendance` router | Low×Med | Distinct sub-path; FastAPI matches specific paths; verify order/test in P09. |
| Timezone ambiguity (server vs local "today") | Med×Med | Use UTC `now()`, store tz-aware; "today" = server date. Document; revisit if multi-tz. |
| Double check-out overwrites time | Low×Low | 409 if already checked_out. |
| Migration/model drift (table in model, not metadata export) | Low×Med | Export in `models/__init__.py`; P09 verifies create_all + alembic parity. |

## Security Considerations
- `ActiveUser` + token-derived user_id; `list_month_for_user` scoped to self (§9.5). No admin PII exposure.

## Next Steps
Unblocks P07 (check-in/out page). Fully parallel with P01, P05.

## Unresolved
- (e) timestamps only, no derived code? Admin oversight view of clock — deferred (YAGNI) unless owner needs it.
