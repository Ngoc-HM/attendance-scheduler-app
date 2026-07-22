# Phase 08 — FE role F in users admin + register

## Context Links
- Plan: [plan.md](plan.md); blocked by [P01](phase-01-backend-role-f.md) (backend accepts F) + [P04](phase-04-fe-shell-routing.md) (`UserRole.f` + `roleLabel` F already added)
- Register: `lib/features/auth/presentation/pages/register_page.dart` (`_selectableRoles = [t, a]`)
- Users admin: `lib/features/users/presentation/pages/users_page.dart` (`onChangeRole` → `UserRoleX.fromApi`)

## Overview
Priority P3. Status pending. Expose role **F** in the admin users role-change flow
and (if self-registerable, Q g) the register page role picker. `UserRole.f`,
`fromApi`, and `roleLabel('F')` already exist from P04 — this phase only surfaces F
in the two pickers.

## Key Insights
- `UserRole.f` + `roleLabel` done in P04 → this phase is small, own-file only (register_page, users_page). No shared-file edits.
- Register selectable roles currently `[t, a]`; add `f` (pending Q g). Admin role-change already maps via `fromApi` — just ensure F appears as an option/label.

## Requirements
- Admin can set a user's role to F (users page role selector/dialog includes F).
- Register page role options include F (if self-register allowed).
- F displays with proper label everywhere (from P04 `roleLabel`).

## Architecture
Data in: admin/user selects F in a dropdown. Transform: `UserRoleX.fromApi/apiValue` → backend `POST/PUT /users` with `role:"F"` (P01 enum accepts). Data out: user with role F, auto-code "F1".

## Related Code Files
**Modify:**
- `lib/features/auth/presentation/pages/register_page.dart` — `_selectableRoles = [UserRole.t, UserRole.a, UserRole.f]` (or `[t,f,a]` order).
- `lib/features/users/presentation/pages/users_page.dart` — ensure role-change UI lists F (add to whatever options list drives `onChangeRole`; verify how options are enumerated — may iterate `UserRole.values`).

## Implementation Steps
1. Register: add `UserRole.f` to `_selectableRoles`.
2. Users page: locate role option source; include F (prefer `UserRole.values` minus none, or explicit list). Confirm role-change confirm dialog uses `roleLabel` (already F-aware).
3. `flutter analyze`.

## Todo List
- [ ] register selectable roles + F
- [ ] users admin role options + F
- [ ] analyze

## Success Criteria
- Admin changes a user to F; account code becomes F#; user then sees T/F employee shell (self-arrange tab).
- (If enabled) new registrant can pick F.

## Risk Assessment
| Risk | L×I | Mitigation |
|------|-----|-----------|
| F self-register undesired (Q g) | Low×Low | If owner says admin-only, drop F from register list; keep in users admin. |
| Users page enumerates roles differently than assumed | Low×Med | P08 starts by reading users_page role-option source before editing. |

## Security Considerations
- Role assignment is admin-gated server-side; F is non-admin (no escalation).

## Next Steps
Depends P01+P04. Parallel with P06, P07.

## Unresolved
- (g) F self-registerable vs admin-assign only.
