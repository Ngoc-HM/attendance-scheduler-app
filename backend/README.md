# Backend — Attendance & Auto-Scheduler API

FastAPI service holding the business logic and the OR-Tools scheduling engine
(spec sections 4 & 5).

## Stack
- **FastAPI** (REST API) · **SQLAlchemy 2.0** + **Alembic** (PostgreSQL)
- **OR-Tools CP-SAT** (constraint-solver scheduling engine)
- **JWT** auth (lightweight, spec §2) · **Pydantic v2** schemas
- **APScheduler** (monthly autorun inside the API process)

## Layout
```
app/
├── main.py            # FastAPI app: env guard → bootstrap → autorun; CORS, /health, app logging
├── core/              # config, database, security (JWT/bcrypt), i18n (en/vi),
│                      #   bootstrap, business_time, script_guard
├── models/            # SQLAlchemy ORM + enums (roles §3, attendance codes §7)
├── schemas/           # Pydantic request/response DTOs
├── api/
│   ├── deps.py        # get_db, current user, require_admin
│   ├── params.py      # bounded year/month query + path parameters (422 on bad input)
│   └── v1/endpoints/  # auth, users, flights, leaves, shift_changes, self_arrange,
│                      #   schedules, attendance, time_clock, holidays,
│                      #   calculations, reports, compliance
├── services/          # business logic (one module per domain + focused helpers)
└── scheduler/         # OR-Tools engine — the core feature (§5)
    ├── domain.py          # SolverInput / SolverOutput (§5.1, §5.2)
    ├── calendar_utils.py  # week partition (§5.1), streak (§5.5)
    ├── role_codes.py      # per-role code domains
    ├── constraints*.py    # hard constraints + one module per soft rule (§5.3)
    ├── objective*.py      # soft objectives (§5.4)
    ├── slack_registry.py  # slack vars → violations (§5.6)
    └── engine.py          # build + two-phase CP-SAT solve
alembic/               # database migrations (head 0011)
scripts/               # seed_demo_users.py, reset_all_passwords.py (local dev DB only)
tests/                 # pytest
```

## Feature → file map
| Feature | Where |
| --- | --- |
| F-01/02/03 Accounts & auth | `api/.../auth.py`, `users.py` · `services/auth_service.py`, `user_service.py` |
| F-04 Flight import (manual + Excel) | `api/.../flights.py` · `services/flight_service.py`, `flight_excel_parser.py` |
| F-05/06 Leave registration | `api/.../leaves.py` · `services/leave_service.py`, `leave_windows.py`, `leave_balance.py` |
| Shift-change requests (#8) | `api/.../shift_changes.py` · `services/shift_change_service.py` |
| F-07/08/09 Auto-schedule + balance + manual edit + rule check | `api/.../schedules.py` · `services/schedule_service.py`, `schedule_autorun.py` · `scheduler/` |
| F-10/11/12 Attendance & sick cover | `api/.../attendance.py` · `services/attendance_service.py`, `sick_backfill.py` |
| F-13 Holidays | `api/.../holidays.py` · `services/holiday_service.py` |
| F-14 Carry-over / comp days | `api/.../calculations.py` · `services/calculation_service.py`, `carry_over_math.py` |
| F-15 Reports/export | `api/.../reports.py` · `services/report_service.py`, `report_serializers.py` |
| Compliance (§9.3 / §9.5) | `api/.../compliance.py` · `services/compliance_service.py`, `audit_service.py` — retention purge, data-subject export |
| Time clock / self-arrange (owner 2026-07-09) | `api/.../time_clock.py`, `self_arrange.py` · `services/time_clock_service.py`, `self_arrange_service.py` |

All endpoints are implemented. Startup runs the environment guard
(`Settings.validate_for_environment`) before bootstrap: a staging or prod
process refuses to start with the dev or `.env.example` placeholder
`SECRET_KEY`, the dev `FIRST_ADMIN_PASSWORD`, a
SQLite or default `DATABASE_URL`, `BACKEND_CORS_ORIGINS=*`,
`AUTO_CREATE_TABLES=true` or a retention below 24 months
(`docs/deployment-guide.md`).

## Run locally
```bash
cd backend
python -m venv .venv && .venv\Scripts\activate      # Windows (macOS/Linux: source .venv/bin/activate)
pip install -r requirements-dev.txt -c requirements.lock
copy .env.example .env                               # then edit secrets (cp on macOS/Linux)

# With Docker (Postgres + API; the API migrates before it starts):
docker compose up --build

# Or run the API directly (needs a reachable PostgreSQL):
alembic upgrade head                                 # before every start of new code
uvicorn app.main:app --reload --port 8035
```
Docs (dev only): http://localhost:8035/docs · Health: http://localhost:8035/health (503 when the DB is unreachable)

`AUTO_CREATE_TABLES=true` only builds a brand-new database. Once the database
has an `alembic_version` table it is ignored (a warning is logged) and new
columns or constraints arrive only through `alembic upgrade head`. Startup
also logs a WARNING naming both revisions when such a database is behind the
code's migration head (startup continues; the API may fail on missing
columns until you migrate).

