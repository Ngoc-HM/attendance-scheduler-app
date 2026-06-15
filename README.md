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

## Status
**Backend: feature-complete & tested — F-01..F-15 all implemented (99/99 tests).**
The OR-Tools CP-SAT engine enforces every §5.3 hard rule (via an always-feasible
slack model that reports violations instead of failing — §5.6) and the §5.4
objectives (A/D balance, weekend pairing, cross-month premium-off fairness).
Schedule generate / manual-override / publish, day-20 autorun, leave +
shift-change requests, attendance with sick A/D backfill, holiday CRUD,
month-close calculations, and CSV/XLSX export are all live. GDPR hardening is in
place (RBAC, audit log on every admin mutation, sick `S` admin-only). Schema is
managed by Alembic (`alembic upgrade head`).

**Frontend:** auth + user management wired; the flights / leaves / schedule /
attendance / reports screens are being wired to the live API (replacing the
earlier mockups). See `docs/development-roadmap.md` for current phase status.

> **Spec overrides** (owner-approved — see `docs/design-decisions.md`):
> holidays are **working days** (not auto-off, diverges from F-13/§7); a "week"
> for the 2-days-off rule is a **7-day block from day 1** (not Mon–Sun).

## Documentation
Full docs live in [`docs/`](./docs): architecture, design decisions (incl. spec
overrides), code standards, deployment/GDPR guide, roadmap, changelog,
codebase summary.

## Compliance (spec §9 — GDPR / BDSG)
Deploy in an EU/Frankfurt region; sick data (`S`) is special-category
(admin-only, no medical detail); TLS + encryption at rest; role-based access;
audit log on admin actions; rule-based scheduling (no AI performance
evaluation, §9.6). Details: [`docs/deployment-guide.md`](./docs/deployment-guide.md).
Final legal sign-off rests with the customer's DPO. **Open question:** does the
customer have a Betriebsrat (works council)? If so, an agreement is needed
before rollout.
