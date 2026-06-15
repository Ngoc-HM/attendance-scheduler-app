# Phase 05 — F-07 / F-08 / F-09 Schedule Service (Generate, Manual Override, Publish, Day-20 Autorun)

## Context Links
- Spec: §4.4 / F-07, F-08, F-09, §5.6. Locked decisions 2,3,5.
- Files: `backend/app/services/schedule_service.py`, `backend/app/api/v1/endpoints/schedules.py`, `backend/app/schemas/schedule.py`, `backend/app/models/schedule.py`.

## Overview
- Priority: P1. Depends on 02 (flight_pairs), 03 (approved_off), 04 (engine).
- Bridge ORM ↔ engine: load inputs → SolverInput → solve → persist draft ShiftAssignment + return Violations; manual override with re-check; publish.

## Key Insights
- Holidays are working days (decision #5): do NOT add holidays to `approved_off`. Pass them as `SolverInput.holidays` for premium-off objective only.
- Engine is always-feasible (decision #2): `generate` persists assignments AND returns violations together (no hard "infeasible" path except input-validation contradictions).
- Manual override (F-09): always save (`is_manual_override=True`), re-run hard-rule checks on the edited cell, return warnings — do NOT block.
- A/D-fallback suggestion text comes from engine Violations (§5.6).
- Restore concrete codes on persist: decision-layer X may be approved AL/CD → write the real code from approved_off; engine A_D stays A/D.

## Requirements
Functional:
- `generate(year, month)`: load active users + carry_*; days; flight_pairs_map; approved_off_map; holidays set; build SolverInput; solve; upsert MonthlySchedule(draft) + ShiftAssignment rows; return ScheduleResult{assignments, violations, suggestions}.
- `get(year, month)`: return schedule + assignments.
- `manual_override(schedule_id, payload)`: update cell(s), flag override, re-check hard rules (exactly-one trivially ok; recompute consecutive/staffing/2-off for affected person/day), return warnings.
- `publish(schedule_id)`: status draft→published (locks edits).
- VISIBILITY (G4): non-admin `get` returns ONLY published schedules (404/empty for draft); admin sees both. Enforced here, re-tested in phase 10.
- `apply_shift_change(request)` (decision #8, called by phase-03 approve): change_code → update the cell; swap_with → exchange the two users' codes for that date; set `is_manual_override=True`; run `schedule_violation_checker`; return warnings (non-blocking). Works on draft or published (published edits audit-logged).
- DAY-20 AUTORUN (decision #9): APScheduler background job in app lifespan — on day 20 (configurable `AUTORUN_DAY=20`, `AUTORUN_ENABLED=true`), close M+1 registration implicitly (window logic, phase 03) and call `generate(M+1)` if no schedule exists yet (never clobbers an existing draft/published). Audit as actor=system.

Non-functional: generate idempotent per (year,month) (regenerate replaces draft, refuses if published unless forced).

## Architecture
Data flow: users+leaves+flights+holidays+carry → `build_solver_input()` → `SchedulerEngine.solve()` → `persist_assignments()` (map decision X→concrete AL/CD via approved_off) → ScheduleResult. Override: write cell → `recheck_hard_rules(person, month_assignments)` → warnings. Publish: status transition + audit (phase 10).

## Related Code Files
Modify:
- `backend/app/services/schedule_service.py` — implement get/generate/manual_override/publish.
- `backend/app/api/v1/endpoints/schedules.py` — wire (POST generate, GET, POST override, POST publish; admin-guarded).
- `backend/app/schemas/schedule.py` — ScheduleResult (assignments + violations + suggestions), ManualOverrideRequest (cells), confirm shapes.

Create:
- `backend/app/services/schedule_input_builder.py` — ORM→SolverInput mapping (<200 LOC, testable without solver).
- `backend/app/services/schedule_violation_checker.py` — re-check hard rules for manual override + shift-change apply (pure, reuses calendar_utils).
- `backend/app/services/schedule_autorun.py` — APScheduler job setup + day-20 trigger function (pure trigger logic testable without scheduler).

Modify (additional): `backend/app/core/config.py` — `AUTORUN_ENABLED`, `AUTORUN_DAY`; `backend/app/main.py` — start/stop scheduler in lifespan; `backend/requirements.txt` — `apscheduler`.

Delete: none.

## Implementation Steps
1. `schedule_input_builder.build(db, year, month)`: gather people (PersonInput with carry_comp/streak/premium_off), days, weeks (build_weeks), flight_pairs_map, approved_off_map, holidays set → SolverInput.
2. `generate`: build input → engine.solve → upsert MonthlySchedule(draft) → replace ShiftAssignment rows (map decision codes to concrete; A_D→A/D; pinned X→AL/CD from approved_off) → ScheduleResult with violations + A/D suggestions.
3. Guard: refuse regenerate if status=published (unless `force`).
4. `get`: fetch schedule + assignments.
5. `schedule_violation_checker.recheck(person_assignments, flight_pairs, weeks, carry_streak)`: returns warnings for consecutive>5, block X != target, staffing shortfall.
6. `manual_override`: apply cell edits, set is_manual_override, run recheck, return warnings (never block).
7. `publish`: status→published.
8. Wire endpoints + admin guard; audit override/publish (phase 10 adds audit calls).

## Todo List
- [ ] schedule_input_builder (ORM→SolverInput)
- [ ] generate: solve + persist draft + violations/suggestions
- [ ] regenerate guard vs published
- [ ] get
- [ ] schedule_violation_checker (override re-check)
- [ ] manual_override: save + warn (non-blocking)
- [ ] publish
- [ ] non-admin sees published only (G4)
- [ ] apply_shift_change (change_code + swap_with + re-check)
- [ ] day-20 autorun job (APScheduler, config-gated, never clobbers)
- [ ] wire + guard endpoints

## Success Criteria
- `generate` on a configured month persists draft assignments for every (user,day) and returns 0 violations when fully staffed.
- Under-staffed month → assignments still persisted + violations list non-empty + A/D suggestion present.
- Holidays appear as working days in output (not auto-X).
- `manual_override` setting a 6th consecutive working day saves AND returns a consecutive-rule warning.
- `publish` flips status; subsequent generate without force refused.

## Risk Assessment
- Input-builder contradictions (approved_off vs flight demand) (Med/Med) → validate pins pre-solve; surface as violation not crash.
- Concrete-code restore wrong (AL vs CD vs X) (Med/Med) → derive from approved_off_map source type; unit-test mapping.
- Regenerate clobbers manual edits (Med/High) → block regenerate after manual edits unless force; warn.

## Security Considerations
- Generate/override/publish admin-only. Override + publish audit-logged (phase 10).

## Next Steps
Unblocks phase 06 (attendance seeded from published schedule), 07 (calc reads assignments), 09 (schedule_page wiring).
