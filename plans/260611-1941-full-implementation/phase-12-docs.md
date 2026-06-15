# Phase 12 — Docs (README Override Notes + docs/ Suite)

## Context Links
- documentation-management.md: maintain `docs/` suite + roadmap + changelog.
- Decisions to record: #5 holiday-as-workday override, #7 week-model change, #2 always-feasible/slack architecture.
- Files: repo `README.md`, `backend/.../README*`, `attendance_scheduler_app/lib/design_system/README.md`, new `docs/`.

## Overview
- Priority: P2. Depends on 01–11 (documents what was built).
- Update README status; create/update docs suite; record design-decision overrides; deployment/compliance notes.

## Key Insights
- Spec F-13/§7 said PH = OFF; we OVERRODE to PH = working day (decision #5). README/docs MUST note this divergence explicitly so future devs don't "fix" it back.
- Week model changed Monday-anchored → 7-day blocks (decision #7) — document + confirm-with-customer flag.
- Always-feasible slack architecture (decision #2) is non-obvious; document so violations aren't mistaken for bugs.
- §9.4 EU region + DPA + TLS/at-rest = deployment doc (not code).

## Requirements
Functional:
- Update root README: feature status F-01..F-15 (done), run/deploy quickstart, the holiday + week overrides.
- Create docs suite per documentation-management.md.
- Record design decisions with rationale.

## Architecture
Docs reflect final system: architecture diagram (FastAPI + CP-SAT engine + Postgres + Flutter), data flow (flights+leaves+holidays+carry → engine → schedule → attendance → calc → reports), compliance posture.

## Related Code Files
Modify:
- `README.md` (root) — status + overrides + quickstart.

Create (`docs/`):
- `docs/system-architecture.md` — components, data flow, engine model summary, slack/violation design.
- `docs/code-standards.md` — conventions (kebab-case, <200 LOC, clean-arch Flutter, service/engine split).
- `docs/codebase-summary.md` — module map (backend services/engine, Flutter features).
- `docs/development-roadmap.md` — phases + status from this plan.
- `docs/project-changelog.md` — features delivered this cycle.
- `docs/design-decisions.md` — holiday-as-workday (#5), 7-day week blocks (#7), always-feasible slack (#2), no-AI (§9.6), premium-off fairness (#6), shift-change requests (#8), day-20 autorun (#9), leave cycle days 1–20 of M for M+1 (#10).
- `docs/deployment-guide.md` — EU region (Frankfurt), DPA, TLS/at-rest, backup/restore, Betriebsrat gate (§9.2 open).

Delete: none.

## Implementation Steps
1. Update root README (status table, overrides, quickstart for backend venv + Flutter).
2. Write design-decisions.md (the 5 decisions + rationale + spec divergence note).
3. Write system-architecture.md (diagram + data flow + engine/slack summary).
4. Write codebase-summary.md, code-standards.md.
5. Write development-roadmap.md (mirror plan phases + status) and project-changelog.md.
6. Write deployment-guide.md (EU region, DPA, encryption, backup, Betriebsrat gate).
7. Cross-check links/dates.

## Todo List
- [ ] README status + overrides + quickstart
- [ ] design-decisions.md (holiday/week/slack/no-AI/premium-off)
- [ ] system-architecture.md
- [ ] codebase-summary.md + code-standards.md
- [ ] development-roadmap.md + project-changelog.md
- [ ] deployment-guide.md (EU/DPA/encryption/backup/Betriebsrat)

## Success Criteria
- README states F-01..F-15 status and both overrides (holiday, week model).
- design-decisions.md explains WHY each spec divergence was made.
- Deployment guide covers EU region, DPA, encryption, backup, and the Betriebsrat open item.
- docs/ suite complete per documentation-management.md.

## Risk Assessment
- Docs drift from code (Med/Low) → write after phase 11; reference real module names.
- Override notes missed → future regression (Med/Med) → design-decisions.md is the single source; link from README + holiday model docstring.

## Security Considerations
- Deployment guide records the §9 controls (region, DPA, TLS, at-rest, audit, RBAC) for the customer's DPO sign-off.

## Next Steps
Project complete; remaining items are the customer-confirmation open questions in plan.md.
