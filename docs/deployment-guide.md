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
- Secrets (`SECRET_KEY`, DB URL) via environment/secret manager — never in git.

## Schema & startup
- Provision schema with **Alembic**: `alembic upgrade head`.
- An existing DB created by the old `create_all` path: `alembic stamp 0001`
  then `alembic upgrade head`.
- The seed admin (role M) is created/reset on startup from `FIRST_ADMIN_*`
  env vars — change the default password immediately in production.

## Access control & audit (§9.5)
- Role-based: normal users see only their own data (`/attendance/me`, own
  leaves/shift-changes); admins (role M) manage everyone.
- **Sick `S` is special-category health data (§9.1)**: admin-only read/write;
  no medical reason stored; every S write is audited. Non-admin month-wide
  attendance/report reads are blocked.
- **Audit log**: every admin mutation (schedule generate/override/publish,
  leave & shift-change decisions, attendance/S writes, holiday CRUD, flight
  import, report export) writes an `audit_logs` row (actor, action, entity).

## AI Act (§9.6)
The scheduler is **rule-based (OR-Tools CP-SAT)** — it performs NO AI/ML
evaluation of staff. `SCHEDULER_IS_RULE_BASED=true`. Introducing ML scoring of
employees requires a fresh legal review (EU AI Act high-risk from 2026-08-02).

## Retention & data-subject rights
- Define a retention policy; delete personnel data when its purpose ends (§9.3,
  §26 BDSG data minimization).
- Support access / rectification / erasure requests for personal data.

## ⚠ Pre-rollout gate — Betriebsrat (§9.2)
A system that can monitor staff behaviour/performance needs an agreement with
the works council (Betriebsrat) under §87(1) No.6 BetrVG **if the customer has
one**. **OPEN QUESTION — confirm with the customer before production rollout.**

## Run
- Backend: `uvicorn app.main:app` behind an HTTPS proxy; `docker compose up`
  for the full stack.
- Day-20 autorun runs inside the API process (APScheduler). For multi-replica
  deployments, run it on a single instance (set `AUTORUN_ENABLED=false` on the
  others) to avoid duplicate generation.
- Flutter desktop client: `API_BASE_URL` in its `.env` points at the API.
