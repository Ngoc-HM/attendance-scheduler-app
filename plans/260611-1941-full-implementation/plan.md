---
title: "Attendance & Auto-Scheduler — Full Implementation (F-01..F-15)"
description: "Complete every backend feature + scheduler engine + Flutter wiring + tests + docs for the attendance/auto-scheduler app."
status: pending
priority: P1
effort: ~120h
branch: main
tags: [scheduler, or-tools, fastapi, flutter, gdpr, full-delivery]
created: 2026-06-11
---

# Attendance & Auto-Scheduler — Full Implementation

Source of truth: `PROJECT_OVERVIEW.md` (F-01..F-15, algorithm §5, GDPR §9).
Architecture is fully scaffolded; auth + user mgmt (F-01..F-03) are DONE. Everything else is STUBBED.

## Locked Decisions (do not re-question)
1. Scheduler = OR-Tools CP-SAT, rule-based, NO ML/AI (EU AI Act §9.6).
2. Staffing & off-day rules = SOFT constraints with penalized SLACK → model always feasible; slack>0 → Violation (§5.6). Only exactly-one-status stays hard.
3. Engine schedules EVERYONE incl. M/admins; flexible-vs-fixed lives in leave/swap layer. M/T not on flight duty default to O/D.
4. "2 X per week" counted SEPARATELY from approved AL/CD.
5. Holidays (PH) = NORMAL WORKING DAYS (overrides spec F-13/§7). Holiday model kept for "premium-off" concept only.
6. PREMIUM-OFF fairness: off on Sat/Sun/holiday is premium; balance `carry_premium_off` across months.
7. WEEK = 7-day blocks anchored at day 1 (1-7, 8-14,...); final partial block target X = round(k/7*2). Confirm with customer.
8. SHIFT-CHANGE REQUESTS (full): any user may request a change on an own cell (change code OR swap with a colleague) → admin approves → assignment updated + hard-rule re-check + audit. Flexible M/T requests are routine; fixed A1–A4 requests flagged for strict review (§3: admin may refuse).
9. DAY-20 AUTORUN: background job (APScheduler) closes registration on day 20 and auto-generates next month's DRAFT; manual admin generate stays available.
10. LEAVE REGISTRATION CYCLE: during month M, days 1–20, users register leave for month M+1; closes end of day 20.

## Phases
| # | Phase | Status | Depends on |
|---|-------|--------|-----------|
| 01 | [Foundation — models, calendar, config, migration strategy](phase-01-foundation.md) | ✅ done | — |
| 02 | [F-04 Flights — CRUD + Excel import](phase-02-flights.md) | ✅ done | 01 |
| 03 | [F-05/F-06 Leaves + Shift-Change Requests — windows, approval, conflict priority](phase-03-leaves.md) | ✅ done | 01 |
| 04 | [Scheduler Engine — hard constraints + soft objectives + slack/violations](phase-04-scheduler-engine.md) | ✅ done | 01 |
| 05 | [F-07/F-08/F-09 Schedule Service — generate, override, publish, day-20 autorun](phase-05-schedule-service.md) | ✅ done | 02,03,04 |
| 06 | [F-10/F-11/F-12/F-13 Attendance, Sick, Holidays](phase-06-attendance-holidays.md) | ✅ done | 01,05 |
| 07 | [F-14 Calculations — comp/streak/premium-off carry](phase-07-calculations.md) | ✅ done | 05,06 |
| 08 | [F-15 Reports — monthly/yearly export](phase-08-reports.md) | ✅ done | 06,07 |
| 09 | [Flutter Wiring — flights, leaves, schedule, attendance, reports + i18n](phase-09-flutter-wiring.md) | ✅ done | 02,03,05,06,08 |
| 10 | [GDPR / §9 Hardening — sick access, audit, RBAC](phase-10-gdpr-hardening.md) | ✅ done | 06 |
| 11 | [Testing — pytest engine/services/endpoints + Flutter widget tests](phase-11-testing.md) | ✅ done | 02-10 |
| 12 | [Docs — README override notes + docs/ suite](phase-12-docs.md) | ✅ done | 01-11 |

## Recommended Execution Order
01 → (02 ∥ 03 ∥ 04 can run parallel; distinct files) → 05 → 06 → 07 → 08 → 09 → 10 → 11 → 12.
Phase 04 (engine) is highest-risk: most detail, dedicated per-constraint tests.

## Key Dependencies
- 05 needs flight_pairs (02), approved leave (03), working engine (04).
- 07 needs persisted assignments (05) + actual records (06).
- 09 (Flutter) needs the backend endpoints it wires to (02,03,05,06,08).

## Open Questions / Confirm-with-customer
- Final partial-week pro-rate rounding (round(k/7*2): 4-day tail → 1 X). Confirm.
- Do M/T appear in the A/D balance objective, or only A1–A4? (Decision #3 says engine schedules all; balance weight scope unclear.)
- Report layout/format (§F-15 deferred — building flexible CSV/Excel exporter).
- Betriebsrat (§9.2) existence at customer site — blocks production deploy if present.
- Excel import column mapping (sample "WR JUN26" layout not in repo) — needs a sample file.
- Can CD (comp days) partially carry across months? (phase 07 assumes full carry, floor 0.)

Resolved by owner (2026-06-11): Alembic adopted (phase 01); shift-change requests = full feature (#8); day-20 autorun (#9); leave cycle = days 1–20 of M for M+1 (#10).

## Progress (2026-06-11)
Backend COMPLETE — phases 01–08 + 10 done, **99/99 backend tests pass**. F-01..F-15 all functional + GDPR (RBAC, audit on every admin mutation, S admin-only, /attendance/me self-service, EU/no-AI config). Remaining: 09 Flutter wiring, 11 Flutter widget tests, 12 docs.
