# Phase 09 — Testing & validation

## Context Links
- Plan: [plan.md](plan.md); depends on ALL phases
- Backend tests: `backend/tests/` (pytest; SQLite via `conftest.py`). Existing: `test_engine_roles.py`, `test_engine_off_days.py`, `test_engine_consecutive.py`, `test_schedule_service.py`, `test_rbac_audit.py`, `test_auth_users.py`, `test_demo_user_seed.py`, `test_calendar_utils.py`
- Frontend: `flutter analyze`

## Overview
Priority P1 (gate). Status pending. Prove role F exemption, self-arrange auth +
weekly-off blocking, time-clock lifecycle, visibility guard; keep existing suite
green; `flutter analyze` clean.

## Key Insights
- Tests use SQLite create_all → schema reflects current models incl F + time_clock without running alembic; alembic parity verified separately (Postgres) or via smoke.
- Reuse engine test patterns for F.

## Requirements (test matrix)
| Area | Type | Cases |
|------|------|-------|
| Role F engine | unit | F domain={AD,X}; F respects weekly-2-off; F NOT flagged for >5 consecutive working; F excluded from staffing/comp |
| F seed | unit | demo seed creates F users w/ code F# |
| Self-arrange | integration | T/F edit own published cell ok; A→403; unpublished→404; other-user body ignored; weekly-off break→422 (not saved); audit row written |
| Visibility | integration | non-admin GET T+3→403; T+2/T/T-n published→200; draft→404 |
| Time-clock | integration | check-in sets time; 2nd check-in→409; check-out needs check-in (409 else); GET /me own-only |
| Migrations | smoke | `alembic upgrade head` then `downgrade` (0006) on scratch PG; 0005 adds enum value |
| Regression | suite | full existing pytest green |
| Frontend | static | `flutter analyze` 0 errors |

## Related Code Files
**Create:**
- `backend/tests/test_engine_role_f.py`
- `backend/tests/test_self_arrange.py`
- `backend/tests/test_time_clock.py`
- `backend/tests/test_schedule_visibility.py`
**Modify (if needed):**
- `backend/tests/test_demo_user_seed.py` — expected F users.

## Implementation Steps
1. Delegate to `tester`: run `pytest` in `backend/` (venv). Fix failures per recommendations, re-run until green.
2. Add new test files above; assert exemptions & auth precisely.
3. Migration smoke: on a scratch Postgres, `alembic upgrade head` + `alembic downgrade -1` (drops time_clock); confirm 0005 enum add idempotent (`IF NOT EXISTS`).
4. `flutter analyze` in `attendance_scheduler_app/`; fix analyzer issues.
5. Manual smoke: log in as F demo user → 4 tabs; self-arrange swap; check-in/out; A user has no self-arrange tab.

## Todo List
- [ ] existing pytest green
- [ ] test_engine_role_f
- [ ] test_self_arrange
- [ ] test_time_clock
- [ ] test_schedule_visibility
- [ ] demo seed test updated
- [ ] alembic up/down smoke (PG)
- [ ] flutter analyze clean
- [ ] manual smoke (F/A roles)

## Success Criteria
- All pytest pass (existing + new). `flutter analyze` 0 errors. Migrations up/down clean. Manual smoke matches requirements 1–6.

## Risk Assessment
| Risk | L×I | Mitigation |
|------|-----|-----------|
| Existing tests assume roles {M,T,A} exact | Med×Med | Update expectations for F seed; keep F additive. |
| SQLite passes but PG enum migration fails | Med×High | Explicit PG alembic up/down smoke step (not just SQLite). |
| flaky solver timing in F test | Low×Low | Small fixture; assert on codes/violations, not runtime. |

## Security Considerations
- Assert negative auth paths (A self-arrange 403, cross-user body ignored, T+2 guard, clock /me isolation) — security IS the test target.

## Next Steps
Final gate → `code-reviewer`; then `docs-manager` updates `docs/system-architecture.md` + changelog (role F, self-arrange, time-clock, employee shell).

## Unresolved
- Confirm conftest builds schema via create_all (assumed) — verify at P09 start; if alembic-based, run migrations in test setup.
