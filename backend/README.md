# Backend — Attendance & Auto-Scheduler API

FastAPI service holding the business logic and the OR-Tools scheduling engine
(spec sections 4 & 5).

## Stack
- **FastAPI** (REST API) · **SQLAlchemy 2.0** + **Alembic** (PostgreSQL)
- **OR-Tools CP-SAT** (constraint-solver scheduling engine)
- **JWT** auth (lightweight, spec §2) · **Pydantic v2** schemas

## Layout
```
app/
├── main.py            # FastAPI app + CORS + health
├── core/              # config, database, security (JWT/bcrypt), i18n (en/vi)
├── models/            # SQLAlchemy ORM + enums (roles §3, attendance codes §7)
├── schemas/           # Pydantic request/response DTOs
├── api/
│   ├── deps.py        # get_db, current user, require_admin
│   └── v1/endpoints/  # auth, users, flights, leaves, schedules,
│                      #   attendance, holidays, calculations, reports
├── services/          # business logic (one module per domain)
└── scheduler/         # OR-Tools engine — the core feature (§5)
    ├── domain.py          # SolverInput / SolverOutput (§5.1, §5.2)
    ├── calendar_utils.py  # week partition (§5.1), streak (§5.5)
    ├── constraints.py     # hard constraints (§5.3)
    ├── objectives.py      # soft objectives (§5.4)
    └── engine.py          # build + solve the CP-SAT model
alembic/               # database migrations
tests/                 # pytest
```

## Feature → file map
| Feature | Where |
| --- | --- |
| F-01/02/03 Accounts & auth | `api/.../auth.py`, `users.py` · `services/auth_service.py`, `user_service.py` |
| F-04 Flight import (manual + Excel) | `api/.../flights.py` · `services/flight_service.py` |
| F-05/06 Leave registration | `api/.../leaves.py` · `services/leave_service.py` |
| F-07/08/09 Auto-schedule + balance + manual edit | `api/.../schedules.py` · `services/schedule_service.py` · `scheduler/` |
| F-10/11/12 Attendance & sick cover | `api/.../attendance.py` · `services/attendance_service.py` |
| F-13 Holidays | `api/.../holidays.py` · `services/holiday_service.py` |
| F-14 Carry-over / comp days | `api/.../calculations.py` · `services/calculation_service.py` |
| F-15 Reports/export | `api/.../reports.py` · `services/report_service.py` |

> Endpoints and services are scaffolded with final signatures; handlers return
> `501 Not Implemented` and services raise `NotImplementedError` with TODOs
> pointing at the exact spec rule. The calendar helpers and the engine wiring
> (one-status-per-day, respect-approved-off) are implemented and covered by tests.

## Run locally
```bash
cd backend
python -m venv .venv && .venv\Scripts\activate      # Windows
pip install -r requirements-dev.txt
copy .env.example .env                               # then edit secrets

# With Docker (Postgres + API):
docker compose up --build

# Or run the API directly (needs a reachable PostgreSQL):
alembic revision --autogenerate -m "init"   # once models are final
alembic upgrade head
uvicorn app.main:app --reload
```
Docs: http://localhost:8000/docs · Health: http://localhost:8000/health

## Test & lint
```bash
pytest
ruff check .
mypy app
```

## Compliance (spec §9 — GDPR/BDSG)
- Deploy DB + API in an **EU/Frankfurt** region; sign a DPA with the provider.
- Sick data (`S`) is special-category — admin-only visibility, no medical detail stored.
- TLS in transit, encryption at rest, role-based access, audit log (`models/audit.py`).
- Scheduling is **rule-based** (no AI performance evaluation — EU AI Act note §9.6).
