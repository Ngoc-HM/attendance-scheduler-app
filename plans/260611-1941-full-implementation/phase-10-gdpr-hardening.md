# Phase 10 — GDPR / §9 Hardening (Sick Access, Audit, RBAC)

## Context Links
- Spec: §9 (all): §9.1 sick = special-category, §9.2 Betriebsrat, §9.3 minimization, §9.4 EU region, §9.5 audit/RBAC/backup, §9.6 no-AI.
- Files: `backend/app/core/security.py`, `backend/app/models/audit.py`, all endpoints, `backend/app/services/*`.

## Overview
- Priority: P1 (legal compliance, Germany/EU). Depends on 06 (S handling exists).
- Enforce role-based access, restrict sick-data access to admin via separate path, audit-log admin actions, document EU-region + no-AI posture.

## Key Insights
- AuditLog model exists (actor_id, action, entity, entity_id, detail) — wire it, currently unused.
- §9.1: S = health data → admin-only read/write; separate query path; no medical reason stored (model already omits reason).
- §9.5: users see ONLY own data; admins full; audit admin actions; backup/restore = ops doc.
- §9.6: engine is rule-based; assert no ML scoring (document in code + docs).
- §9.2 Betriebsrat = OPEN QUESTION (blocks production deploy if present) — flag, don't block dev.

## Requirements
Functional:
- RBAC dependency: `require_admin` and `require_self_or_admin` FastAPI deps applied across endpoints.
- Sick-data access: a dedicated admin-only path for reading S records; normal schedule/attendance reads mask S for non-admin.
- Audit: every admin mutation (schedule override/publish/generate, leave approve/reject, SHIFT-CHANGE approve/reject, attendance status update incl. S, holiday CRUD, flight import, report export) writes an AuditLog row; autorun generate audited as actor=system.
- Shift-change RBAC: create = own cells only (403 on others'); decide = admin-only. Draft schedules invisible to non-admin (verify phase-05 G4 rule with tests).
- Config: assert EU region note; TLS/at-rest = deployment doc (phase 12).

Non-functional: audit write must not break the main action (best-effort, logged).

## Architecture
Data flow: request → auth dep resolves user+role → RBAC dep authorizes → service runs → audit hook records actor/action/entity. Sick reads routed through `sick_data_access` guard.

## Related Code Files
Modify:
- `backend/app/core/security.py` — add `require_admin`, `require_self_or_admin` deps.
- All `backend/app/api/v1/endpoints/*.py` — apply RBAC deps; add audit calls on admin mutations.
- `backend/app/services/attendance_service.py` — separate sick-read path; mask S for non-admin reads.

Create:
- `backend/app/services/audit_service.py` — `record(actor_id, action, entity, entity_id, detail)` (<100 LOC).
- `backend/app/core/rbac.py` — reusable role guards if security.py grows >200 LOC.

Delete: none.

## Implementation Steps
1. `audit_service.record(...)` best-effort writer.
2. RBAC deps in security.py (or rbac.py): admin-only, self-or-admin.
3. Apply RBAC to every endpoint: users read-own; admin mutations admin-only.
4. Sick: admin-only read path; non-admin attendance/report reads mask S → generic "off"/hidden.
5. Insert audit calls at admin mutation points (schedule, leave, attendance/S, holiday, flight import, report export).
6. Add config flag/comment documenting EU region + no-AI.

## Todo List
- [ ] audit_service.record
- [ ] require_admin / require_self_or_admin deps
- [ ] apply RBAC across all endpoints
- [ ] sick-data admin-only path + non-admin masking
- [ ] audit hooks on all admin mutations
- [ ] EU-region + no-AI config/doc note

## Success Criteria
- Non-admin GET on another user's data → 403; own data → 200.
- Non-admin cannot read S; admin can via dedicated path.
- Each admin mutation produces an AuditLog row (actor, action, entity).
- Audit failure does not abort the underlying action.

## Risk Assessment
- Missed endpoint left unguarded (Med/High) → checklist all routes; phase 11 adds RBAC tests per route group.
- Over-masking breaks legitimate admin views (Med/Med) → role-conditional masking, test both roles.
- Betriebsrat unresolved (Low/High legal) → OPEN QUESTION; deployment gate, documented.

## Security Considerations
- This phase IS the security phase. Encryption in transit/at rest + EU region + DPA = deployment doc (phase 12), not code.

## Next Steps
Feeds phase 11 (RBAC/audit tests) and phase 12 (compliance docs).
