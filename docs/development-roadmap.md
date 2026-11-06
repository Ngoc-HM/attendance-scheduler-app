# Development Roadmap

Living status of the full-implementation plan
(`plans/260611-1941-full-implementation/`). Spec: `PROJECT_OVERVIEW.md`.

## Phases
| # | Phase | Features | Status |
|---|-------|----------|--------|
| 01 | Foundation (models, calendar, Alembic) | — | ✅ done |
| 02 | Flights CRUD + Excel import | F-04 | ✅ done |
| 03 | Leaves + shift-change requests | F-05/06, #8 | ✅ done |
| 04 | **Scheduler engine** (CP-SAT, §5) | F-07/08 core | ✅ done |
| 05 | Schedule service + day-20 autorun | F-07/08/09, #9 | ✅ done |
| 06 | Attendance, sick backfill, holidays | F-10/11/12/13 | ✅ done |
| 07 | Calculations (carry comp/streak/premium) | F-14 | ✅ done |
| 08 | Reports (monthly/yearly export) | F-15 | ✅ done |
| 09 | Flutter wiring (5 pages → real API) | all UI | ✅ done |
| 10 | GDPR hardening (RBAC, audit, sick) | §9 | ✅ done |
| 11 | Testing | — | ✅ done (110 tests green) |
| 12 | Docs | — | ✅ done |

## Current state — 2026-09-03 hardening pass
- **Backend:** F-01..F-15 implemented; 188 tests, `ruff` and `mypy` clean.
  Production environment guard, dev-only seed-admin reset, sickness never in
  the planned schedule (write-reject + read-mask), no note on S rows,
  fail-loud audit covering user CRUD / approval / manual flight entry /
  month-close / autorun, F-09 recheck mirroring every engine rule,
  premium-off carry derived from history, 3-criteria leave-conflict ranking,
  retention purge + data-subject export, DB-backed `/health`.
- **Frontend:** every screen wired; Excel import and month-close in the UI;
  auth guard on all routes; 401 → session expired → login; release builds
  start with an empty login form. `flutter analyze` clean, 18/18 tests.
- **CI:** `.github/workflows/ci.yml` — ruff, mypy, pytest on SQLite and on
  PostgreSQL 16 (with a fresh `alembic upgrade head`), production-guard
  smoke, `flutter analyze`/`test`, `flutter build windows` artifact.
- DB at Alembic `0007`.

## Remaining before production
| Item | Owner | Notes |
|------|-------|-------|
| Betriebsrat agreement (§9.2) | customer | now also covers time clock + self-arrange |
| Staffing floor vs exact count | customer | see design-decisions "Open questions" |
| Real "WR JUN26" Excel layout | customer | importer expects date / flt / route / STA / STD |
| Final retention period | customer DPO | shipped 36 months, floor 24 |
| Windows build smoke-tested on a customer PC | dev | CI produces the bundle; install + login + generate |
| PostgreSQL restore rehearsal on staging | dev/ops | `scripts/backup_db.sh` + `scripts/restore_db.sh` |
| Audit row in the same transaction as the change | dev (nice-to-have) | currently fail-loud after commit, see decision #18 |

## Test coverage note
Backend has per-constraint bind + slack-violation tests, service/endpoint/RBAC/
audit tests, privacy (S) tests, production-guard tests, recheck-rule tests and
compliance tests. Flutter coverage = design-system boundary (all wired pages),
i18n parity, app boot/navigation, users-page guards, and schedule-page golden
renders. Deeper per-page Flutter widget tests (flights/leaves/attendance/
reports interaction) remain a sensible future addition.
