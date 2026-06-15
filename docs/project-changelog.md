# Project Changelog

## 2026-06-11 — Full backend implementation (F-01..F-15) + GDPR

Brought the app from "scaffold + auth only" to a feature-complete, tested
backend. Spec: `PROJECT_OVERVIEW.md`; decisions: `design-decisions.md`.

### Added — scheduling engine (§5, the core feature)
- OR-Tools CP-SAT engine with an **always-feasible slack architecture**: hard
  rules = exactly-one-status + approved-off pins; soft+slack = 2-X-per-7-day-
  block, ≤5 consecutive working days (incl. cross-month `carry_streak`), and
  A1–A4 staffing per `flight_pairs` (A/D covers one A + one D, §5.3 #6).
- Objectives: balance A/D (top weight), premium-off fairness, weekend pairing.
- `slack > 0` is reported as `Violation`s (§5.6) — no silent infeasibility.
- Modularized: `constraints_*`, `objective_*`, `slack_registry` (<200 LOC each).

### Added — domain features
- F-04 Flights: CRUD + Excel import (openpyxl) → `flight_pairs`.
- F-05/06 Leaves: registration windows (days 1–20 of M for M+1; annual
  prior-year), approve/reject, conflict ranking, annual-balance tracking.
- Shift-change requests (decision #8): change-code / swap, admin-decided,
  re-checked against hard rules.
- F-07/08/09 Schedule service: generate → draft, manual override (save +
  warn), publish; non-admins see published only.
- Day-20 autorun (APScheduler) generates next month's draft (decision #9).
- F-10/11/12/13 Attendance: actual records, sick (S) A/D backfill (recently-
  sick forced, §6), holiday CRUD (working-day markers, decision #5).
- F-14 Calculations: idempotent carry of comp days / streak / premium-off.
- F-15 Reports: pluggable CSV/XLSX export of monthly & yearly attendance.

### Added — compliance (§9) & infra
- RBAC (`AdminUser`, `ensure_self_or_admin`), `/attendance/me` self-service.
- Sick `S` is admin-only (special-category, §9.1); audit log on every admin
  mutation; EU-region + no-AI config flags (§9.4/§9.6).
- Alembic migrations (`0001` baseline, `0002` carry_premium_off + shift
  changes); `create_all` demoted to fresh-DB convenience.

### Tests
- 99 backend tests (pytest/SQLite): per-constraint bind + slack-violation
  pairs, services, endpoints, RBAC/audit. All passing.

### Spec overrides (owner-approved — see design-decisions.md)
- Holidays are working days (not auto-off) — overrides F-13/§7.
- Week = 7-day blocks from day 1 (not Mon–Sun).

### In progress
- Flutter UI wiring (flights/leaves/schedule/attendance/reports) and widget
  tests; final docs.
