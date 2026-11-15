# Task 1: monthly quota and rest replacement

Implemented in the shared checkout without commits or external side effects.

## Behavior and interfaces

- `constraints_monthly_quota.add(model, x, inp, registry)` replaces weekly quotas for every scheduler role. Exact ordinary X entitlement is diagnostic-capable: `monthly_off_shortfall` / `monthly_off_excess`, with `target` and `amount` parameters. Both use the standard rule slack priority.
- `objective_monthly_off_target.target(inp, user_id)` remains compatible. Shared `entitlement(days, pinned)` computes weekends minus approved leave on weekend dates. Weekday approved leave does not consume ordinary X; generated CD is additional rest. Public-holiday compensation is unchanged.
- `recheck(..., approved_off=None)` adds an optional trailing keyword. Persisted AL/S cells and approved persisted CD cells supply effective leave accounting. Persisted ordinary X remains ordinary X even inside an approved request span, because approval of an existing roster preserves its X cells. The service should continue passing the full `leave_service.approved_off_map(...)`; no filtering at the caller is required.
- Approved CD is counted exactly once in compensation accounting, including after the solver's X placeholder is restored to CD. This fixes an existing solver/recheck mismatch rather than changing CD entitlement.
- `constraints_weekly_rest.add` and `check_weekly_rest` remain compatibility no-ops. No Mon–Sun or rolling-seven working quota is enforced. Existing max-five-consecutive work constraints, including carried runs, remain active.
- `objective_boundary_week.terms` retains its interface but now projects only consecutive-work protection over the first five days of next month. It penalizes projected staffing shortages only for explicit known next-month flight data. It neither creates weekly rest debt nor copies flight demand from previous weekdays. Actual next-month leave and quotas remain the next generation's responsibility.
- English/Vietnamese diagnostics use ordinary shift labels A and D, with monthly quota messages. Actual flight metadata labels remain unchanged.

## Test-first evidence

The initial new quota test run showed seven real assertion failures: a legal one-rest/three-rest-week pattern still reported weekly slack, all four month lengths had no monthly excess warning, missing X had no shortfall warning, and pinned CD disagreed after persistence. All were fixed. A preserved weekday-X approval-span test then reproduced a false shortfall before the persisted-code accounting fix. Three boundary projection tests failed against the old weekly-debt look-ahead before replacement.

## Validation

All commands use `env -u DATABASE_URL .venv/bin/python -m pytest ...` from `backend`, so conftest creates an isolated temporary SQLite database.

- 44 tests passed together: `test_monthly_quota.py` (12), `test_engine_boundary_week.py` (4), `test_violation_checker.py` (7), `test_violation_text.py` (11), `test_leave_staffing.py` (10).
- A broader run also completed four seeded solver/persisted-grid agreement tests and six compensation tests successfully, including random manual edits.
- Cross-month tests had one obsolete fixture: `test_off_chain_crosses_month_boundary` supplied nine X when August 2026 owes ten. It now adds X on August 31, preserving the boundary-off-run focus; the corrected targeted test passed. The other six cross-month tests passed in the broader run.
- The rest half of `test_engine_weekly_rest_and_turns.py` passed after replacing weekly assertions. Two old scalar-pair-point fairness tests failed under the new independent-kind model: `test_turns_with_memory` and `test_the_leader_yields_to_the_middle_when_the_lowest_is_capped`; Task 2 owns their migration.
- Ruff passed over every owned production/test file. `git diff --check` passed.
- In total, 61 focused test cases were covered in the broad run: 60 passed and the obsolete August fixture failed; its corrected targeted rerun passed. This is not a claim that the entire broad run passed. The redundant service tail was interrupted at the parent's request to reduce duplicate CPU load; final service and full-suite integration are owned by the parent.

Only the existing Starlette/httpx TestClient deprecation warning was observed in focused green runs. No third-party dependency was added.
