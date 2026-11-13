# Deployment Guide (EU / GDPR)

Deploying personnel data in Germany (Frankfurt) → GDPR (EU) + BDSG (federal).
This guide records the §9 controls for the customer's DPO sign-off and how the
backend runs today. Legal responsibility rests with the customer.

## The current setup (2026-11-08)
What actually runs today, as opposed to the target production layout below:

- **Backend:** the FastAPI process runs on the owner's workstation with
  `ENVIRONMENT=dev`, reading `backend/.env`.
- **Database:** one shared PostgreSQL reached over **Tailscale** (the
  `DATABASE_URL` host is a tailnet address). Traffic between tailnet nodes is
  encrypted by WireGuard; the database must not be exposed outside the
  tailnet.
- **Clients:** the Flutter desktop app points at the backend through
  `API_BASE_URL` (bundled `.env`, or `--dart-define=API_BASE_URL=...`, which
  wins, decision #56).

Because the process runs in **dev mode against real data**, these dev
conveniences are live on that host (kept on purpose by the owner,
2026-11-08):
- the seed admin's password, role and status are reset to
  `FIRST_ADMIN_PASSWORD` on every start (`FIRST_ADMIN_RESET_ON_STARTUP`);
- the leave-registration window is never closed and employees may open
  schedules more than two months ahead;
- CORS is `*` and `/docs`, `/redoc` and the OpenAPI schema are served;
- `CREATE DATABASE` is attempted when the database is missing;
- the staging/prod startup refusals below do not apply (only the
  `TIMEZONE` check runs in every environment).

### Starting the backend
1. **Migrate first, every time the code changes:**
   ```bash
   cd backend
   .venv/bin/alembic upgrade head      # head is 0010 (2026-11-13)
   ```
   `AUTO_CREATE_TABLES` does not help here: it only builds a brand-new
   database and is ignored (with a warning in the log) once the database has
   an `alembic_version` table. Migration `0009` removes duplicate flight legs
   (same day + FLT number, keeping the lowest id) and adds a unique
   constraint; without it the flight import cannot rely on that rule. If you
   forget, startup logs a WARNING such as "Database schema revision 0008
   differs from the code's migration head 0010; run 'alembic upgrade head'"
   and the API may then fail on missing columns (the warning does not stop
   startup).
2. **Start the API**, bound to the workstation's tailnet address (find it
   with `tailscale ip -4`):
   ```bash
   .venv/bin/python -m uvicorn app.main:app --host <tailnet-ip> --port 8035
   ```
   Use `--host 127.0.0.1` when only this machine's client needs it.
   `--host 0.0.0.0` listens on every network of the host (office LAN,
   public Wi-Fi), and in dev mode CORS is `*` and `/docs` is open — use it
   only on purpose, behind a firewall.
   `make backend` / `make dev` add `--reload`, which suits editing code but
   not a long-running service. For a backend that others depend on, run the
   command above under a process manager that restarts it after a crash or a
   reboot (launchd on macOS, systemd on Linux, a Windows service wrapper such
   as NSSM), with `backend/` as the working directory so `.env` is found.
3. **Check it:** `GET /health` answers 200 when the database responds, 503
   otherwise. The `app.*` log lines (bootstrap, autorun) go to stderr at
   INFO; point the process manager's log file at them, and look for the
   schema WARNING from step 1 after every update.

### Autorun on this host
Every start of the backend, and the daily check at 00:05 Europe/Berlin
(decision #55):
- **drafts the CURRENT month if it has no schedule at all** — on any day.
  On a fresh install (or after the host was off for a whole run window) the
  first start therefore creates a draft of the current month;
- **from day `AUTORUN_DAY + 1` (default the 21st) until the end of the
  month, drafts NEXT month if it has no schedule yet.**

It never overwrites an existing draft or published month; drafts still need
an admin to publish them. The log says what happened ("generated draft",
"already exists, skipping", "no flight days", or an error; a second backend
that loses the race logs "already exists (created concurrently)").
Consequences:
- enter next month's flights before day 21, or regenerate after entering
  them (the log warns when a draft was planned without flights);
- if several backends ever point at the same database, keep
  `AUTORUN_ENABLED=true` on exactly one of them;
- a developer who starts a dev backend against the shared database triggers
  the same generation (current month any day, next month from day 21);
  set `AUTORUN_ENABLED=false` in that developer's `.env`.

### Maintenance scripts against the shared database
`scripts/seed_demo_users.py` and `scripts/reset_all_passwords.py` refuse
(exit code 2) because the tailnet database is not local; `--allow-non-dev`
overrides on purpose. Both prompt for the password without echo when
`--password` is omitted (`seed_demo_users.py` has no default password).

## Shared server at 160.187.228.64 (2026-11-13)
The API now also runs on the owner's VPS (Ubuntu 24.04, user `trunggian`,
reached over Tailscale at `100.114.205.121`), published as
`http://160.187.228.64/` (desktop clients use `http://160.187.228.64/api/v1`).

