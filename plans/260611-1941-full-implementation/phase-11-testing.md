# Phase 11 — Testing (pytest engine/services/endpoints + Flutter widget tests)

## Context Links
- Dev rule: NO fake data/mocks-to-pass; real implementations; do not ignore failing tests.
- Existing: `backend/tests/{test_auth_users,test_calendar_utils,test_health,test_scheduler_smoke}.py`, `conftest.py`.

## Overview
- Priority: P1. Depends on phases 02–10.
- Prove every hard constraint binds AND that slack reports a violation; cover services, endpoints, RBAC; Flutter widget tests for wired pages.

## Key Insights
- Always-feasible engine (decision #2): each hard rule needs TWO tests — (a) feasible scenario → rule satisfied with 0 slack; (b) impossible scenario → solution still returned, slack>0, Violation reported.
- calendar_utils tests must be updated to 7-day-block semantics (phase 01 changed them).
- Use real SQLite/Postgres test DB per conftest; no mocking the DB (per dev rules).

## Requirements
Engine (per constraint):
- exactly-one-status: every cell has one code.
- two-X-per-block: feasible → each block has target X; over-constrained → slack reported.
- max-consecutive: no 6-run feasible; carry_streak boundary forces early X; impossible → slack.
- staffing: demand met from A1-A4 incl. A/D substitution; short-staffed → slack + A/D suggestion.
- balance: spread minimized; A/D balanced across A1-A4.
- weekend pairing: prefers Sat+Sun.
- premium-off: spread reduced given uneven carry.

Services: flight derivation, leave windows/classification/conflict rank (incl. days-1–20-of-M-for-M+1 window, decision #10), shift-change create/approve/swap apply + strict_review flag (decision #8), schedule generate/override/publish + draft-invisible-to-non-admin, day-20 autorun trigger (pure function: fires on day 20, skips if schedule exists, decision #9), sick backfill, holiday CRUD (not auto-off), carry-over math idempotency (re-run identical), report assembly + serializers.

Endpoints: happy-path + RBAC (403 for non-admin/other-user), sick masking.

Flutter: widget tests that each wired page renders provider state and triggers the right usecase (mock the datasource boundary only, not business logic).

## Architecture
Backend: pytest fixtures build minimal real scenarios (small people/days sets) → assert solver output / service results. Flutter: `flutter_test` with fake datasource returning canned API payloads.

## Related Code Files
Create (backend, kebab/snake):
- `backend/tests/test_engine_off_days.py`
- `backend/tests/test_engine_consecutive.py`
- `backend/tests/test_engine_staffing.py`
- `backend/tests/test_engine_objectives.py` (balance/weekend/premium-off)
- `backend/tests/test_engine_slack_violations.py` (each over-constrained → violation)
- `backend/tests/test_flight_service.py`
- `backend/tests/test_leave_service.py`
- `backend/tests/test_shift_change_service.py`
- `backend/tests/test_schedule_service.py` (incl. autorun trigger + visibility)
- `backend/tests/test_attendance_sick.py`
- `backend/tests/test_calculation_service.py`
- `backend/tests/test_report_service.py`
- `backend/tests/test_rbac_audit.py`
Create (Flutter):
- `test/features/{flights,leaves,schedule,attendance,reports}/*_page_test.dart`

Modify:
- `backend/tests/test_calendar_utils.py` — 7-day-block expectations.
- `backend/tests/test_scheduler_smoke.py` — align with new engine signature.

## Implementation Steps
1. Update calendar_utils + smoke tests for new semantics.
2. Write per-constraint engine tests (bind + slack pair each).
3. Write objective tests (assert improved spread vs baseline).
4. Service tests (real DB fixtures).
5. Endpoint + RBAC + sick-masking tests.
6. Flutter widget tests per wired page.
7. Run full suite; fix failures (no skipping).

## Todo List
- [ ] Update calendar_utils + smoke tests
- [ ] Engine off-days tests (bind + slack)
- [ ] Engine consecutive tests (bind + slack + carry_streak)
- [ ] Engine staffing tests (bind + slack + A/D)
- [ ] Engine objective tests (balance/weekend/premium)
- [ ] Service tests (flight/leave/schedule/sick/calc/report)
- [ ] Endpoint + RBAC + sick-masking tests
- [ ] Flutter widget tests per page
- [ ] Full suite green

## Success Criteria
- Every hard constraint has a passing bind-test and a passing slack-reports-violation test.
- All service/endpoint tests pass against a real test DB.
- RBAC: non-admin 403 cases pass; sick masked for non-admin.
- `flutter test` passes for all wired pages.
- No skipped/xfail used to hide real failures.

## Risk Assessment
- Solver nondeterminism flakiness (Med/Med) → assert invariants (counts, no-6-run), not exact assignments; fixed random seed + time limit.
- Slow solver in CI (Med/Med) → tiny scenarios (≤5 people, ≤10 days).
- DB fixture leakage (Med/Low) → transactional rollback per test.

## Security Considerations
- Tests assert the §9 access controls (RBAC, sick masking) — security is test-verified, not assumed.

## Next Steps
Green suite gates phase 12 docs + any release.
