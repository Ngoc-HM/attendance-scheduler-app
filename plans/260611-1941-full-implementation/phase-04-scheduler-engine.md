# Phase 04 — Scheduler Engine (CP-SAT: Hard Constraints + Soft Objectives + Slack/Violations)

## Context Links
- Spec: §5 (full), esp. §5.3 hard, §5.4 soft, §5.5 streak, §5.6 infeasible. Locked decisions 1–7. CP-SAT modeling guidance in task brief.
- Files: `backend/app/scheduler/{engine,constraints,objectives,domain,calendar_utils}.py`, `backend/app/models/enums.py`.

## Overview
- Priority: P1 — THE core. Highest risk. Most detail / sub-steps / dedicated tests.
- Status: ✅ COMPLETE (2026-06-11). All hard constraints + objectives + slack architecture implemented; verified: 0-slack full-staff month, exact staffing/off-quota, no 6-runs, carry_streak boundary, understaffed → violations + A/D fallback, balance spread ≤1, premium-off fairness. Engine tests in tests/test_engine_*.py (76/76 suite green). NOTE vs plan: uniform vocabulary {A,D,A/D,O/D,X} for ALL roles (simpler than per-person sets); staffing = equality with under+over slack (forbids spurious flight codes on 0-pair days); conflict_priority objective skipped (resolved in leave layer per phase 03).
- Implement 3 missing hard constraints + 2+1 soft objectives, switch staffing/off-day rules to SOFT-with-slack so the model is ALWAYS feasible, and report slack as Violations (§5.6).

## Key Insights
- Already done: `one_status_per_day` (HARD, keep), `respect_approved_off` (HARD pin, keep).
- Decision #2: ALWAYS-FEASIBLE architecture. Staffing (§5.3 #4), 2-X/week (§5.3 #2), max-consecutive (§5.3 #3) become SOFT via heavily-penalized slack vars. Only exactly-one-status stays truly hard. slack>0 → Violation (§5.6 #12-14) + A/D fallback suggestion (§5.3 #6).
- Decision #3: engine schedules everyone. Add `O_D` to assignable vocab for NON-fixed people so M/T not on flight duty default to office duty rather than spurious A/D. Fixed A1-A4 assignable = {A,D,A_D,X}; non-fixed = {A,D,A_D,O_D,X}. (Cleanest: per-person assignable set.)
- A/D covers one A AND one D simultaneously; usage penalized ("bất đắc dĩ" only); earns +1 workday & 1 CD next month (CD carry handled in phase 07 calc, not engine).
- File-size rule: split constraints/objectives into focused modules (<200 LOC each).

## Requirements
Functional (each constraint implemented with the CP-SAT formulation below):
- §5.3 #1 exactly-one-status: HARD (done).
- §5.3 #5 respect approved off: HARD pin (done).
- §5.3 #2 two X / 7-day block: SOFT; per person & block `sum(X) + slack_under - slack_over == target` (target = 2, or `partial_block_off_target` on final block). Separate from AL/CD (those are pinned X via approved_off but counted distinctly — see note).
- §5.3 #3 + §5.5 max 5 consecutive working: sliding window of 6 days → `sum(work) <= 5 + slack`. First days fold in `carry_streak`: window of `(6 - carry_streak)` from day 1 must contain >=1 X.
- §5.3 #4 fixed-group staffing: per day, demand from `flight_pairs[d]` (2→A=1,D=2; 1→A=1,D=1; 0→none). Coverage with A/D substitution + slack.
- Derived `works[p][d] = OR(A,D,A_D[,O_D])`.

Soft objectives (weighted sum, balance highest):
- §5.4 #7 balance A/D (weight 100).
- §5.4 #8 weekend pairing (weight 10): Sat+Sun > Fri+Sat > Sun+Mon.
- §5.4 #9 conflict priority (weight 5, optional): prefer larger carry_comp gets the contested X.
- NEW premium-off fairness (weight 30 — above weekend pairing, below balance; tunable): balance `carry_premium_off` across people (off on Sat/Sun/holiday).
- SLACK penalties: weight >> all objective weights (e.g. 10_000) so the solver only uses slack when genuinely infeasible.

