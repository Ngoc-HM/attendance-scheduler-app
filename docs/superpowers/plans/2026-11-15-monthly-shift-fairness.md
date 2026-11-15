# Monthly Shift Fairness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Steps use checkbox tracking. User explicitly requests Sol implementers and parent final review; disjoint file ownership permits parallel work.

**Goal:** Implement monthly quotas, maximum-five work runs, fair A/D monthly distribution and chronological independent preferred-rest turns.

**Architecture:** Keep CP-SAT and effective-history assembly. Separate monthly constraints, chronological turn objectives and ordered optimization stages. Share pure accounting with persisted-grid recheck. Parent integrates and verifies all paths.

**Tech Stack:** Python, FastAPI, SQLAlchemy, OR-Tools CP-SAT, pytest; existing Flutter client.

**Spec:** `docs/superpowers/specs/2026-11-15-monthly-shift-fairness.md`.

## Global Constraints

- At most five consecutive working days; no Mon–Sun or rolling-seven work quota.
- Standard monthly working days = calendar days minus Saturdays and Sundays.
- Preserve leave/CD and holiday entitlements; no generated emergency A/D.
- A/D are ordinary shifts; demand remains 0:(0,0), 1:(1,1), 2:(1,2).
- Independent chronological Fri+Sat, Sat+Sun, Sun+Mon turns, including prior months.
- Only role A has A/D balancing; compare turns within roles.
- No writes to live DB during tests, no new third-party dependency, no push/deploy.

## Review Focus

1. Approved leave/CD must not cause make-up work or lost rest entitlement (Task 1).
2. Boundary X pairs counted once; regeneration/actual overrides change history without double counting (Task 2).
3. Six-person groups cannot lose fairness at rank four and above (Tasks 2/3).
4. Solver timeout retains incumbent and does not claim proven optimality (Task 3).
5. Manual edits and next-month rechecks agree with generated rules (Tasks 1/4).

### Task 1: Monthly quota and rest-rule replacement

**Files:** scheduler constraints.py, constraints_weekly_rest.py, objective_boundary_week.py, objective_monthly_off_target.py, new constraints_monthly_quota.py; services/schedule_violation_checker.py; core/i18n.py; relevant rest/checker tests.

**Interfaces:** retain `objective_monthly_off_target.target(inp, user_id)` as entitlement helper; new `constraints_monthly_quota.add(model, x, inp, registry)`; checker receives optional approved_off for the same accounting. Keep old input fields for compatibility where useful.

- [x] Write failing tests for one-rest/three-rest weeks, exact monthly X entitlement, leave/CD and boundary runs.
- [x] Replace weekly rule wiring with monthly quota violations; preserve max-five-consecutive.
- [x] Remove weekly-debt boundary objective, preserve meaningful consecutive-boundary behavior.
- [x] Mirror quota in recheck and update callers/messages, tests and shared rest assertions.
- [x] Run focused pytest for rest, comp, checker agreement, service integration; report files and results.

### Task 2: Independent chronological turns with effective history

**Files:** scheduler/domain.py, objective_off_pairing.py, objective_pair_points_fair.py (or replacement module); services/schedule_history.py, schedule_input_builder.py; turn/history tests.

**Interfaces:** add frozen `RestTurnHistory(count: int = 0, last_date: date | None = None)`; `PersonInput.rest_turns: dict[int, RestTurnHistory]` keyed by first weekday 4/5/6. Add `schedule_history.rest_turn_history(db, user_ids, year, month)`. Keep legacy pair-point fields while compatibility requires. Existing `terms(model, found, inp, weight, spread_weight)` may be retained as wrapper, expose ordered turn terms for engine integration.

- [x] Write failing chronological tests: no repeated Fri+Sat before available peers; counts tie -> longest wait; six people; independent kinds.
- [x] Aggregate genuine X+X history by kind and last date; include month-start boundary exactly once.
- [x] Implement chronological turn objective using earlier in-month assignments and eligibility; avoid all-zero/no-award solution and hard greedy allocation. Preserve feasible higher-priority duties.
- [x] Ensure best-day preference does not allow cross-kind turn substitution. Remove top-three fairness restriction.
- [x] Run turn/history tests plus small full-roster and multi-month cases; report mathematical limitations explicitly.

