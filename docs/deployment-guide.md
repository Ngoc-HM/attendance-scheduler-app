# Deployment Guide (EU / GDPR)

Deploying personnel data in Germany (Frankfurt) → GDPR (EU) + BDSG (federal).
This guide records the §9 controls for the customer's DPO sign-off. Legal
responsibility rests with the customer.

## Hosting
- **Region: EU/EEA, prefer Germany/Frankfurt** (§9.4). Set `DATA_REGION`
  accordingly. Do not transfer data outside the EU (especially to the US).
- Sign a **DPA (GDPR Art. 28)** with the cloud provider.
- PostgreSQL on a managed EU instance; backups stay in-region.

## Transport & storage
- **TLS/HTTPS** for all client↔API traffic (§9.5). Terminate at the proxy.
- **Encryption at rest** for the DB volume and backups.
- Secrets (`SECRET_KEY`, DB URL, admin password) via environment/secret
  manager — never in git.

## Environment guard (blocker #1 of the 2026-09-03 review)
- `ENVIRONMENT=dev` is for laptops only: it resets the seed admin's password
  to `FIRST_ADMIN_PASSWORD` on every start, skips the leave-registration
  window and the non-admin schedule-month limit.
- `ENVIRONMENT=staging|prod` **refuses to start** while `SECRET_KEY` is the
  dev default / shorter than 32 chars or `FIRST_ADMIN_PASSWORD` is the dev
  default / shorter than 12 chars. An existing admin's credentials are never
  touched. `AUTO_CREATE_TABLES=true` and `BACKEND_CORS_ORIGINS=*` are allowed
  but logged as warnings.
- The Docker image ships `ENVIRONMENT=prod`, `AUTO_CREATE_TABLES=false`,
  `FIRST_ADMIN_RESET_ON_STARTUP=false` and runs `alembic upgrade head`
  before `uvicorn`. Supply the secrets with `-e` / compose `environment` /
  a secret manager.
- Generate a secret: `python -c "import secrets; print(secrets.token_urlsafe(48))"`.

## Schema & startup
- Provision schema with **Alembic**: `alembic upgrade head` (the image does
  this automatically).
- An existing DB created by the old `create_all` path: `alembic stamp 0001`
  then `alembic upgrade head`.
- The seed admin (role M) is created on first start from `FIRST_ADMIN_*`.
  Change its password from the app after the first login; production never
  resets it.

## Access control (§9.5) and sickness (§9.1)
- Role-based: normal users see only their own data (`/attendance/me`, own
  leaves / shift-changes / self-arrange / time clock / export); admins
  (role M) manage everyone.
- **Sick `S` is special-category health data:**
  - written only by admins into ACTUAL attendance, every write audited;
  - never stored with a free-text note (the API drops it);
  - never accepted in the PLANNED schedule (override, shift-change and
    self-arrange reject it), and any legacy S of another person is masked
    as X when a non-admin reads a schedule;
  - visible to the person themself in `/attendance/me` (data-subject access)
    and to admins in the month-wide grid and exports.
- Month-wide attendance and report exports are admin-only.

## Audit log (§9.5)
- Every admin mutation writes an `audit_logs` row (actor, action, entity,
  id, detail): user create/update/delete, account approval, schedule
  generate/override/publish, leave / shift-change / self-arrange decisions,
  attendance and S writes, holiday CRUD, manual flight entry, preset CRUD,
  Excel import, report export, month-close, retention purge, data export.
  The autorun (00:05 the day after `AUTORUN_DAY`) records `actor_id = NULL`
  (system).
- **Fail-loud:** if the audit row cannot be written the request returns
  HTTP 500 and the failure is logged with full context. Known limitation:
  services commit the business change before the endpoint writes the audit
  row, so a 500 here can mean "change persisted, audit missing" — reconcile
  from the error log.

## Retention & data-subject rights (§9.3, Art. 15/17/20)
- `DATA_RETENTION_MONTHS` (default 36) defines how long personnel records are
  kept. `POST /api/v1/compliance/retention/purge` (admin, audited) deletes
  attendance, schedule cells, time-clock entries, leave / shift-change /
  self-arrange requests and audit rows dated before the cutoff. The cutoff
  can never be more recent than `DATA_RETENTION_MIN_MONTHS` (24 — ArbZG
  §16(2) working-time records). Run it monthly from a scheduler of your
  choice, e.g. `curl -X POST … -H "Authorization: Bearer <admin token>"`.
- **Access / portability:** `GET /api/v1/compliance/users/{id}/export`
  returns every record held about a person as JSON — the person themself
  or an admin may call it (audited).
- **Erasure:** admin `DELETE /api/v1/users/{id}` removes the person and
  cascades their history; audit rows they authored keep the row with
  `actor_id = NULL`.
- The customer's DPO owns the final retention figure and the legal basis
  (§26 BDSG) documentation.

## Features outside the original specification — legal review needed
Two owner-requested features (2026-07-09) are not in `PROJECT_OVERVIEW.md`
and must be part of the DPO / works-council review before rollout:
- **Time clock** (`/attendance/clock/*`): real check-in/out timestamps per
  person per day. This is behaviour monitoring in the §87(1) No.6 BetrVG
  sense.
- **Self-arrange** (`/self-arrange`): employees propose batch changes to
  their own published cells; admins approve.
Both are own-data-only for employees, audited, included in the data export
and covered by the retention purge.

## AI Act (§9.6)
The scheduler is **rule-based (OR-Tools CP-SAT)** — it performs NO AI/ML
evaluation of staff. `SCHEDULER_IS_RULE_BASED=true`. Introducing ML scoring of
employees requires a fresh legal review (EU AI Act high-risk from 2026-08-02).

## Backup, restore, health
- `scripts/backup_db.sh [dest]` — `pg_dump` custom-format archive, pruned
  after `BACKUP_KEEP_DAYS` (30). Schedule it daily; keep archives in-region
  and encrypted.
- `scripts/restore_db.sh <archive>` — `pg_restore --clean`, then prints the
  Alembic revision so you can confirm it matches `alembic current`.
  **Rehearse a restore on staging before go-live.**
- `GET /health` returns 200 `{"status":"ok"}` only when the database answers
  `SELECT 1`; otherwise 503 `{"status":"degraded"}`. Point the load balancer
  / uptime monitor at it.

## CI
`.github/workflows/ci.yml` runs on every push/PR: ruff, mypy, pytest on
SQLite, a fresh `alembic upgrade head` plus the full test suite on
PostgreSQL 16, the production-guard smoke test, `flutter analyze`,
`flutter test`, and a `flutter build windows --release` job that uploads the
Windows bundle as an artifact.

## ⚠ Pre-rollout gate — Betriebsrat (§9.2)
A system that can monitor staff behaviour/performance needs an agreement with
the works council (Betriebsrat) under §87(1) No.6 BetrVG **if the customer has
one**. **OPEN QUESTION — confirm with the customer before production rollout.**
The time-clock feature above makes this question unavoidable.

## Run
- Backend: `uvicorn app.main:app` behind an HTTPS proxy; `docker compose up`
  for the full stack (compose reads `backend/.env`, which is dev by default).
- The autorun (00:05 the day after `AUTORUN_DAY`) runs inside the API process
  (APScheduler). For multi-replica
  deployments, run it on a single instance (set `AUTORUN_ENABLED=false` on the
  others) to avoid duplicate generation.
- Flutter desktop client: `API_BASE_URL` in its `.env` points at the API.
  Release builds start with an empty login form; only debug builds pre-fill
  the seed admin.