- **Code:** `~/attendance-scheduler/backend` (a copy of `backend/`, not a git
  checkout). Stack: `backend/docker-compose.prod.yml` — PostgreSQL 16 and the
  API image, both bound to the host only (API on `127.0.0.1:8035`, the
  database on the compose network). The host already runs another PostgreSQL
  on `0.0.0.0:5432`; this stack does not use or touch it.
- **Settings:** `~/attendance-scheduler/backend/.env.prod` (mode 600, never in
  git; template `backend/.env.prod.example`). `ENVIRONMENT=prod` because the
  server is on the public internet and the dev admin password is public in
  this repository: the leave window, the two-month limit for employees and the
  startup guard are all active, `/docs` is not served.
- **Admin:** the database was copied from the owner's workstation on
  2026-11-13 (users, November roster, flights for November–December), then
  the seed admin got the random `FIRST_ADMIN_PASSWORD` of `.env.prod`. The
  other accounts kept their passwords.
- **nginx:** `deploy/nginx-attendance.conf`, installed as the site
  `attendance-scheduler` (`server_name 160.187.228.64`, so the named sites and
  the `default` site are unchanged). Plain HTTP: Let's Encrypt does not issue
  certificates for a bare IP; use a domain name and certbot for HTTPS.
- **Update the code:** copy `backend/` again (without `.env`, `.venv`,
  `tests`), then
  `docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build`
  in `~/attendance-scheduler/backend` (the image runs `alembic upgrade head`).
- **Clients:** macOS on a Mac with
  `flutter build macos --release --dart-define=API_BASE_URL=http://160.187.228.64/api/v1`;
  Windows and Linux from the manual workflow
  `.github/workflows/desktop-release.yml`
  (`gh workflow run desktop-release.yml -f api_base_url=...`). The builds are
  not code-signed: macOS asks to confirm the first start (right-click → Open),
  Windows SmartScreen shows "More info → Run anyway".

## Target production layout

### Hosting
- **Region: EU/EEA, prefer Germany/Frankfurt** (§9.4). Set `DATA_REGION`
  accordingly. Do not transfer data outside the EU (especially to the US).
- Sign a **DPA (GDPR Art. 28)** with the cloud or hosting provider.
- PostgreSQL in the EU (managed instance, or the current tailnet database
  once it is backed up and encrypted at rest); backups stay in-region.

### Transport & storage
- **TLS/HTTPS** for all client↔API traffic outside a private tailnet (§9.5);
  terminate at a reverse proxy.
- **Encryption at rest** for the DB volume and backups.
- Secrets (`SECRET_KEY`, DB URL, admin password) via environment/secret
  manager — never in git, never baked into an image (`backend/.dockerignore`
  keeps `.env` out of the Docker build context).

### Environment guard
- `ENVIRONMENT=dev` is meant for laptops and the current workstation setup:
  it resets the seed admin's password to `FIRST_ADMIN_PASSWORD` on every
  start and skips the leave-registration window and the non-admin
  schedule-month limit.
- `ENVIRONMENT=staging` gets exactly the same checks as `prod`. Both
  **refuse to start** ("Refusing to start: unsafe settings …") while any of
  these hold:
  - `SECRET_KEY` is the code's dev default, the `.env.example` placeholder
    (`please-generate-a-long-random-string`) or shorter than 32 characters;
  - `FIRST_ADMIN_PASSWORD` is the dev default or shorter than 12 characters;
  - `DATABASE_URL` is SQLite or the dev default
    (`postgres:postgres@localhost`);
  - `BACKEND_CORS_ORIGINS` contains `*`;
  - `AUTO_CREATE_TABLES=true`;
  - `DATA_RETENTION_MIN_MONTHS` is below 24, or `DATA_RETENTION_MONTHS` is
    below the effective floor.
  An unknown `TIMEZONE` is refused in every environment.
  `FIRST_ADMIN_RESET_ON_STARTUP=true` is only logged as a warning (it is
  ignored outside dev). An existing admin's credentials are never touched,
  and `/docs`, `/redoc` and the OpenAPI schema are not served.
