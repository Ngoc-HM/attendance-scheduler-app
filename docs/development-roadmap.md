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
| 05 | Schedule service + autorun (00:05 the day after `AUTORUN_DAY`) | F-07/08/09, #9 | ✅ done |
| 06 | Attendance, sick backfill, holidays | F-10/11/12/13 | ✅ done |
| 07 | Calculations (carry comp/streak/premium) | F-14 | ✅ done |
| 08 | Reports (monthly/yearly export) | F-15 | ✅ done |
| 09 | Flutter wiring (5 pages → real API) | all UI | ✅ done |
| 10 | GDPR hardening (RBAC, audit, sick) | §9 | ✅ done |
| 11 | Testing | — | ✅ done (2026-11-08: 479 backend + 136 Flutter tests) |
| 12 | Docs | — | ✅ done |

## Current state — 2026-11-08 review-2 fixes
- 2026-11-08: every finding of the 2026-11-08 whole-system review fixed
  except A1 (the dev-mode seed-admin reset, kept on purpose by the owner);
  rulings R1–R8 and the rulings taken during the work are design decisions
  #41–#59 (see `project-changelog.md`). Backend 479 tests, `ruff`/`mypy`
  clean, Alembic head `0009`; Flutter `analyze` clean, 136 tests incl. 3
  goldens (goldens run on macOS only).
- The backend runs in `ENVIRONMENT=dev` on a workstation against a shared
  PostgreSQL over Tailscale (`deployment-guide.md`, "The current setup").
- 2026-11-07: owner decisions D1 (holiday work → +1 CD, every role) and D4
  (annual leave quota) implemented, review findings B1–B10 / C1–C11 fixed
  (design decisions #24–#40). The 2026-09-03 notes below still hold.
- **Backend (2026-09-03):** F-01..F-15 implemented, `ruff` and `mypy` clean.
  Production environment guard, dev-only seed-admin reset, sickness never in
  the planned schedule (write-reject + read-mask), no note on S rows,
  fail-loud audit covering user CRUD / approval / manual flight entry /
  month-close / autorun, F-09 recheck mirroring every engine rule,
  premium-off carry derived from history, 3-criteria leave-conflict ranking,
  retention purge + data-subject export, DB-backed `/health`.
- **Frontend:** every screen wired; Excel import and month-close in the UI;
  auth guard on all routes; 401 → session expired → login; a confirmed 403
  (account disabled) ends the session; logout clears every user's data;
  violations shown before publishing; release builds start with an empty
  login form. `flutter analyze` clean.
- **CI:** `.github/workflows/ci.yml` — backend (locked dependencies, ruff,
  mypy, pytest on SQLite and on PostgreSQL 16 after a fresh `alembic upgrade
  head` + `alembic check`, production-guard smoke), Flutter on Ubuntu
  (`analyze`, tests without goldens), goldens on macOS 15, and the
  `flutter build windows` artifact (needs only the Ubuntu Flutter job).
- DB at Alembic `0009` (run `alembic upgrade head` before starting).

## Remaining before production
| Item | Owner | Notes |
|------|-------|-------|
| Betriebsrat agreement (§9.2) | customer | now also covers the time clock (self-arrange was removed, #63) |
| Staffing exact vs minimum, extra role-A person (D7) | customer | see design-decisions "Open questions" |
| Weekend preference for paired offs (D6) | owner | decided 2026-11-10: Fri+Sat > Sat+Sun > Sun+Mon (#62) |
| Real annual-leave quota | customer | 30 days is a placeholder (decision #30) |
| 2026-11 customer notes | owner / customer | listed in design-decisions "Open questions" |
| Confirm the 2026-11-08 provisional rulings | owner / customer | leave next to weekly offs (#41), comp days before the cut-off (#43), disabled users' past cells as cover (I2, #44), no holiday-work penalty (R5) |
| Night shifts and the time clock | customer | check-out after midnight answers 409 today |
| Drafts in the data-subject export | customer DPO | Art. 15 export includes draft cells and draft-synced actuals |
| Id above the 64-bit range | dev | `schedule_id` > int64 still answers 500 on PostgreSQL |
| Leave dev mode on the shared database | owner | today: admin password reset on start, no leave window, CORS `*`, `/docs` open (`deployment-guide.md`) |
| Real "WR JUN26" Excel layout | customer | importer expects date / flt / route / STA / STD |
| Final retention period | customer DPO | shipped 36 months, floor 24 |
| Windows build smoke-tested on a customer PC | dev | CI produces the bundle; install + login + generate |
| PostgreSQL restore rehearsal on staging | dev/ops | `scripts/backup_db.sh` + `scripts/restore_db.sh` |
| Audit row in the same transaction as the change | dev (nice-to-have) | done for user delete (#50); other actions still fail-loud after commit, see decision #18 |

## Test coverage note
Backend has per-constraint bind + slack-violation tests, service/endpoint/RBAC/
audit tests, privacy (S) tests, production-guard tests, recheck-rule tests and
compliance tests; since 2026-11-08 also solve-phase, engine/checker
agreement, input-bounds (every year/month endpoint, every error detail is an
i18n key), user-delete (foreign keys on), bootstrap and autorun catch-up
tests. Flutter coverage = design-system boundary (all wired pages), i18n
parity and "every used key exists", app boot/navigation, API base URL
resolution, session restore and reset on logout, users-page guards and error
messages, schedule month switching / publish confirmation / shift-change
panel, attendance dialog and sick-cover payload, leaves reload and date
rules, reports selectors, flights batch, and schedule-page golden renders.
Deeper end-to-end UI flows (e.g. a full generate → publish → attendance run
against a live backend) remain manual (see the test guides in
`docs/superpowers/`).
