# Attendance & Auto-Scheduler

Automatic shift-scheduling and attendance system for airline ground personnel
in Frankfurt (spec: [`PROJECT_OVERVIEW.md`](./PROJECT_OVERVIEW.md)). The core
feature is **automatic schedule generation** (constraint solver), not just
time tracking.

## Monorepo layout
```
attendance-scheduler-app/
├── backend/                     # FastAPI + OR-Tools + PostgreSQL (REST API + engine)
│   └── app/{core,models,schemas,api,services,scheduler}
├── attendance_scheduler_app/    # Flutter desktop (Windows) client
│   └── lib/{core,features,shared,l10n}
├── PROJECT_OVERVIEW.md          # Full requirements (sections 1–9 + Appendix A)
└── README.md
```

## Architecture
```
Flutter (Windows desktop)  ──HTTPS/JWT──►  FastAPI  ──►  PostgreSQL (EU/Frankfurt)
        feature-first /                     layered:        shared by all clients
        clean architecture            api → services → models
                                              └► scheduler/ (OR-Tools CP-SAT, §5)
```

### Backend (`backend/`) — layered
- `core/` config, database, security (JWT/bcrypt), i18n (en/vi)
- `models/` SQLAlchemy ORM + enums (roles §3, attendance codes §7)
- `schemas/` Pydantic DTOs (API contract)
- `api/v1/endpoints/` thin HTTP handlers
- `services/` business logic (one module per domain)
- `scheduler/` the OR-Tools engine — hard constraints (§5.3), soft objectives (§5.4)

### Frontend (`attendance_scheduler_app/lib/`) — feature-first
- `core/` config, network (Dio), router (go_router), theme, secure storage
- `features/<x>/{data,domain,presentation}` — `auth` is the full template;
  `schedule`, `flights`, `leaves`, `attendance`, `reports`, `users` follow it
- `shared/` reusable widgets · `i18n/` English + Vietnamese strings (custom `AppLocalizations`, no codegen)

## Feature map (spec §4)
| Module | Features | Backend | Frontend |
| --- | --- | --- | --- |
| Accounts & auth | F-01..F-03 | `api/.../auth.py`, `users.py` | `features/auth`, `features/users` |
| Flight input | F-04 | `api/.../flights.py` | `features/flights` |
| Leave | F-05, F-06 | `api/.../leaves.py` | `features/leaves` |
| **Auto-schedule** | F-07..F-09 | `scheduler/`, `schedules.py` | `features/schedule` |
| Attendance | F-10..F-13 | `attendance.py`, `holidays.py` | `features/attendance` |
| Calculations | F-14 | `calculations.py` | (reports/schedule) |
| Reports/export | F-15 | `reports.py` | `features/reports` |

## Getting started
**Quick start (both at once):**
```bash
make install      # backend venv + deps, flutter pub get   (first time)
make dev          # runs backend on :8035 + Flutter desktop; Ctrl-C stops both
```
`make dev` auto-detects the desktop device (macOS/Linux/Windows); override with
`make dev DEVICE=windows`. See `make help` for individual targets.

**Backend only** (see [`backend/README.md`](./backend/README.md)):
```bash
cd backend
python -m venv .venv && .venv\Scripts\activate   # (Windows) or: source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env              # set DATABASE_URL etc. (DB + tables auto-created on startup)
uvicorn app.main:app --reload --port 8035
# or the full stack: docker compose up --build
```
**Frontend only** (desktop): the API base URL comes from
`attendance_scheduler_app/.env` (`API_BASE_URL`, default `http://localhost:8035/api/v1`).
```bash
cd attendance_scheduler_app
flutter pub get
flutter run -d macos            # or windows / linux
```

## Status (2026-11-07)
**Backend: F-01..F-15 implemented; 239 pytest tests pass, ruff and mypy
clean; Alembic head `0008`.**
The OR-Tools CP-SAT engine enforces every §5.3 rule through an always-feasible
slack model that reports violations instead of failing (§5.6), plus the §5.4
objectives (A/D balance, adjacent off-pairing, cross-month premium-off
fairness). Schedule generate (409 guard on published or hand-edited months) /
manual override (re-checked against every engine rule) / publish, the monthly
autorun (00:05 on the day after the leave window closes, day 21 by default),
leave + shift-change + self-arrange requests, leave decisions written straight
into an already-generated schedule, annual-leave quota and remaining balance,
holiday work earning a comp day for every role, attendance with sick A/D
backfill and seeded actuals that follow published edits, holiday CRUD, time
clock, month-close, CSV/XLSX export, retention purge and data-subject export
are live. Schema is managed by Alembic (`alembic upgrade head`).

**Frontend:** all screens are wired to the live API, including Excel flight
import, month-close, session restore on start-up, session-expiry handling and
an auth guard on every route. Employees get their own attendance view,
shift-change requests from their own roster cells, colleagues shown by code,
the live leave window and their annual leave left; admin-only actions are
hidden for everyone else. `flutter analyze` reports no issues; `flutter test`
passes 60 tests, including the 3 golden images.

**Not yet done / needs the customer** (details in `docs/design-decisions.md`,
"Open questions"): weekend preference for paired offs (D6, undecided), staffing
exact vs minimum and what the extra role-A person does (D7), the real
annual-leave quota (30 days is a placeholder), Betriebsrat agreement (now also
covering the time clock), the customer notes from the 2026-11 remediation,
real "WR JUN26" Excel layout, final retention period, a rehearsed PostgreSQL
restore, and a Windows build produced by the CI job
(`.github/workflows/ci.yml`) and smoke-tested on a customer machine.
Treat the current state as **release candidate for internal pilot**, not as
a production release.

> **Spec overrides** (owner-approved — see `docs/design-decisions.md`):
> holidays are **working days** (not auto-off, diverges from F-13/§7) and
> working one earns **+1 comp day (CD)** next month for every role; a "week"
> for the 2-days-off rule is a **7-day block from day 1** (not Mon–Sun); the
> engine pairs weekly offs **adjacently without a weekend preference** (the
> T7+CN > T6+T7 > CN+T2 order applies only to leave-conflict ranking; D6 is
> still open).

## Documentation
Full docs live in [`docs/`](./docs): architecture, design decisions (incl. spec
overrides), code standards, deployment/GDPR guide, roadmap, changelog,
codebase summary.

## Compliance (spec §9 — GDPR / BDSG)
Deploy in an EU/Frankfurt region; sick data (`S`) is special-category: written
by admins only into actual attendance, never with a note, never in the planned
schedule, visible only to admins and the person themself. TLS + encryption at
rest; role-based access; fail-loud audit log on every admin action; retention
purge with a 24-month legal floor; per-person data export; production
environment guard; rule-based scheduling (no AI performance evaluation, §9.6).
Details: [`docs/deployment-guide.md`](./docs/deployment-guide.md).
Final legal sign-off rests with the customer's DPO. **Open question:** does the
customer have a Betriebsrat (works council)? If so, an agreement is needed
before rollout — and the time-clock feature makes that question unavoidable.
