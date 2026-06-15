# Codebase Summary

Monorepo: FastAPI backend + Flutter desktop client. Spec: `PROJECT_OVERVIEW.md`.

## Backend (`backend/app/`)
```
core/        config, database, security (JWT/bcrypt), i18n (en/vi), bootstrap, RBAC deps
models/      User, Flight/FlightDay, LeaveRequest, ShiftChangeRequest,
             MonthlySchedule/ShiftAssignment, AttendanceRecord, Holiday, AuditLog, enums
schemas/     Pydantic DTOs per domain (the API contract)
api/v1/       endpoints/ (auth, users, flights, leaves, shift_changes, schedules,
             attendance, holidays, calculations, reports) + router + deps
services/    auth, user, flight (+flight_pair_derivation, flight_excel_parser),
             leave (+leave_windows, leave_conflict_resolver), shift_change,
             schedule (+schedule_input_builder, schedule_violation_checker,
             schedule_autorun), attendance (+sick_backfill), holiday,
             calculation (+carry_over_math), report (+report_table,
             report_serializers), audit
scheduler/   domain (SolverInput/Output), engine (CP-SAT), constraints +
             constraints_off_days/_consecutive/_staffing, objectives +
             objective_balance/_weekend/_premium_off, slack_registry, calendar_utils
alembic/     0001 baseline, 0002 carry_premium_off + shift_change_requests
tests/       99 tests — engine (off_days/consecutive/staffing/objectives/slack),
             services, endpoints, rbac_audit, calendar_utils, health
```

### Feature → code map (spec §4)
| Module | Features | Backend |
|--------|----------|---------|
| Accounts & auth | F-01..F-03 | `auth.py`, `users.py`, `auth_service`, `user_service` |
| Flight input | F-04 | `flights.py`, `flight_service` |
| Leave + swaps | F-05/06, #8 | `leaves.py`, `shift_changes.py`, `leave_service`, `shift_change_service` |
| **Auto-schedule** | F-07..F-09 | `scheduler/`, `schedules.py`, `schedule_service` |
| Attendance | F-10..F-13 | `attendance.py`, `holidays.py`, `attendance_service`, `holiday_service` |
| Calculations | F-14 | `calculations.py`, `calculation_service` |
| Reports | F-15 | `reports.py`, `report_service` |

## Frontend (`attendance_scheduler_app/lib/`)
```
core/         config, network (Dio + JWT interceptor), router (go_router),
              storage (secure JWT), constants (api_endpoints, shift_codes)
design_system/ reusable Ds*View widgets (Schedule, Flights, Leaves, Attendance,
              Reports, Users) + dialogs
features/<x>/ data/{datasources,models,repositories} · domain/{entities,
              repositories,usecases} · presentation/{providers,pages}
              x ∈ auth, users, flights, leaves, schedule, attendance, reports
i18n/         custom AppLocalizations (en/vi, graceful text(key) fallback)
```
`auth` is the canonical clean-architecture template; the business features
mirror it, feeding live provider state into the `design_system` views.

## Entry points
- Backend: `uvicorn app.main:app` (lifespan: bootstrap + day-20 autorun).
- Frontend: `flutter run -d macos|windows|linux` (`API_BASE_URL` from `.env`).
- `make dev` runs both.