## Architecture — CP-SAT formulations (implementer spec)
Decision vars `x[(uid, day, code)]` bool over per-person assignable codes. `works[p][d]` = sum of working codes for that cell.

Pinned codes counting toward "at work" for the consecutive rule: B, T, O/D(admin), and approved working cells. AL/CD/S/X count as OFF for the streak.

1. **two_days_off_per_week** (soft): for each person p, each block b: `sum(x[p,d,X] for d in block) + under[p,b] - over[p,b] == target_b`. `target_b = 2` (full) or `partial_block_off_target(len(block))`. Penalize `under+over` at SLACK weight. NOTE decision #4: AL/CD are separate — a block with an approved AL still needs its 2 X. Since approved_off pins those days to X in the decision layer, count ONLY non-approved X toward the target, OR raise target by approved-off count in block. **Chosen approach:** target_b += (#approved-off days in block) so the person still gets 2 genuine X on top of leave. Confirm rounding interaction on partial block (open question).

2. **max_consecutive_working** (soft): for every window of 6 consecutive days `[d..d+5]`: `sum(works over window) <= 5 + slack_streak[p,w]`. For the month start, add a window of `(6 - carry_streak)` days from day 1 requiring `sum(works) <= (5 - carry_streak)` (i.e. >=1 OFF), clamped to >=0. Penalize slack at SLACK weight.

3. **fixed_group_staffing** (soft): let F = fixed people (A1-A4). Per day d with demand (dA, dD):
   - `sum(x[p,d,A] for p in F) + sum(x[p,d,A_D] for p in F) + slackA[d] >= dA`
   - `sum(x[p,d,D] for p in F) + sum(x[p,d,A_D] for p in F) + slackD[d] >= dD`
   - Penalize `slackA+slackD` at SLACK weight; penalize total `A_D` usage at a moderate weight (discourage unless needed).

4. **balance_shifts** (soft, weight 100): per person `totalA[p]=sum(A)`, `totalD[p]=sum(D)` (decide A/D inclusion — open question). `AddMaxEquality(maxA, totalA[*])`, `AddMinEquality(minA, ...)`, same for D. Minimize `(maxA-minA)+(maxD-minD)`. Apply across A1-A4 group with extra weight.

5. **weekend_pairing** (soft, weight 10): per person per block, indicator `pair_satsun`, `pair_frisat`, `pair_sunmon` = AND of the two X day vars; reward (negative penalty) ordered 3:2:1.

6. **conflict_priority** (soft, weight 5, optional): for contested requested-off days, term favoring higher carry_comp. May be deferred to leave layer (phase 03) — keep optional.

7. **premium_off_fairness** (soft): premium days = Sat/Sun/`holidays`. `premium_off[p] = sum(x[p,d,X] for d in premium_days) + carry_premium_off[p]`. Minimize spread `(max-min)` of premium_off across people. Persist next-month `carry_premium_off` in phase 07.

Objective = `Minimize(SLACK_terms*BIG + balance*100 + premium*30 + weekend*10 + conflict*5)` (BIG = 10_000).

## Related Code Files
Modify:
- `backend/app/scheduler/engine.py` — per-person assignable codes; build `works`; collect slack vars; on solve, translate slack>0 into `Violation`s (§5.6) instead of only feasible/infeasible.
- `backend/app/scheduler/domain.py` — already extended in phase 01 (`carry_premium_off`, `holidays`); add weights/slack-weight to SolverInput or read from config.
- `backend/app/scheduler/objectives.py` — `add_all` aggregates from submodules.

Create (modularize, each <200 LOC, kebab-case):
- `backend/app/scheduler/constraints_off_days.py` — two_days_off_per_week (soft).
- `backend/app/scheduler/constraints_consecutive.py` — max_consecutive_working (soft + carry_streak).
- `backend/app/scheduler/constraints_staffing.py` — fixed_group_staffing (soft + A/D substitution).
- `backend/app/scheduler/objective_balance.py` — balance_shifts.
- `backend/app/scheduler/objective_weekend.py` — weekend_pairing.
- `backend/app/scheduler/objective_premium_off.py` — premium_off_fairness.
- `backend/app/scheduler/slack_registry.py` — collect/label slack vars → Violation mapping helper.

