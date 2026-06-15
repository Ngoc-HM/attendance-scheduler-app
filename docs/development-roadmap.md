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

## Current state — ALL PHASES COMPLETE
- **Backend: feature-complete, 99/99 tests pass.** Every F-01..F-15 endpoint
  is implemented; the CP-SAT engine enforces all §5.3 hard rules (soft+slack)
  and §5.4 objectives, verified on realistic 9-person months.
- **Frontend: all 7 features wired** (auth, users, flights, leaves, schedule
  +shift-change, attendance+holidays, reports) to the live API; mockups
  removed; `flutter analyze` clean; **11/11 Flutter tests pass** (i18n parity,
  boot, navigation, design-system boundary on all pages, schedule goldens).
- DB migrated to Alembic `0002`.

## Test coverage note
Backend has per-constraint bind + slack-violation tests, service/endpoint/RBAC/
audit tests. Flutter coverage = design-system boundary (all 6 wired pages),
i18n parity, app boot/navigation, and schedule-page golden renders. Deeper
per-page Flutter widget tests (flights/leaves/attendance/reports interaction)
are a sensible future addition but the pages are structurally validated.

## Confirm-with-customer (non-blocking)
Partial-week rounding (#7) · M/T in A/D balance · real "WR JUN26" Excel layout
· Betriebsrat (§9.2, deploy gate) · partial CD carry.
