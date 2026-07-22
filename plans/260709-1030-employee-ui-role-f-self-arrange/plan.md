---
title: "Employee UI rebuild + Role F + self-arrange + time-clock"
description: "Add role F, employee shell w/ view+leaves+clock+self-arrange, weekend colors, T+2 visibility"
status: completed (2026-07-09; backend 157/157 pytest, flutter analyze clean; review H1/M2-M5 fixed)
priority: P2
effort: 22h
branch: main
tags: [backend, flutter, scheduler, rbac, migration, i18n]
created: 2026-07-09
---

# Overview

Owner request 2026-07-09: split new role **F** off T (no admin, scheduler-exempt
except weekly-2-off); rebuild the employee (non-M) UI (deleted → `EmployeeBlankShell`)
with View schedule / Register leave / Check-in-out / Self-arrange (T & F only);
weekend column tint; employee schedule visibility T-n..T+2 published-only.

## Data flow (high level)
`Role.F` → scheduler skips consecutive/off-chain/staffing, keeps weekly-off → published
schedule → employee shell (role-gated tabs) → self-arrange BATCH proposal (own cells,
published, weekly-off validated) → **admin approves once** → applied to schedule /
time-clock POST (timestamps) → audit log.

## Phases

| # | Phase | Status | Wave | Blockers |
|---|-------|--------|------|----------|
| 01 | [Backend Role F](phase-01-backend-role-f.md) | done | 1 | — |
| 02 | [Backend self-arrange + visibility](phase-02-backend-self-arrange.md) | done | 2 | P01 |
| 03 | [Backend time-clock](phase-03-backend-time-clock.md) | done | 1 | — |
| 04 | [FE employee shell + routing + i18n](phase-04-fe-shell-routing.md) | done | 2 | — |
| 05 | [FE weekend coloring](phase-05-fe-weekend-coloring.md) | done | 1 | — |
| 06 | [FE self-arrange tab](phase-06-fe-self-arrange-tab.md) | done | 3 | P02,P04 |
| 07 | [FE check-in/out page](phase-07-fe-time-clock-page.md) | done | 3 | P03,P04 |
| 08 | [FE role F in users/register](phase-08-fe-role-f-ui.md) | done | 3 | P01,P04 |
| 09 | [Testing](phase-09-testing.md) | done | 4 | all |

Review: [code-reviewer report](../reports/code-reviewer-260709-1030-role-f-employee-ui.md) —
H1 (leave-cell lock) + M2/M3/M4/M5 fixed same-day; M1 resolved by bucketing clock
days in Europe/Berlin (owner may override). 4 pre-existing Flutter test failures
(boundary flights/users, goldens Timer, tab-direction) flagged as separate task.

## Parallelization
- **Wave 1 (parallel, disjoint files):** P01, P03, P05
- **Wave 2:** P02 (after P01), P04 (foundation; owns shared FE files: shell, router, entity, i18n)
- **Wave 3 (parallel, own feature dirs only):** P06, P07, P08
- **Wave 4:** P09

## Key locked decisions (ALL owner-confirmed 2026-07-09)
- (a) F split from T, same nature: code domain = **{AD, X}**, T-like behavior.
- (b) Self-arrange = employee proposes batch → **admin approves once more** → applied.
  Server validates weekly-off at submit AND approve; cross-week clustering
  (Sat/Sun then Mon/Tue) fine as long as each 7-day block keeps its quota.
- (c) **Exactly 2 regulation X days**/block; AL/sick/CD do NOT count toward the 2.
- (d) M self-arranges via **existing admin override** — no new M UI.
- (e) Time-clock stores **timestamps only**; admin attendance grid unchanged.
- (f) Employees see **whole roster** in published month.
- (g) Anyone can self-register; **admin activates + assigns role** (incl. F).
- Self-arrange validation enforces **weekly-2-off only** (not consecutive).
- Schema via **Alembic** (`upgrade head`), NOT create_all in prod; tests use SQLite create_all.
- Weekend highlight = **row** tint (roster is transposed: days=rows).

## Dependencies / seams reused
- Weekly-off logic: `constraints_off_days` + `schedule_violation_checker.check_off_quota` + `calendar_utils.build_weeks/partial_block_off_target`.
- Published-only GET already enforced (`schedule_service.get`).
- Role guards: `api/deps.py`; audit: `audit_service.record`.
- Shift grid widget: `DsScheduleView` (business_views.dart) — shared admin+employee.

## Unresolved questions
Q a–g answered by owner 2026-07-09 (see locked decisions). Remaining minor:
- (h) off-chain (max-5-consecutive-OFF) dropped for F — implied by "no constraints
  except weekly-off"; proceeding with drop.
- T+2 guard returns 403 (explicit) — proceeding.
