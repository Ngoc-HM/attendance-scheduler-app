# Phase 07 — F-14 Calculations (Comp / Streak / Premium-Off Carry)

## Context Links
- Spec: §4.6 / F-14, §8 (auto-calc), §5.3 #6 (A/D → CD), §5.5 (carry_streak). Locked decision #6 (premium-off carry).
- Files: `backend/app/services/calculation_service.py`, `backend/app/api/v1/endpoints/calculations.py`, `backend/app/models/user.py` (carry fields), `backend/app/scheduler/calendar_utils.py` (trailing_work_streak).

## Overview
- Priority: P1. Depends on 05 (assignments) + 06 (actuals).
- At month close, compute carry-over into next month: comp days (CD from A/D), consecutive-streak, premium-off accrual.

## Key Insights
- F-14 scope note: only current comp-day logic; NO complex annual-leave accrual.
- A/D earns +1 working day & 1 CD next month (§5.3 #6 / §7). Count A/D in actuals → carry_comp += count.
- carry_streak = trailing working-day run at month end (`trailing_work_streak`), used by next month's max-consecutive boundary window.
- carry_premium_off accrues from premium days (Sat/Sun/holiday) where person was OFF (X) this month; balances fairness across months (decision #6).
- Calc reads ACTUAL records (phase 06), falling back to planned assignments if actuals absent.

## Requirements
Functional:
- `compute_month_close(year, month)`: per user compute `carry_comp` delta (A/D count), `carry_streak` (trailing run), `carry_premium_off` delta (premium OFF days), and persist onto `users` for use next month.
- Idempotent: re-running for same month replaces that month's contribution (store last-computed month to avoid double-count) OR compute deltas freshly from records each run (preferred: recompute from records, set absolute carry).
- Expose summary endpoint (per-user comp/streak/premium-off).

Non-functional: deterministic; safe to re-run.

## Architecture
Data flow: actual_records_map(year,month) + holiday_dates → per-user aggregation → set `users.carry_comp/carry_streak/carry_premium_off`. Next month's `schedule_input_builder` reads these into PersonInput.

Idempotency: recompute carry from the just-closed month's records as the authoritative source. carry_comp = prior outstanding − consumed CD this month + A/D earned this month (track CD consumption from records where code==CD).

## Related Code Files
Modify:
- `backend/app/services/calculation_service.py` — implement compute_month_close + summary.
- `backend/app/api/v1/endpoints/calculations.py` — wire (POST compute-month-close, GET summary; admin-guarded).
- `backend/app/scheduler/calendar_utils.py` — reuse `trailing_work_streak` (already present).

Create:
- `backend/app/services/carry_over_math.py` — pure functions: comp delta, streak, premium-off count (<200 LOC, testable without DB).

Delete: none.

## Implementation Steps
1. `carry_over_math.py`: `comp_days_from_records(records)` (count A/D), `consumed_cd(records)` (count CD taken), `trailing_streak(ordered_working_flags)` (wraps calendar util), `premium_off_count(records, premium_dates)`.
2. `compute_month_close`: IDEMPOTENT BY RECOMPUTATION — recompute ALL carry values absolutely from full record history up to the closed month (cheap at ≤10 users): carry_comp = Σ earned_AD − Σ consumed_CD over history (floor 0); carry_streak = trailing run of the closed month; carry_premium_off = Σ premium-off count over history. NO incremental `+=` against the stored value (re-run would double-count). Persist absolutes.
3. Summary endpoint returns per-user carry triple.
4. Wire + admin guard; audit.

## Todo List
- [ ] carry_over_math pure functions
- [ ] compute_month_close (comp/streak/premium-off persist)
- [ ] idempotent recompute from records
- [ ] summary endpoint
- [ ] wire + guard + audit

## Success Criteria
- A user with 2 A/D days this month → carry_comp increases by 2 (minus any CD consumed).
- Month ending on a 3-day working run → carry_streak = 3; 0 if last day OFF.
- A user OFF on 2 Saturdays → carry_premium_off increases by 2.
- Re-running compute_month_close yields identical carry values (idempotent).

## Risk Assessment
- Double-counting on re-run (Med/High) → recompute from records (absolute), don't accumulate blindly; test re-run idempotency.
- CD consumption tracking ambiguous (Med/Med) → CD appears as a code in records; count it as consumption. Confirm with customer if CD can partially carry.
- Cross-boundary streak vs carry from prior month (Med/Med) → streak uses this month's trailing run only; prior carry already applied during that month's solve.

## Security Considerations
- Calc admin-only; reads actuals (no S detail needed beyond off/working flag). Audit run.

## Next Steps
Unblocks phase 08 (reports use comp/working totals) and feeds next-month phase 05 generate.