With `AUTORUN_ENABLED=true` (the default) every start and the daily 00:05
check draft the current month when it has no schedule, and next month from
the day after `AUTORUN_DAY`; a fresh database therefore gets a draft of the
current month at its first start. Set `AUTORUN_ENABLED=false` for a local
backend pointed at a shared database.

`requirements.lock` pins every package (direct and transitive) to the
versions CI tests; the Dockerfile, CI and `make install` at the repository
root all install with `-c requirements.lock`.

### Seed demo users
```bash
python scripts/seed_demo_users.py                    # prompts for the password twice, hidden
```
This creates 10 active demo users with usernames `nguyenvana` through
`nguyenvanj`: `a`, `b` role T; `c`, `d` role F; `e`–`j` role A
(`app/services/demo_user_seed.py`). There is no default password: the script
prompts for one, or takes `--password` for non-interactive use (it then stays
in the shell history). Re-running the tool skips existing usernames.

### Maintenance scripts are local-only
`scripts/seed_demo_users.py` and `scripts/reset_all_passwords.py` load
`backend/.env` by its absolute path and run only when `ENVIRONMENT=dev`
**and** `DATABASE_URL` points at a local database (SQLite, or host
`localhost` / `127.0.0.1` / `::1`; a `host`, `hostaddr` or `service` query
parameter makes it non-local). Anything else — a staging/prod environment, or
a dev `.env` that points at a shared or remote PostgreSQL such as the
Tailscale one — exits with code 2 and prints the environment and database host
(never the password). Pass `--allow-non-dev` only when you really mean to
touch that database.

```bash
# Every user's password becomes the one you type (hidden prompt, asked twice).
python scripts/reset_all_passwords.py
# or non-interactively:
python scripts/reset_all_passwords.py --password 'a-local-test-password'
```

## Test & lint
```bash
pytest                    # 479 tests on a throw-away SQLite database
ruff check app tests
mypy app
```
`tests/conftest.py` builds a temporary SQLite database with foreign keys
enforced. A `DATABASE_URL` already set in the environment is used only when it
is local (CI's PostgreSQL on localhost); any other URL stops the run before it
connects. Because the URL is set in the environment before the app is
imported, the `DATABASE_URL` in `backend/.env` is never used by the tests.

## Compliance (spec §9 — GDPR/BDSG)
- Deploy DB + API in an **EU/Frankfurt** region; sign a DPA with the provider.
- Sick data (`S`) is special-category — written by admins into actual attendance only,
  never with a note, never in the planned schedule; visible to admins and the person themself.
- TLS in transit, encryption at rest, role-based access, fail-loud audit log (`models/audit.py`).
- Retention purge (`DATA_RETENTION_MONTHS`, floor 24) and per-person data export under `/compliance`.
- Scheduling is **rule-based** (no AI performance evaluation — EU AI Act note §9.6).
