# Project Changelog

## 2026-11-07 — Review remediation (owner decisions 2026-11-06)

Fixes the findings of the 2026-11-06 full-project review (B1–B10, C1–C11) and
implements the owner's decisions D1 and D4. D5/D8 keep the code as it was;
D6 and D7 stay open. Decisions #24–#38 and the customer notes are in
`design-decisions.md`.

### Scheduling
- Holidays stay working days; working one earns +1 CD for **every role**
  from `HOLIDAY_COMP_EFFECTIVE_FROM` (default 2026-11-06). CD is now in the
  T/F/M solver domains; self-arrange cannot set CD (decisions #5, #13).
- Regenerating a published or hand-edited month returns 409 unless `force`;
  the client asks before forcing (#24).
- Carry values (comp days, streak, premium offs) come from one source,
  `schedule_history`, for the engine, re-check, leave-conflict ranking and
  month-close; the stored streak is used only for users with no history (#29).
- The ≤5-consecutive-OFF rule in the engine counts CD as well as X (#34).
- Autorun runs at 00:05 in `TIMEZONE` on day `AUTORUN_DAY + 1` (was 02:00 on
  day 20) and reads `business_today()`; `AUTORUN_DAY` is limited to 1–27 (#9, #31).

### Leave
- A `leave_type` that disagrees with the span is refused (422) (#26).
- Approving writes AL into already-generated months; revoking returns to X
  only the cells still on AL (#28).
- Annual leave quota per user (migration `0008` adds `annual_leave_quota`,
  drops `annual_leave_balance`; default `ANNUAL_LEAVE_DEFAULT_DAYS` = 30,
  placeholder); `GET /leaves/balance`; approving past the quota only warns (#30).
- `GET /leaves/window` exposes the live registration window; the window-closed
  error names the real last day (#31, #32).

### Attendance
- Override, shift change, self-arrange and leave decisions on a published month
  update still-seeded actuals; re-publish re-syncs them (#27).
- Recently-sick forced cover looks back 30 days across month boundaries (#35).

### Accounts / security
- Self-registration has no role: pending accounts get T and the admin assigns
  the role at approval, which works only on pending accounts (#25).
- `GET /users/directory` lists active users' id, code and role for any signed-in
  user (#32).
- `reset_all_passwords.py` and `seed_demo_users.py` refuse to run outside
  `ENVIRONMENT=dev` unless `--allow-non-dev` (#33).

### UI (Flutter)
- Session restore at start-up; the token is kept when the server is
  unreachable (#36).
- Employees: own attendance view, shift-change requests from their own roster
  cells with a requests panel, colleagues shown by code, live leave window,
  comp days and annual leave left (#37).
- Admin-only actions (Generate/Publish, cell edits, holidays, attendance
  update, month-close) hidden for other roles; the cell editor offers only the
  role's planned codes, never S (#38).
- Admins set the annual leave quota on create and edit it on the Users page.
- Hard-coded English strings moved to the en/vi catalogs.

### Quality gates
- Backend: 239 pytest tests pass (was 188), `ruff check app tests scripts` and
  `mypy app` clean.
- Flutter: `flutter analyze` no issues; `flutter test` 60 tests pass,
  including the 3 goldens refreshed for the signed-out roster (no
  Generate/Publish, neutral "not published yet" message);
  `test/failures/` removed from git and ignored.

### Docs
- `design-decisions.md` (#3/#5/#9/#10/#13 amended, #24–#38 added, open questions
  rewritten), README status, codebase summary, system architecture, code
  standards (fail-loud audit, business dates), `DESIGN/README.md` (which design
  docs apply to this app).

## 2026-09-03 — Review remediation (Codex + Claude audit)

Closes every code-fixable finding of the 2026-09-03 review; customer-side
questions are listed in `design-decisions.md` → "Open questions".

### Security / bootstrap
- `ENVIRONMENT=staging|prod` refuses to start with the dev `SECRET_KEY` or
  `FIRST_ADMIN_PASSWORD`; seed-admin password reset is now dev-only
  (`FIRST_ADMIN_RESET_ON_STARTUP`). Docker image defaults to prod and runs
  `alembic upgrade head` before serving. CORS credentials disabled for `*`.
- Flutter login pre-fill only in debug builds; unauthenticated routes redirect
  to `/login`; a 401 on any call clears the session and returns to login.

### GDPR (§9.1 / §9.3 / §9.5)
- Sickness `S` rejected in the planned schedule (override, shift-change,
  self-arrange); legacy S of another user masked as X for non-admin readers;
  S attendance rows never keep a note.
- Audit is fail-loud (HTTP 500 on write failure) and now also covers user
  create/update/delete, account approval, manual flight-day / flight entry,
  month-close and the autorun (system actor).
- New `POST /compliance/retention/purge` (config `DATA_RETENTION_MONTHS`,
  floor 24) and `GET /compliance/users/{id}/export`.
- Deployment guide documents the out-of-spec time clock / self-arrange
  features for the DPO / Betriebsrat review, backup/restore and CI.

### Scheduling
- F-09 recheck now mirrors all engine rules (≥2 A days, comp-day grant/excess,
  ≤5 consecutive off).
- `carry_premium_off` derived from effective history (no month-close needed).
- Leave-conflict ranking applies all three §5.4 #9 criteria.
- Weekend-pairing override (owner 2026-06-18/07-01) recorded as decision #16.

### UI
- Excel import button on the Flights page (admin) wired to `POST /flights/import`.
- Close-month action on the Attendance page (admin) with a per-user carry
  summary dialog.

### Quality gates
- ruff 71 → 0, mypy 54 → 0 (OR-Tools calls moved to the snake_case API,
  `python_version = 3.12`), Flutter analyzer 59 → 0 (users-page fixes +
  `packages/**` excluded), goldens regenerated, `test/failures/` removed.
- `/health` checks the database and returns 503 when it is unreachable.
- `.github/workflows/ci.yml`: backend on SQLite + PostgreSQL, guard smoke,
  Flutter analyze/test, Windows release build artifact.
- `scripts/backup_db.sh`, `scripts/restore_db.sh`.

## 2026-07-25 — Navigation, attendance scroll, flights import, and leave split

### Fixed
- **Flight Presets page navigation freeze**: moved `/flights/presets` into the
  ShellRoute so the side menu stays usable instead of opening as a full-screen
  overlay.
- **Attendance horizontal scroll**: froze the employee name + role columns on
  the left and made the day/summary area scrollable, keeping header and data
  rows aligned.

### Changed
- **Flights page**: removed the "Import Excel" button (monthly Excel import is
  still available via the dedicated import flow).
- **Leave registration**: split the single "Đăng ký nghỉ" action into two
  distinct buttons — "Đăng ký nghỉ tháng" and "Đăng ký nghỉ phép năm". The
  selected type is now sent to the backend as `leave_type`, and the backend
  honors it when provided; otherwise it still falls back to span-based
  classification.

### Design-system alignment
- Flight preset / batch dialogs, role-change confirm dialog, and leave form
  now use `DsFormDialog`, `DsTextField`, `DsTextAction`, `DsPrimaryButton`,
  `DsSecondaryButton`, `DsSurface`, and `DsGridCell` instead of raw Material
  widgets.

## 2026-06-17 — Demo user seed tool

- Added a small backend CLI tool to seed 10 deterministic active demo users.
- Usernames are `nguyenvana` through `nguyenvanj`; roles are split as 4 `T`
  users and 6 `A` users.
- The seed is idempotent: reruns skip usernames that already exist.

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
