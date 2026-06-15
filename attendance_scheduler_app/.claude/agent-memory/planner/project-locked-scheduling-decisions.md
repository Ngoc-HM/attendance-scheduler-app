---
name: project-locked-scheduling-decisions
description: Owner-locked decisions for the attendance auto-scheduler that DIVERGE from PROJECT_OVERVIEW.md spec — do not "fix" back to spec.
metadata:
  type: project
---

Locked decisions from the requirements owner (2026-06-11) for the Attendance & Auto-Scheduler. Several OVERRIDE the written spec (`PROJECT_OVERVIEW.md`).

- **Holidays (PH) = NORMAL WORKING DAYS.** This OVERRIDES spec F-13/§7 which said PH=X=off. Do NOT auto-pin holidays as off. Holiday model is kept only as a "premium-off" marker.
- **Always-feasible engine:** staffing, 2-X/week, max-consecutive are SOFT constraints with heavily-penalized slack vars; only exactly-one-status + approved-off pin stay hard. slack>0 → reported as a §5.6 Violation, NOT a solver failure.
- **Week = 7-day blocks anchored at day 1** (1-7, 8-14, ...), NOT Monday-anchored. Final partial block target X = round(k/7*2). (Was Monday-anchored in `calendar_utils.build_weeks`.)
- **Engine schedules everyone** incl. M/admins; flexible-vs-fixed lives in the leave/swap layer, not the solver. M/T not on flight duty default to O/D.
- **"2 X per week" counted separately from approved AL/CD** — a week with approved leave still needs its full 2 X.
- **Premium-off fairness (new):** off on Sat/Sun/holiday is premium; balance `carry_premium_off` across months. Added field on User + PersonInput.
- **Tech locked:** OR-Tools CP-SAT, rule-based, NO ML/AI (EU AI Act §9.6).

**Why:** owner clarified these in the requirements lock; the .docx spec predates them.
**How to apply:** when planning/implementing scheduler or holiday logic, follow these over the spec text. The full plan lives at `plans/260611-1941-full-implementation/`. See also [[seed-admin-reset-on-restart]] for auth behavior.
