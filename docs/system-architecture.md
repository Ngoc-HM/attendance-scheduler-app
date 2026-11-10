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
                                            └► APScheduler (monthly autorun, 00:05 on day AUTORUN_DAY+1, #9;
                                               catch-up on later days and at startup; also drafts a
                                               current month without a schedule, #55)
```
That is the target layout. Today the API runs in `ENVIRONMENT=dev` on a
workstation against a shared PostgreSQL reached over Tailscale
(`deployment-guide.md`, "The current setup").

## Backend layers (`backend/app/`)
- `core/` — config, database, security (JWT/bcrypt), i18n (en/vi), bootstrap,
  `business_time.business_today()` (the business date in `TIMEZONE`, used by
  the autorun and the leave window instead of the host clock).
- `models/` — SQLAlchemy ORM + enums (roles §3, attendance codes §7).
- `schemas/` — Pydantic DTOs (the API contract).
- `api/v1/endpoints/` — thin HTTP handlers; RBAC via `deps.AdminUser` / `ensure_self_or_admin`; audit on every admin mutation (fail-loud, decision #18).
- `services/` — business logic, one module per domain (+ focused helpers).
- `scheduler/` — the CP-SAT engine.

## Data flow (one month)
```
flights (F-04) ─┐
leaves  (F-05/06)┤
holidays(F-13)  ─┤─► schedule_input_builder ─► SolverInput ─► SchedulerEngine.solve
carry_* (F-14)  ─┘   (carry from schedule_history:                  │
                      planned cells + actuals on top, #29)           ▼
              persist draft ShiftAssignment rows; the solver's violations go back
              in the generate response only (they are NOT stored)
                                          │ regenerate: 409 if published / edited, unless force (#24)
                                          │ GET /schedules/{id}/violations: re-check on demand (#46)
                                          │ admin override F-09, shift change, publish
                                          ▼
              actuals: AttendanceRecord (F-11/12) ◄─ seed on publish ─ published schedule
                                                  ◄─ re-sync of still-seeded rows on EVERY edit or
                                                     regenerate, draft or published (#27; hidden from
                                                     employees while the month is unpublished, #52)
                          │  sick S → A/D backfill (F-10, §6; recently sick = last 30 days, #35)
                          ▼
              calculations close (F-14): stores carry_comp / carry_streak / carry_premium_off
                          ▼
              reports (F-15): ReportTable ─► CSV / XLSX serializer
```
Leave decisions after generation (#28):
```
POST /leaves/{id}/decide (approve) ─► AL into the user's cells of every generated month in the span
POST /leaves/{id}/revoke           ─► X into those cells that are still AL
        └► still-seeded actuals follow (#27) ─► re-check warnings returned to the admin
```
Months without a schedule pick approved leave up when they are generated.

## Endpoints readable by every signed-in user
- `GET /users/directory` — active users' `id`, `code`, `role` (no names), for
  the roster and the shift-change dialog (#32).
- `GET /leaves/window` — whether monthly registration is open today, for which
  month, the annual target year, `closes_on_day` (= `AUTORUN_DAY`) and whether
  the window is enforced (not in dev) (#31, #32).
- `GET /leaves/balance` — own annual-leave quota / used / pending / remaining
  (an admin may pass `user_id`) (#30).
- `GET /attendance/me` (seeded rows of a month whose schedule is not
  published are hidden, #52), `GET /schedules/{year}/{month}` (published
  months only for non-admins, at most two months ahead outside dev; a
  colleague's legacy S is masked as X), own leave and shift-change
  requests.

Every year/month parameter is bounded (year 2000–2100, month 1–12) and
answers 422 instead of 500; text fields are length-checked the same way
(#54). Known gap: an id above the 64-bit range still answers 500 on
PostgreSQL.

## Scheduler engine (`scheduler/`, §5)
- Decision vars `x[(user_id, day, code)]` bool over each person's role domain
  (`role_codes.py`, #3): role A `{A, D, X, CD}`, roles T and F `{AD, X, CD}`,
  role M `{O/D, X, CD}`. The solver never assigns A/D (#15); CD is granted
  only against owed comp days.
- **Hard** (`constraints.py`): exactly one status per person and day; approved
  leave pinned off (X in the decision layer, the real AL/CD written back on
  save). Holidays are not pinned (#5). Also hard: `sum(CD) == 0` for anyone,
  of any role, who owes no comp days (`constraints_comp_days.py`).
- **Soft + slack** (always-feasible, decision #2), slack weight 10 000 unless noted:
  - `constraints_off_days.py` — 2 X per 7-day block (target += pinned leave, #4).
  - `constraints_rolling_rest.py` — ≥2 rest days in every rolling 7 days, across month ends (#7).
  - `constraints_consecutive.py` — ≤5 consecutive working days incl. the carried streak (§5.5).
  - `constraints_off_chain.py` — ≤5 consecutive OFF days, counting X and CD; annual leave exempt (#11, #34).
  - `constraints_staffing.py` — role-A floor per flight pairs: 1 pair → ≥1A+1D, 2 pairs → ≥1A+2D (§5.3 #4).
  - `constraints_role_a_distribution.py` — ≥2 pure A days per role-A person on a full month (#14).
  - `constraints_comp_days.py` — for anyone owing CDs, grant exactly the owed number; shortfall/excess slack weight 2 000, so a CD yields to flight cover (#13). With nothing owed the rule is the hard `sum(CD) == 0` above, not slack.
- **Objectives** (`objectives.WEIGHTS` + `objective_*`): per-person A≈D gap
  (300) > A/D balance across role A (100) > premium-off fairness (30) >
  adjacent off-pairing without weekend bias (15). Role A only for the balance terms.
- `slack_registry.py` collects slack vars → `Violation`s after solve.
- **Two-phase solve** (#45): phase 1 minimises the weighted slack alone with
  40 % of `SOLVER_MAX_TIME_SECONDS`; phase 2 bounds the slack by phase 1's
  result, starts from phase 1's plan and minimises slack + objectives with
  the remaining time. If phase 1 finds nothing in its share, one combined
  solve uses what is left. `SolverOutput.status` (`optimal` / `feasible` /
  …) and `slack_proven_minimal` tell whether the reported violations are
  proven unavoidable.
- **Not fully deterministic:** CP-SAT runs `SOLVER_NUM_WORKERS` workers
  (default 8) with `random_seed = 42`. The same input gives the same plan
  only with 1 worker and a solve that finishes inside the time limit; a run
  stopped by the limit depends on machine speed.
- Violations are not persisted. The generate response carries the solver's
  list; afterwards `schedule_violation_checker` re-runs every rule over the
  stored grid on demand (manual edit, shift change, leave decision,
  `GET /schedules/{id}/violations`). For a disabled user, cells before
  today (`business_today()`) stay ordinary cover; working cells from today
  on are flagged `disabled_user_duty` and not counted as cover (#44,
  ruling I2). Engine, re-check and
  month-close count the month boundary the same way: off-runs reach into the
  previous month (`prev_codes`), an off-run holding approved leave is exempt
  (#41), premium offs count only engine-chosen X (#42), comp consumption
  starts at `HOLIDAY_COMP_EFFECTIVE_FROM` (#43).

## Frontend (`attendance_scheduler_app/lib/`)
Feature-first clean architecture. `core/` (Dio client + JWT interceptor,
go_router with an auth guard and admin-only routes, secure token storage used
for session restore), `features/<x>/{data,domain,presentation}` (auth is the
template; flights/leaves/schedule/attendance/reports/users follow it),
`design_system/` (reusable `Ds*View` widgets), `i18n/` (custom en/vi,
graceful `text(key)` fallback). Admin-only actions are hidden for other roles
(#38); employees get their own attendance view and shift-change requests (#37).
Admins see the month's rule violations and confirm before publishing (#46).
Logout and session expiry reset every user-scoped provider, and a 403 that
`GET /users/me` confirms ends the session (#56). Every error message goes
through `core/network/api_error_message.dart` (`apiErrorMessage`): no
response → "server unavailable", 5xx → a translated generic message (never
the server's text), other errors → the backend's translated `detail`.

## Compliance posture (§9 → `deployment-guide.md`)
EU/Frankfurt region; sick `S` is special-category (admin-written into actual attendance only, never in the planned schedule, no
medical detail, audited); RBAC; fail-loud audit log on admin actions; rule-based engine
(no AI staff evaluation, §9.6). Final legal sign-off: customer DPO.
