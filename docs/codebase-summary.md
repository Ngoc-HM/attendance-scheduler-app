# Codebase Summary

Monorepo: FastAPI backend + Flutter desktop client. Spec: `PROJECT_OVERVIEW.md`.

## Backend (`backend/app/`)
```
core/        config, database, security (JWT/bcrypt), i18n (en/vi), bootstrap,
             business_time (business_today() in TIMEZONE), script_guard
             (maintenance scripts: dev + local database only)
models/      User, RoleCodeCounter, Flight/FlightDay/FlightPreset, LeaveRequest,
             ShiftChangeRequest, SelfArrangeRequest, MonthlySchedule/ShiftAssignment,
             AttendanceRecord, TimeClockEntry, Holiday, AuditLog, enums
schemas/     Pydantic DTOs per domain (the API contract)
api/v1/      endpoints/ (auth, users, flights, leaves, shift_changes, self_arrange,
             schedules, attendance, time_clock, holidays, calculations, reports,
             compliance) + router + deps; api/params.py (bounded year/month
             parameters → 422)
services/    auth, user, flight (+flight_pair_derivation, flight_excel_parser),
             leave (+leave_windows, leave_balance, leave_conflict_resolver),
             shift_change, self_arrange, schedule (+schedule_input_builder,
             schedule_history, schedule_violation_checker, schedule_autorun),
             role_code_validation, attendance (+sick_backfill), time_clock,
             holiday, calculation (+carry_over_math), report (+report_table,
             report_serializers), compliance, audit, demo_user_seed
scheduler/   domain (SolverInput/Output), engine (CP-SAT), role_codes (per-role
             domains), constraints + constraints_off_days / _rolling_rest /
             _consecutive / _off_chain / _staffing / _comp_days /
             _role_a_distribution, objectives + objective_balance /
             _premium_off / _off_pairing, slack_registry, calendar_utils
alembic/     0001 baseline … 0009 flight_unique_day_number (head; see
             design-decisions "Migration strategy")
scripts/     seed_demo_users.py, reset_all_passwords.py (both refuse unless
             ENVIRONMENT=dev and the database is local, app/core/script_guard.py;
             --allow-non-dev overrides; hidden password prompt)
tests/       479 tests (pytest on SQLite, foreign keys on) — engine rules
             (bind + slack violation), solve phases, engine/checker agreement,
             roles, cross-month rules, services, endpoints, input bounds,
             RBAC/audit, user delete, sick privacy, production guard, bootstrap,
             compliance, attendance sync, health
requirements.lock  every package pinned (CI, Docker and make install use -c)
```

New in the 2026-11 remediation: `core/business_time.py`,
`services/leave_balance.py` (quota / used / pending / remaining),
`schedule_service.apply_leave_span` (leave decisions into generated months),
`attendance_service.sync_planned_cell` (roster edits → seeded actuals; since
2026-11-08 on drafts too).

New in the 2026-11-08 review fixes: `api/params.py`,
`schedule_service.violations_for` + `GET /schedules/{id}/violations`,
`carry_over_math.comp_balance_from_counts` (R3), `schedule_history.BoundaryState.prev_codes`
/ `scheduler.domain.PersonInput.prev_codes` (off-runs across the month start),
`SolverOutput.status` / `slack_proven_minimal`, `SOLVER_NUM_WORKERS`,
migration `0009`, `backend/.dockerignore`; `attendance_service.sync_planned_cell`
now runs on every roster edit, draft or published (`follow_plan` is shared
with the regenerate resync); `schedule_autorun.maybe_draft_current_month`
(the current month is drafted when it has no schedule);
`bootstrap.warn_if_schema_outdated` (WARNING when the database is behind the
migration head); `schedule_violation_checker.recheck(..., cover_roles=)`
(past cells of disabled users still count as cover, ruling I2).

### Feature → code map (spec §4)
| Module | Features | Backend |
|--------|----------|---------|
| Accounts & auth | F-01..F-03 | `auth.py`, `users.py`, `auth_service`, `user_service` |
| Flight input | F-04 | `flights.py`, `flight_service` |
| Leave + swaps | F-05/06, #8 | `leaves.py`, `shift_changes.py`, `self_arrange.py`, `leave_service`, `leave_balance`, `shift_change_service`, `self_arrange_service` |
| **Auto-schedule** | F-07..F-09 | `scheduler/`, `schedules.py`, `schedule_service`, `schedule_history` |
| Attendance | F-10..F-13 | `attendance.py`, `time_clock.py`, `holidays.py`, `attendance_service`, `holiday_service` |
| Calculations | F-14 | `calculations.py`, `calculation_service` |
| Reports | F-15 | `reports.py`, `report_service` |
| Compliance | §9 | `compliance.py`, `compliance_service`, `audit_service` |

## Frontend (`attendance_scheduler_app/lib/`)
```
core/         config, network (Dio + JWT interceptor, ApiException,
              apiErrorMessage: the one error-message rule), router (go_router, auth
              guard + admin-only routes), storage (secure JWT, locale),
              constants (api_endpoints, shift_codes incl. plannedCodesFor(role)
              for the admin editor and requestableCodesFor(role) for requests),
              utils
design_system/ reusable Ds*View widgets (Schedule, Flights, Leaves, Attendance,
              Reports, Users) + dialogs, tokens, theme
features/<x>/ data/{datasources,models,repositories} · domain/{entities,
              repositories,usecases} (auth, schedule, attendance) ·
              presentation/{providers,pages,widgets}
              x ∈ auth, users, flights, leaves, schedule, attendance, reports, home
i18n/         custom AppLocalizations (en/vi, graceful text(key) fallback)
```
`auth` is the canonical clean-architecture template; the business features
mirror it, feeding live provider state into the `design_system` views.
Tests: `test/` — 136 tests including 3 goldens (`test/goldens/`, tagged
`golden` in `dart_test.yaml`; run them on macOS with `flutter test --tags
golden`, everything else with `--exclude-tags golden`); among them
`i18n_keys_used_exist_test.dart` (every key used in `lib/` exists).
`pubspec.lock` is tracked; CI runs `flutter pub get --enforce-lockfile`.

## Entry points
- Backend: `alembic upgrade head`, then `uvicorn app.main:app` (lifespan:
  environment guard → bootstrap (schema-revision warning, seed admin) →
  autorun: daily at 00:05 and once at startup, drafting the current month
  when it has no schedule and next month from day `AUTORUN_DAY + 1`).
- Frontend: `flutter run -d macos|windows|linux` (`API_BASE_URL` from
  `--dart-define`, else `.env`).
- `make dev` runs both.