### Task 3: A/D fairness and ordered optimization

**Files:** scheduler/objective_balance.py, objectives.py, engine.py, optional new optimization module; solve-phase/balance tests. Coordinate Task 2 turn interface and Task 1 constraints.

**Interfaces:** keep `SchedulerEngine.solve(inp) -> SolverOutput`; implement named objective stages. Preserve public compatibility and existing status fields. Add phase diagnostics if needed.

- [x] Write failing tests for gaps [12,0,0,0] versus [3,3,3,3], equal/odd work counts and D-heavy demand.
- [x] Build max-gap, remaining fairness, and aggregate balance objectives across ALL role-A members; avoid sum-only or top-three logic.
- [x] Prioritize rule violations/month quota, individual A/D fairness, chronological turns, then reserve/pair-shaping preferences; prevent lower-stage regression.
- [x] Bound all stages by one max_solve_seconds deadline; keep incumbent on timeout and truthful proof flags.
- [x] Run focused balance, solve-phase, staffing, reserve and role tests; report timing and unavoidable tradeoffs.

### Task 4: Parent integration and final review

**Files:** schedule_service.py, schemas/schedule.py if diagnostic additions; relevant docs, report diagnostics and regression tests; terminology in enums.py and client copy where applicable.

- [x] Review each task against spec and code, settle interface conflicts, request fixes from owning Sol agent.
- [x] Correct A/D terminology without changing actual flight arrival/departure metadata or inventing fixed hours.
- [x] Ensure generated/persisted/rechecked quotas agree, and manual edits update following-month warnings and effective turn history.
- [x] Run complete backend suite in isolated temporary SQLite database; inspect every failure; update obsolete expectations only when superseded by spec.
- [x] Run multi-month roster diagnostics showing working/X/CD/AL counts, A/D gap and per-kind turns for every member.
- [x] Run lint and final diff review; update this checklist with actual validation and any remaining limitations.

## Execution ledger

- 2026-11-15: User authorized plan plus implementation, Sol subagents, parent final review. Work on `codex/monthly-shift-fairness` in current clean checkout; no external side effects.
- Ruling: preserve existing leave/CD accounting, because the user changed ordinary work/rest scheduling rather than leave entitlements.
- Ruling: parallel implementation uses disjoint ownership; parent reviews integration. User explicitly requested Sol agents.

## Completion / verification

- Task1 report: `monthly-rest-report.md`; Task2: `rest-turns-report.md`; Task3: `optimization-report.md`. Parent reviewed interfaces and corrected service boundary warnings, approval accounting integration, and API proof diagnostics.
- Verification ran in isolated SQLite batches (not against dev.db): 36 regression test files passed; schedule/shift-change/history integration 48 cases passed; leave/attendance lifecycle75 cases passed; autorun/smoke/role-F15 cases passed. Focused agent suites and final consecutive/slack regressions supplement these batches.
- Changed Python files pass Ruff; git diff --check clean. Flutter changes are display strings only.
- Three-month synthetic audit: Feb2027 20 duties, March23, April22; ordinary rest8 days per member; A/D gaps0/1/0; no rule violations. March30-second run is feasible, not proven optimal; diagnostics explicitly retain this distinction.
- Ruling: role-group coverage precedes rest-turn awards to keep groups without flight minimums operational. Known next-month consecutive coverage precedes turn shaping.
- Ruling: chronological turn utility is ordered by opportunity; old global award maximization was rejected by an adversarial test where extra future awards could skip today's rightful recipient.
- Ruling: lazy objective construction finds a valid rule incumbent before building expensive chronological helpers. Dense9-person8-second benchmark has zero violations; lower fairness stages may remain unproven.
