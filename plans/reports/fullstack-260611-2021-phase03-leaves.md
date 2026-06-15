# Phase 03 Implementation Report — F-05/F-06 Leaves + Shift-Change Requests

## Executed Phase
- Phase: phase-03-leaves
- Plan: /Users/hmngoc/project/attendance-scheduler-app/plans/260611-1941-full-implementation/
- Status: completed

## Files Modified
| File | Action | Notes |
|------|--------|-------|
| `backend/app/services/leave_service.py` | Modified | Full impl replacing NotImplementedError stubs |
| `backend/app/api/v1/endpoints/leaves.py` | Modified | Replaced 501 stubs; added GET /conflicts endpoint |
| `backend/app/schemas/leave.py` | Modified | Added ConflictEntry schema; made leave_type optional in LeaveCreate |
| `backend/app/api/v1/router.py` | Modified | Added single import + include_router for shift_changes |

## Files Created
| File | LOC | Notes |
|------|-----|-------|
| `backend/app/services/leave_windows.py` | 52 | Pure window/classify logic, no DB |
| `backend/app/services/leave_conflict_resolver.py` | 44 | Pure ranking by carry_comp, no DB |
| `backend/app/services/shift_change_service.py` | 131 | Create/list/decide with lazy schedule seam |
| `backend/app/api/v1/endpoints/shift_changes.py` | 64 | POST / GET / POST /{id}/decide |
| `backend/app/schemas/shift_change.py` | 43 | ShiftChangeCreate/Decision/Read with strict_review + warnings |
| `backend/tests/test_leave_service.py` | 199 | Pure unit + integration tests |
| `backend/tests/test_shift_change_service.py` | 176 | Integration tests for all business rules |

## Tasks Completed
- [x] leave_windows: classify (4 days monthly, 5+ annual) + window checks (days 1-20; prior-year annual)
- [x] create_request with window enforcement + overlap guard
- [x] list_for_user / list_all / list_pending / decide (approve/reject)
- [x] conflict resolver (carry_comp ranking + stable tie-break)
- [x] approved_off_map for scheduler input (AL codes, month-clipped)
- [x] annual_leave_balance decrement on approval; 400 if insufficient
- [x] shift_change_service: create/list/decide + strict_review derivation
- [x] Lazy phase-05 seam: getattr(schedule_service, "apply_shift_change", None); NotImplementedError → warning
- [x] shift_changes endpoints + schemas (strict_review + warnings in response)
- [x] Idempotency guards: re-decide → 409 (leave.already_decided / swap.already_decided)
- [x] Wire shift_changes router (single import + include_router in router.py)

## Tests Status
- Compile check: PASS (`import app.main` clean)
- Unit tests (pure): PASS — classify boundary, window open/closed, annual prior/same year, conflict ranking
- Integration tests: PASS — balance decrement, approved_off_map AL codes, overlap 409, window day-21 400, shift-change create/missing-fields/strict-review/approve-warning/re-decide-409
- Pre-existing tests: PASS (all 58 tests pass, 0 failures)

## Business Rules Implemented
- Registration cycle #10: monthly window days 1-20 of M for M+1; outside → 400 leave.window_closed_monthly
- Classification: span >= 5 → annual; < 5 → monthly (caller-supplied leave_type overridden)
- Annual window: submission must be in calendar year before leave start year
- Sick (S) not handled here per GDPR §9.1
- approved_off_map: AttendanceCode.AL only; CD not generated here
- Balance: decrement on approve; 400 leave.balance_insufficient if short; restore not auto-triggered on reject (admin-only flow)
- Conflict resolver: advisory, carry_comp desc, stable tie-break by created_at then id
- Shift-change: change_code requires requested_code; swap_with requires counterpart_user_id
- strict_review = requester.role.is_fixed (A1-A4 = True, M/T = False)
- Schedule seam: getattr + NotImplementedError catch → "schedule application pending" in warnings

## Issues Encountered
- SQLAlchemy mapped models can't be instantiated via `__new__` in unit tests; fixed by using `types.SimpleNamespace` for pure conflict-rank tests.
- `UserUpdate` schema doesn't expose `annual_leave_balance`; integration tests set it directly via DB session instead of PATCH endpoint.

## Next Steps
- Phase 05 unblocked: implement `apply_shift_change` in schedule_service.py to fulfil the seam.
- Phase 09 unblocked: leaves_page wiring can now call real endpoints.
- Balance restore on reject of approved leave: current flow only allows decide() on pending requests (idempotency guard). If admin needs to revoke an approved request, a cancel/revoke endpoint should be added in a later phase.

**Status:** DONE
**Summary:** All 9 phase-03 tasks implemented; 58/58 tests pass including 27 new tests covering all specified business rules. Compile clean.
**Concerns:** Balance restore on already-approved-then-rejected path not exposed via HTTP (only pending→rejected is guarded). The `revoke_balance_on_reject` helper exists in leave_service.py for future use.
