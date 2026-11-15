# Task 3 — ordered monthly fairness

Implemented `objective_balance.py`, `objectives.py`, `engine.py`, and new
`optimization.py`, plus focused balance, optimization, phase and reserve tests.
No database writes, new dependency, worktree or commit.

## Final priority order

1. Existing weighted diagnostic rule slack, including the new monthly quota.
2. Descending individual monthly `abs(A-D)` gaps for **every** role-A rank.
3. Aggregate A/D gap, then cross-person A/D total spread.
4. Operational role-group cover; known next-month consecutive-work cover.
5. Independent chronological turn stages supplied by Task 2.
6. Reserve, premium-off and pair-shaping preferences.

Each achieved integer objective is fixed before a lower stage. There is no
combined-weight fallback. Initial UNKNOWN retries the rule objective alone;
later UNKNOWN preserves the last incumbent. `optimal` requires every stage to
be proven optimal; phase diagnostics expose each status, value, bound, proof
flag and solve seconds. Monthly-off and weekly-debt soft weights are removed.

Rule search builds only base constraints. Remaining objective helpers are added
**after** its incumbent, and hints are captured before the new variables exist.
This matters: with all turn helpers built eagerly, the 8-second review case's
first search took 3.188 seconds and stopped FEASIBLE with weighted slack 774000
and 49 violations. The same base model without those helpers proved zero slack
in 0.0756 seconds. The lazy construction fixes the actual failing regression.

## Verification

Tests use `env -u DATABASE_URL backend/.venv/bin/pytest`; conftest creates an
isolated temporary SQLite database.

- Initial balance TDD: 5 failures for missing ordered fairness -> 5 passed.
- Initial ordered solver TDD: missing module ->4 passed (strict priority,
  incumbent retention, rule-only retry, shared deadline).
- Existing nonflight all-group-off regression reproduced -> passed after
  moving operational group cover above turns.
- Broad final-stage run before lazy-build fix: 47 passed, 1 failed in 48 tests.
  Files: `test_engine_objectives.py`, `test_engine_staffing.py`,
  `test_engine_roles.py`, `test_engine_reserve_cover.py`,
  `test_engine_solve_phases.py`, `test_objective_balance_ordered.py`,
  `test_ordered_optimization.py`, `test_engine_rest_pairs.py` (with
  `-k 'not pair_points'`). The sole failure was
  `test_one_worker_finds_zero_slack`; fixed by lazy objective construction.
- After final lazy-build fix: **15 passed** across
  `test_ordered_optimization.py`, `test_objective_balance_ordered.py`, and
  `test_engine_solve_phases.py`, including the actual 8-second regression and
  a RED->GREEN helper-construction regression. Parent owns the full suite.
- Ruff passes all 8 owned source/test files (the 4 source files and
  `test_objective_balance_ordered.py`, `test_ordered_optimization.py`,
  `test_engine_solve_phases.py`, `test_engine_reserve_cover.py`).

The reserve test's former demand for 3 workers on every Friday is superseded
by the binding turn-before-reserve order. It now verifies demand floors,
zero violations and all 8-X entitlements while reserve yields to genuine
Friday/Saturday turns.

## Actual single-worker benchmarks, final code

| Input | Budget | Elapsed | Result | Rules | A/D fairness |
|---|---:|---:|---|---|---|
| 4 role-A, Feb 2027; 1 pair/day, 2 on Wednesdays | 30s | 2.593s |optimal, all 20 stages proven |zero violations |everyone 10A/10D/8X, gap 0 |
| 9 people, Dec 2026; M/T/F/A roles, holidays, carry | 8s | 8.049s |feasible, all 22 stages attempted |zero violations, slack proven minimal |all 5 individual ranks proven: 1/1/1/0/0 |

The review case gives every user 8X and uses carried CD for users 3, 6, 9.
Role-A users 5..9 have (A,D) totals (11,12),(11,11),(12,11),(11,12),(11,11).
Many lower review-case stages remain FEASIBLE rather than proven; diagnostics
and overall status retain that distinction.

## Limitations and rulings

- A finite budget cannot guarantee every preference or even every higher
  objective reaches its mathematical optimum. Achieved values are protected;
  unproven values remain explicitly unproven. A lower stage never buys worse
  achieved rule slack or fairness.
- Rules receive an initial 40% of remaining budget; later stages share the
  remainder equally, reusing time saved by earlier stages. All construction,
  hint work and searches use one deadline. CP-SAT teardown/extraction can
  exceed it slightly (49 ms in the 8s benchmark); it is not a real-time cutoff.
- Sorting covers all ranks with quadratic comparator helpers. Per-date turns
  add stages, so larger groups/months may stop with a valid but incompletely
  optimized incumbent. No top-three cutoff or unsafe combined fallback.
- Operational group cover precedes turns because maximizing awards first
  otherwise lets nonflight role groups all rest together. Known-demand
  consecutive lookahead also precedes turns, so turn choices cannot spend
  already-achieved boundary cover. Unknown next flights create no demand.
