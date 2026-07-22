# Phase 06 — FE self-arrange tab (T & F) + admin approval panel

> REVISED 2026-07-09: propose-then-approve flow (owner decision b). Employee edits
> own row LOCALLY, submits ONE batch; admin approves in a pending panel on the
> admin schedule page (next to the existing shift-change panel).

## Context Links
- Plan: [plan.md](plan.md); blocked by [P02](phase-02-backend-self-arrange.md) + [P04](phase-04-fe-shell-routing.md)
- Reuse: `lib/features/schedule/...` datasource/provider patterns, `DsScheduleView`
- Endpoints: `POST /self-arrange`, `GET /self-arrange[?all=true]`, `POST /self-arrange/{id}/decide`

## Overview
Priority P2. Employee (T/F) tab: published month grid (full roster read-only, own
row toggleable X↔AD as local draft), live client quota hint, submit batch with
note → pending. Status list of own requests. Admin side: pending self-arrange
panel on schedule page with approve/reject.

## Requirements
- Month nav bounded T-n..T+2 (client mirror of server 403).
- Tap own cell toggles X↔AD locally (draft); client shows per-block off-count hint;
  Submit button POSTs `{year, month, changes, note}`; clear draft on 201.
- 422 (quota) / 409 / 403 errors surfaced via DsFeedback with server message.
- Own request history list (pending/approved/rejected badges).
- Admin: list pending self-arrange requests (requester code, month, #changes, note),
  approve/reject buttons; approve refreshes schedule grid.

## Related Code Files
**Create:**
- `lib/features/schedule/data/datasources/self_arrange_remote_datasource.dart`
- `lib/features/schedule/data/models/self_arrange_model.dart`
- `lib/features/schedule/presentation/providers/self_arrange_provider.dart`
- `lib/features/schedule/presentation/widgets/self_arrange_pending_panel.dart` (admin)
**Modify / finalize:**
- `lib/features/schedule/presentation/pages/self_arrange_page.dart` (stub from P04)
- `lib/features/schedule/presentation/pages/schedule_page.dart` — mount admin panel

## Implementation Steps
1. Model: SelfArrangeChange {workDate, code}; SelfArrangeRequest {id, requesterId,
   year, month, changes, status, note, decidedAt}.
2. Datasource: create/listMine/listAll/decide.
3. Provider: employee draft state (Map<date,code>), quota hint calc (7-day blocks
   anchored day 1, count X only), submit, load history; admin pending list + decide.
4. Page: month switcher (≤T+2), DsScheduleView-based grid; own-row tap toggle;
   draft chips + per-block indicator; note field; submit; history section.
5. Admin panel widget + mount in schedule_page (admin-only, like shift-change panel).
6. flutter analyze.

## Todo List
- [ ] models + datasource
- [ ] provider (draft + submit + history + admin decide)
- [ ] self_arrange_page finalize
- [ ] admin pending panel + schedule_page mount
- [ ] analyze

## Success Criteria
- T/F drafts a swap keeping 2X/block → submit 201 → appears pending; admin approves →
  employee reloads schedule and sees new codes.
- Draft breaking quota → client hint red + server 422 surfaced if forced.
- A never sees the tab (P04); admin sees pending panel with working approve/reject.

## Risk Assessment
| Risk | L×I | Mitigation |
|------|-----|-----------|
| Client quota calc drift vs server | Med×Low | Hint only; server authoritative both ends. |
| Draft lost on month switch | Med×Low | Confirm-discard dialog or auto-clear (KISS: auto-clear + toast). |
| Admin panel bloats schedule_page (>200 LOC) | Med×Low | Separate widget file; page only mounts it. |

## Security Considerations
- UI restrictions are UX; server re-validates ownership/quota/publish at create AND decide.

## Next Steps
Parallel with P07/P08 after P02+P04.
