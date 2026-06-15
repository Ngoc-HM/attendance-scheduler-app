# System Architecture

Automatic shift-scheduling + attendance for airline ground staff (Frankfurt).
Core feature = **automatic schedule generation** (constraint solver), not just
time tracking. Spec: `PROJECT_OVERVIEW.md`. Key choices: `design-decisions.md`.

## Components
```
Flutter desktop (Windows)  ──HTTPS / JWT──►  FastAPI  ──►  PostgreSQL (EU/Frankfurt)
   feature-first /                            layered:       shared by all clients
   clean architecture                api → services → models
                                            └► scheduler/ (OR-Tools CP-SAT, §5)
                                            └► APScheduler (day-20 autorun, #9)
```

## Backend layers (`backend/app/`)
- `core/` — config, database, security (JWT/bcrypt), i18n (en/vi), bootstrap.
- `models/` — SQLAlchemy ORM + enums (roles §3, attendance codes §7).
- `schemas/` — Pydantic DTOs (the API contract).
- `api/v1/endpoints/` — thin HTTP handlers; RBAC via `deps.AdminUser` / `ensure_self_or_admin`; audit on every admin mutation.
- `services/` — business logic, one module per domain (+ focused helpers, each <200 LOC).
- `scheduler/` — the CP-SAT engine.

## Data flow (one month)
```
flights (F-04) ─┐
leaves  (F-05/06)┤
holidays(F-13)  ─┤─► schedule_input_builder ─► SolverInput ─► SchedulerEngine.solve
carry_* (F-14)  ─┘                                                   │
                                                                     ▼
                              persist draft ShiftAssignment + Violations (§5.6)
                                          │ (admin override F-09 / publish)
                                          ▼
              actuals: AttendanceRecord (F-11/12) ◄─ seed ─ published schedule
                          │  sick S → A/D backfill (F-10, §6)
                          ▼
              calculations close (F-14): carry_comp / carry_streak / carry_premium_off
                          ▼
              reports (F-15): ReportTable ─► CSV / XLSX serializer
```

## Scheduler engine (`scheduler/`, §5)
- Decision vars `x[(user_id, day, code)]` bool over `{A, D, A/D, O/D, X}`.
- **Hard** (`constraints.py`): exactly-one-status-per-day; approved-off pinned X.
- **Soft + slack** (always-feasible, decision #2):
  - `constraints_off_days.py` — 2 X per 7-day block (target += pinned leave, #4).
  - `constraints_consecutive.py` — ≤5 consecutive working days incl. `carry_streak` boundary (§5.5).
  - `constraints_staffing.py` — A1–A4 demand per `flight_pairs` (A/D covers one A + one D, §5.3 #6).
- **Objectives** (`objectives.py` + `objective_*`): balance A/D (100) > premium-off (30) > weekend pairing (10); A/D-usage and non-fixed-flight-duty shaping terms.
- `slack_registry.py` collects slack vars (weight 10 000) → `Violation`s after solve.
- Deterministic (`random_seed = 42`); time-limited (`SOLVER_MAX_TIME_SECONDS`).

## Frontend (`attendance_scheduler_app/lib/`)
Feature-first clean architecture. `core/` (Dio client + JWT interceptor,
go_router, secure storage), `features/<x>/{data,domain,presentation}` (auth is
the template; flights/leaves/schedule/attendance/reports/users follow it),
`design_system/` (reusable `Ds*View` widgets), `i18n/` (custom en/vi, graceful
`text(key)` fallback).

## Compliance posture (§9 → `deployment-guide.md`)
EU/Frankfurt region; sick `S` is special-category (admin-only read/write, no
medical detail, audited); RBAC; audit log on admin actions; rule-based engine
(no AI staff evaluation, §9.6). Final legal sign-off: customer DPO.