- The Docker image ships `ENVIRONMENT=prod`, `AUTO_CREATE_TABLES=false`,
  `FIRST_ADMIN_RESET_ON_STARTUP=false`, installs the versions pinned in
  `requirements.lock` and runs `alembic upgrade head` before `uvicorn`.
  Supply the secrets, `DATABASE_URL` and `BACKEND_CORS_ORIGINS` with `-e` /
  compose `environment` / a secret manager.
- Generate a secret: `python -c "import secrets; print(secrets.token_urlsafe(48))"`.

### Schema & startup
- Provision the schema with **Alembic**: `alembic upgrade head` before every
  start of new code (the Docker image does this automatically).
- A database built by the old `create_all` path (no `alembic_version`
  table) already holds the schema of the code that built it: run `alembic
  stamp head` when that was the current code (otherwise stamp the revision
  that was head in that code), then `alembic upgrade head`. Do **not** stamp
  `0001`: later migrations would then fail with DuplicateTable.
- The seed admin (role M) is created on start from `FIRST_ADMIN_*` only while
  no active admin exists; a seed admin deleted on purpose is not recreated.
  Change its password from the app after the first login; staging/prod never
  reset it.

## Access control (§9.5) and sickness (§9.1)
- Role-based: normal users see only their own data (`/attendance/me`, own
  leaves / shift-changes / time clock / export); admins
  (role M) manage everyone. A user disabled mid-session is signed out by the
  client at the next refused request (decision #56).
- **Sick `S` is special-category health data:**
  - written only by admins into ACTUAL attendance, every write audited;
  - never stored with a free-text note (the API drops it), and the A/D cover
    row of a colleague carries no note either (decision #53);
  - never accepted in the PLANNED schedule (override and shift-change
    reject it), and any legacy S of another person is masked
    as X when a non-admin reads a schedule;
  - visible to the person themself in `/attendance/me` (data-subject access)
    and to admins in the month-wide grid and exports.
- Month-wide attendance, schedule violations and report exports are
  admin-only. Exported text cells that a spreadsheet would run as a formula
  are prefixed with `'` (decision #48).

## Audit log (§9.5)
- Every admin mutation writes an `audit_logs` row (actor, action, entity,
  id, detail): user create/update/delete, account approval, schedule
  generate/override/publish, leave / shift-change decisions,
  attendance and S writes, holiday CRUD, manual flight entry, preset CRUD,
  Excel import, report export, month-close, retention purge, data export.
  The autorun records `actor_id = NULL` (system).
- **Fail-loud:** if the audit row cannot be written the request returns
  HTTP 500 and the failure is logged with full context.
- **Known limitation:** for most actions the service commits the business
  change before the endpoint writes the audit row, so a 500 there can mean
  "change persisted, audit missing" — reconcile from the error log. User
  deletion is the exception: its `user.delete` row is committed in the same
  transaction as the delete, so either both persist or neither does
  (decision #50).

## Retention & data-subject rights (§9.3, Art. 15/17/20)
- `DATA_RETENTION_MONTHS` (default 36) defines how long personnel records are
  kept. `POST /api/v1/compliance/retention/purge` (admin, audited) deletes
  attendance, schedule cells, time-clock entries, leave / shift-change
  requests, the rows of the removed self-arrange feature (#63) and audit
  rows dated before the cutoff. The cutoff
  can never be more recent than the legal floor of 24 months (ArbZG §16(2)
  working-time records); `DATA_RETENTION_MIN_MONTHS` may raise the floor but
  never lower it. Run the purge monthly from a scheduler of your choice, e.g.
  `curl -X POST … -H "Authorization: Bearer <admin token>"`.
- **Access / portability:** `GET /api/v1/compliance/users/{id}/export`
  returns every record held about a person as JSON — the person themself
  or an admin may call it (audited).
- **Erasure:** admin `DELETE /api/v1/users/{id}` removes the person and their
  own history; audit rows they authored keep the row with `actor_id = NULL`,
  attendance they recorded is attributed to the deleting admin, and other
  people's requests they decided or joined are kept as described in decision
  #50.
- The customer's DPO owns the final retention figure and the legal basis
  (§26 BDSG) documentation.

## Features outside the original specification — legal review needed
One owner-requested feature (2026-07-09) is not in `PROJECT_OVERVIEW.md`
and must be part of the DPO / works-council review before rollout:
- **Time clock** (`/attendance/clock/*`): real check-in/out timestamps per
  person per day. This is behaviour monitoring in the §87(1) No.6 BetrVG
  sense.
It is own-data-only for employees, audited, included in the data export
and covered by the retention purge. (Self-arrange, the second such feature,
was removed on 2026-11-10 — decision #63; its old rows stay in the export
and the purge.)

## AI Act (§9.6)
The scheduler is **rule-based (OR-Tools CP-SAT)** — it performs NO AI/ML
evaluation of staff. `SCHEDULER_IS_RULE_BASED=true`. Introducing ML scoring of
employees requires a fresh legal review (EU AI Act high-risk from 2026-08-02).

## Backup, restore, health
- `scripts/backup_db.sh [--encrypt-age RECIPIENT | --encrypt-gpg RECIPIENT]
  [dest]` — `pg_dump` custom-format archive, pruned after `BACKUP_KEEP_DAYS`
  (30). The password is passed through `PGPASSWORD`, never on the command
  line, and the URL is printed masked. Use one of the encryption flags when
  the archive leaves the machine. Schedule it daily; keep archives in-region.
- `scripts/restore_db.sh [--age-identity KEYFILE] <archive>` —
  `pg_restore --clean`, then prints the Alembic revision so you can confirm
  it matches `alembic current`. **Rehearse a restore on staging before
  go-live.**
- `GET /health` returns 200 `{"status":"ok"}` only when the database answers
  `SELECT 1`; otherwise 503 `{"status":"degraded"}`. Point the uptime
  monitor at it.

## CI
`.github/workflows/ci.yml` runs on every push to `main` and every PR:
- **Backend** (Ubuntu 24.04): dependencies pinned by `requirements.lock`,
  ruff, mypy, pytest on SQLite, a fresh `alembic upgrade head` plus
  `alembic check` and the full test suite on PostgreSQL 16, and the
  production-guard smoke test (it must refuse the dev defaults).
- **Flutter** (Ubuntu 24.04, Flutter 3.47.7): `flutter analyze` and
  `flutter test --exclude-tags golden`.
- **Flutter goldens** (macOS 15): `flutter test --tags golden`; the pixel
  goldens are rendered on macOS and only match there. Diffs are uploaded on
  failure.
- **Windows build**: `flutter build windows --release`, uploaded as the
  `attendance-scheduler-windows` artifact. It waits only for the Ubuntu
  Flutter job, not for the goldens.

All three Flutter jobs install packages with `flutter pub get
--enforce-lockfile`, so a `pubspec.lock` that does not match `pubspec.yaml`
fails the build instead of resolving new versions.

## ⚠ Pre-rollout gate — Betriebsrat (§9.2)
A system that can monitor staff behaviour/performance needs an agreement with
the works council (Betriebsrat) under §87(1) No.6 BetrVG **if the customer has
one**. **OPEN QUESTION — confirm with the customer before production rollout.**
The time-clock feature above makes this question unavoidable.

## Run (all options)
- **Workstation, as today:** see "The current setup" above — migrate, then
  `uvicorn` under a process manager.
- **Docker (option):** `docker compose up --build` in `backend/` starts
  PostgreSQL 16 and the API; the API waits for the database health check
  and runs `alembic upgrade head` first. Compose reads `backend/.env`, which
  is dev by default; for a production-like run set `ENVIRONMENT=prod` and the
  values the guard requires.
- Behind an HTTPS reverse proxy for anything reachable outside a private
  tailnet.
- The autorun runs inside the API process (APScheduler). With several
  backends on one database, set `AUTORUN_ENABLED=false` on all but one.
- Flutter desktop client: `API_BASE_URL` points at the API (`--dart-define`
  wins over the bundled `.env`). Release builds start with an empty login
  form; only debug builds pre-fill the seed admin.
