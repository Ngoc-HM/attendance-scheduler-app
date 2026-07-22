# Phase 02 — Backend self-arrange BATCH request + admin approval + T+2 visibility

> REVISED 2026-07-09 after owner answers: self-arrange is NOT direct edit — employee
> submits a batch proposal, admin approves once more, then it applies to the
> published schedule. Mirrors existing shift-change flow but batched (a single
> cell change always breaks the weekly quota; only a SET of changes can keep it).

## Context Links
- Plan: [plan.md](plan.md); blocked by [P01](phase-01-backend-role-f.md)
- Pattern to mirror: `backend/app/services/shift_change_service.py`, `endpoints/shift_changes.py`
- Weekly-off check: `schedule_violation_checker.check_off_quota`; `calendar_utils.build_weeks/partial_block_off_target`
- Apply seam: `schedule_service.apply_shift_change` (study for cell-apply + recheck pattern)

## Overview
Priority P1. After publish, **T & F** (and M, though M normally uses admin override)
propose a rearrangement of their OWN cells as ONE batch: list of `{work_date, code}`.
Validation at submit AND at approve: every affected 7-day block keeps X-count ==
`partial_block_off_target` (AL/S/CD do not count — owner decision #3: only
regulation X counts). Admin approves → all cells applied atomically. Role A → 403.
Plus: non-admin GET schedule months capped at T+2.

## Requirements
- New model `SelfArrangeRequest`: id, requester_id FK, year, month, changes JSON
  `[{work_date, code}]`, status (LeaveStatus enum), note, decided_by_id, decided_at, timestamps.
- `POST /self-arrange` (ActiveUser): role.is_fixed → 403; month published required;
  every work_date in month + cell exists + owned; codes ∈ `codes_for(role)`;
  candidate own-row grid must keep X-count == target per affected block (422 otherwise);
  create pending request; audit `self_arrange.create`.
- `GET /self-arrange?all=` — own list; `all=true` admin-only (mirror shift_changes).
- `POST /self-arrange/{id}/decide` (AdminUser): pending-only guard; approve →
  RE-validate against current schedule (409/422 if stale/broken now), apply all cells
  (`is_manual_override=True`), commit, audit; reject → just status. Return warnings list.
- `GET /schedules/{year}/{month}`: non-admin, `idx(y,m) > idx(today)+2` → 403. Past unbounded.

## Related Code Files
**Create:**
- `backend/app/models/self_arrange_request.py`
- `backend/app/schemas/self_arrange.py` — Create/Read/Decision DTOs
- `backend/app/services/self_arrange_service.py` — create/list/decide + `_validate_quota`
- `backend/app/api/v1/endpoints/self_arrange.py`
- `backend/alembic/versions/0007_add_self_arrange_requests.py` (down_rev 0006)
**Modify:**
- `backend/app/models/__init__.py` — export model
- `backend/app/api/v1/router.py` — include router `/self-arrange`
- `backend/app/api/v1/endpoints/schedules.py` + `schedule_service.py` — T+2 guard
- `backend/app/core/i18n.py` — keys: forbidden_role, not_published, cell_not_found,
  invalid_code, breaks_weekly_off, month_out_of_range, already_decided, empty_changes

## Implementation Steps
1. Model + export + migration 0007 (JSON col works PG+SQLite).
2. Schemas: `SelfArrangeCreate {year, month, changes:[{work_date,code}], note?}`,
   `SelfArrangeRead` (+status, decided fields, warnings), `SelfArrangeDecision {status}`.
3. Service `create`: guards (fixed-role, published via `schedule_service.get(include_draft=False)`,
   ownership, domain, non-empty, dedupe dates); `_validate_quota(own_row_grid, changes, weeks)`
   reusing `partial_block_off_target`; persist pending.
4. Service `decide`: pending guard; on approve re-run validation, locate cells, set codes
   + `is_manual_override`, commit; warnings from full `recheck` (info only, admin confirmed).
5. Endpoints mirroring shift_changes (own list / admin all / decide + audit).
6. T+2 guard in `get_schedule` (non-admin only).
7. i18n keys en/vi; compile import check.

## Todo List
- [ ] model + migration 0007
- [ ] schemas
- [ ] service create + quota validation
- [ ] service decide + apply + revalidate
- [ ] endpoints + router + audit
- [ ] T+2 guard
- [ ] i18n keys
- [ ] compile check

## Success Criteria
- T/F batch keeping 2-X/block → 201 pending; admin approve → cells applied, audit rows.
- Batch breaking any block quota → 422 at submit; approve after schedule changed → 409/422, not applied.
- A → 403. Unpublished month → 404. Non-admin GET T+3 → 403 (admin unrestricted).
- Ownership: token-derived requester; cells of others untouchable.

## Risk Assessment
| Risk | L×I | Mitigation |
|------|-----|-----------|
| Stale approval (schedule edited between submit/approve) | Med×Med | Re-validate at decide; fail loud, employee resubmits. |
| JSON changes column abuse (huge list) | Low×Low | Cap changes ≤ 62 (2×31); validate each entry. |
| Quota math drift vs solver | Low×Med | Reuse `partial_block_off_target` + only-X counting (matches checker + owner #3). |
| Double-apply on repeated decide | Low×Med | Pending-only guard (mirrors shift_change idempotency). |

## Security Considerations
- Token-derived requester_id; fixed roles blocked; published-only; both create & decide audited.
- Changes validated server-side at BOTH ends; client hints are UX only.

## Next Steps
Unblocks P06 (employee propose UI + admin approval panel).
