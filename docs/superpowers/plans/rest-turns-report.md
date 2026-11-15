# Task 2: chronological independent preferred-rest turns

## Changes

- Added frozen `RestTurnHistory(count=0, last_date=None)` and optional `PersonInput.rest_turns`, keyed by first weekday 4/5/6. `last_date` is always the pair's **second/completion day**. Preserved scalar legacy fields; an aggregate 3:2:1 point history cannot be meaningfully converted to independent histories and is not used by the new turn objectives.
- Effective history reads two SELECTs for the entire roster: actual X, then planned X with no actual row. Actual non-X overrides break a planned pair. Only genuine adjacent X+X counts; AL/CD do not. A pair belongs to the month/window containing its second day. The preceding twelve calendar months are read plus one left-edge day, excluding incomplete pairs that finish in the target month. Regeneration and manual/actual corrections are reconstructed rather than accumulated.
- Parent assembled `rest_turn_history` and builder wiring while execution was resumed. This task added verification, completion-date consistency and function documentation/types. Builder passes the histories plus compatible legacy values and reads five next-month days for maximum-five-work-run lookahead.
- Replaced rank-capped aggregate pair points with ordered chronological opportunities. For each kind in Fri+Sat, Sat+Sun, Sun+Mon order, each date has its own objective stage. A person's running count and last date use history plus their own earlier same-kind awards in the current solve.
- A candidate's rank counts same-role eligible peers who outrank it, comparing fewer prior awards first and oldest completion date second. Positive superincreasing rank rewards make one higher rank beat all lower-rank recipients together at that opportunity. Every rank participates. Positive rewards prevent a no-award solution when any award remains feasible at the earlier fixed priorities. For unusually large groups, per-rank stages replace powers that would exceed the CP-SAT integer safety bound.
- Added additive `SolverOutput.phase_diagnostics` for the optimization agent's named-stage diagnostics. Engine/objectives are owned by that agent.

## Evidence

TDD observed missing turn/history functionality, then green tests. A specific adversarial regression first failed with month-total award maximization: giving the oldest eligible peer this Friday precludes two later awards; the old objective skipped that peer to collect three awards. Per-date ordered stages now select that peer this Friday, sacrificing later awards as required.

Final focused command:

```
backend/.venv/bin/pytest backend/tests/test_rest_turns.py backend/tests/test_rest_turn_history.py backend/tests/test_pair_points_history.py backend/tests/test_engine_weekly_rest_and_turns.py -q
```

Result: **25 passed**. Covers six-person chronology; counts before recency; same-month memory; peer absence; independent kinds; no-award degeneracy including an infeasible higher-priority candidate; fifth/sixth ranks after unavailable lower ranks; a seventeen-member overflow fallback; next-month turn priority; actual/planned precedence; regeneration; AL/CD exclusion; both window edges; boundary award ownership; zero-history users; two-statement history reads; input-builder wiring; and full-month three-person solver rosters with and without history. Legacy scalar carry and aggregate-points assertions were migrated to independent Fri+Sat counts and realistic chronological dates.

```
backend/.venv/bin/ruff check backend/app/scheduler/domain.py backend/app/scheduler/objective_pair_points_fair.py backend/app/services/schedule_history.py backend/app/services/schedule_input_builder.py backend/tests/test_rest_turns.py backend/tests/test_rest_turn_history.py backend/tests/test_engine_weekly_rest_and_turns.py
```

Result: **All checks passed**. Tests use isolated temporary SQLite through the existing test fixture; new history tests use their own in-memory SQLite. No live database writes. The only test warning is the existing Starlette/httpx deprecation. Whole-backend verification and integrated multimonth roster audit belong to the parent integration step.

## Mathematical scope and limitations

- Chronology is an objective hierarchy, not hard greedy allocation: staffing, rule/quota slack, A/D balance and configured group-cover objectives can make a turn infeasible or force a different recipient. Unavailability does not change historical counts or consume a turn.
- Candidate eligibility excludes pinned leave and incompatible known boundary cells. Other restrictions are resolved jointly by CP-SAT against the complete month, rather than guessed by a local availability test.
- Equally ranked recipients can be permuted; later stages may choose among equally good earlier-stage solutions. A higher earlier turn score cannot be purchased by later extra pairs, or substituted by a different kind.
- Extra chronological stages consume the same single global solver deadline. A timed-out run may retain a feasible incumbent before all future opportunities have been optimized; engine diagnostics must report that fact, rather than claiming full chronological optimality. Typical months add roughly 12–15 turn stages; unusually large groups may require more rank stages.
- Historical memory is intentionally rolling twelve months; an old award disappears when its completion date leaves that window. An absent/unknown last date is treated as the longest wait. No individual rank is dropped or clamped.
- The legacy `terms(...)` wrapper remains source compatible but a caller summing those expressions cannot reproduce an ordered hierarchy. The production engine must call `ordered_terms(...)`, as integrated by the optimization agent.