Refactor: `constraints.py` keeps `add_all` + the two hard rules; delegates soft rules to the new modules. `objectives.py` keeps `add_all` + WEIGHTS, delegates to objective_* modules.

Delete: none (keep existing test_scheduler_smoke.py; update if signature changes).

## Implementation Steps
1. Engine: introduce per-person assignable codes (fixed vs non-fixed incl. O_D for non-fixed).
2. Engine: build `works[p][d]` linear expr helper; expose to constraint modules.
3. Implement `slack_registry.py` (register slack var with rule+day+user metadata).
4. Implement `constraints_off_days.py` (soft 2-X/block, target adjusted for approved-off, partial-block target).
5. Implement `constraints_consecutive.py` (6-day windows + carry_streak boundary window).
6. Implement `constraints_staffing.py` (A/D substitution coverage + slack + A/D penalty term).
7. Implement `objective_balance.py`, `objective_weekend.py`, `objective_premium_off.py`.
8. Wire `constraints.add_all` and `objectives.add_all` to call new modules + sum penalties incl. BIG slack weight.
9. Engine solve(): after solve, read slack values; any slack>0 → append `Violation(rule, message, day, user_id)`; still return feasible=True with assignments (always-feasible model).
10. Tune weights so slack only fires under true shortage (BIG >> sum of all soft maxima).

## Todo List
- [ ] Per-person assignable codes (O_D for non-fixed)
- [ ] works[p][d] helper
- [ ] slack_registry + Violation mapping
- [ ] constraints_off_days (soft, approved-off-aware)
- [ ] constraints_consecutive (soft + carry_streak boundary)
- [ ] constraints_staffing (A/D substitution + slack + A/D penalty)
- [ ] objective_balance (highest weight)
- [ ] objective_weekend (Sat+Sun > Fri+Sat > Sun+Mon)
- [ ] objective_premium_off (carry balance)
- [ ] objective conflict_priority (optional)
- [ ] Engine: slack→Violation translation, always-feasible
- [ ] Weight tuning so slack is last resort

## Success Criteria (proven by phase 11 tests)
- Every person gets exactly one code/day (hard).
- Full-staffing scenario: solver finds 0-slack solution; A1-A4 daily A/D counts match demand.
- 2 X per 7-day block honored when feasible; partial final block uses pro-rated target.
- No 6+ consecutive working days; carry_streak=4 → at most 1 working day before forced X at month start.
- Under-staffed day → solution still returned, A/D suggested, Violation reported with day + rule.
- A/D balance spread minimized across A1-A4.
- Premium-off spread shrinks vs. naive assignment when carry differs.

## Risk Assessment
- Model infeasible despite slack (e.g. exactly-one + pinned conflict) (Med/High) → keep ONLY exactly-one + approved-off pin hard; everything else soft; assert pins don't contradict (validate input pre-solve).
- Solve time blow-up at 30 people × 31 days (Med/Med) → time limit + FEASIBLE acceptance; tune; reduce var count via per-person code sets.
- Weight mis-tuning lets solver "buy out" a constraint cheaply (Med/High) → BIG slack weight, integration test asserting 0 slack when feasible.
- A/D double-count in balance (Med/Med) → decide inclusion explicitly; test.
- Week-block change interacts with partial-block target + approved-off offset (Med/Med) → dedicated unit test on a month with a leave in the final partial block.

## Security Considerations
- Engine is pure compute, no PII beyond user_id. Sick (S) never enters engine vocab — handled as pinned OFF/backfill at service layer (phase 06).
- Rule-based only; NO ML/AI scoring (EU AI Act §9.6) — document in code header.

## Next Steps
Unblocks phase 05 (schedule_service maps ORM→SolverInput, persists output, surfaces Violations). Per-constraint tests live in phase 11.
