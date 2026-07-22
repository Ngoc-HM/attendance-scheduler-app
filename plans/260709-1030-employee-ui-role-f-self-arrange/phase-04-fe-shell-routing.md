# Phase 04 — FE employee shell + routing + entity + i18n (foundation)

## Context Links
- Plan: [plan.md](plan.md)
- Shell: `attendance_scheduler_app/lib/features/home/presentation/pages/home_shell.dart` (currently gates non-admin → `employee_blank_shell.dart`)
- Router: `lib/core/router/app_router.dart`; entity: `lib/features/auth/domain/entities/user.dart`
- i18n: `lib/i18n/app_localizations.dart` (`text()` map + getters + `roleLabel`)

## Overview
Priority P1 (FE foundation). Status pending. Replace `EmployeeBlankShell` gate with
a **role-gated navigation shell**. Owns all SHARED FE files (shell, router, entity,
i18n) + creates **stub pages** for self-arrange/clock so P06/P07 fill them in. This
prevents parallel file conflicts.

## Key Insights
- `HomeShell` already builds `DsNavigationShell` for admin — reuse it; just compute a role-specific `destinations` list instead of early-returning blank.
- Existing sub-pages are employee-safe: `schedule_page` shows published-only + "not published" message for non-admin; `leaves_page` hides approve/reject when `!isAdmin`. Reuse both as-is.
- Router is a single `ShellRoute`; add routes `/self-arrange`, `/clock`. Add redirect guard so non-admin hitting admin-only paths → `/schedule`.
- `UserRole` enum lacks `f`; `fromApi` falls back to `t` → F would silently render as T. Must add `f`.

## Requirements
- Non-admin **T/F** tabs: Schedule, Leaves, Check-in/out (Clock), **Self-arrange**.
- Non-admin **A** tabs: Schedule, Leaves, Clock (NO self-arrange).
- Admin **M**: unchanged 6 tabs.
- No admin-only buttons for non-M anywhere (guard admin routes).
- Add all new i18n keys (en/vi) used by P05/P06/P07/P08 so those phases touch no shared file.

## Architecture
Data in: `auth.user.role`. Transform: `destinations = _destinationsFor(role)`. Non-admin no longer blank. Router redirect: `if !isAdmin && path in adminOnly → /schedule`. Data out: `DsNavigationShell` with role-correct tabs.

## Related Code Files
**Modify:**
- `lib/features/auth/domain/entities/user.dart` — `UserRole { m, t, a, f }`; `fromApi 'F'→f`; add `isSelfArrangeCapable => this==t || this==f` (or `!isFixed && !isAdmin || t/f`); keep `isAdmin`/`isFixed`.
- `lib/features/home/presentation/pages/home_shell.dart` — remove blank-shell early return; build role-based `destinations`; keep admin branch.
- `lib/core/router/app_router.dart` — add `AppRoute.selfArrange='/self-arrange'`, `AppRoute.clock='/clock'`; `GoRoute`s → stub pages; `redirect` guard for admin-only routes.
- `lib/i18n/app_localizations.dart` — en+vi keys: `navSelfArrange`, `navClock`, `selfArrange*`, `clock*` (checkIn/checkOut/checkedInAt/notCheckedIn...), role F in `roleLabel` (`'F' => 'F — Flexible (no swap)'` / `'F — Linh hoạt'`).
**Create (stubs, finalized by P06/P07):**
- `lib/features/schedule/presentation/pages/self_arrange_page.dart` — stub scaffold.
- `lib/features/attendance/presentation/pages/time_clock_page.dart` — stub scaffold.

## Implementation Steps
1. Entity: add `f`; update `fromApi` switch (`'F' => UserRole.f`); helper `isSelfArrangeCapable`.
2. i18n: add keys to en map (~line 30) + vi map (~line 294); add getters where pattern used; extend `roleLabel` switch with `'F'`.
3. Stub pages: minimal `StatelessWidget` returning `DsPage`/`Center(Text('...'))`.
4. Router: add route constants + `GoRoute`s (NoTransitionPage) for `/self-arrange`,`/clock`; add `redirect` returning `/schedule` when non-admin requests `/flights`,`/reports`,`/users`,`/attendance`.
5. `home_shell.dart`: replace `if (user!=null && !user.isAdmin) return EmployeeBlankShell(...)` with role-based destinations:
   - admin → existing 6.
   - non-admin base → [Schedule, Leaves, Clock]; if `role.isSelfArrangeCapable` insert Self-arrange.
   - keep logout/lang controls.
6. Leave `employee_blank_shell.dart` in place (unused) or delete import — remove reference.
7. `flutter analyze` (allow P06/P07 stubs).

## Todo List
- [ ] UserRole.f + fromApi + helper
- [ ] i18n new keys + roleLabel F (en/vi)
- [ ] stub self_arrange_page + time_clock_page
- [ ] router routes + admin redirect guard
- [ ] home_shell role-based nav
- [ ] remove blank-shell gate
- [ ] analyze

## Success Criteria
- Log in as T/F → shell with 4 tabs (Schedule/Leaves/Clock/Self-arrange). A → 3 tabs (no self-arrange). M → unchanged.
- Non-admin cannot reach /users,/flights,/reports,/attendance (redirect).
- F role renders as "F …" not "T".

## Risk Assessment
| Risk | L×I | Mitigation |
|------|-----|-----------|
| Shared-file contention w/ P06–P08 | High×High | P04 SOLE owner of shell/router/entity/i18n; P06/P07/P08 own only feature dirs. Enforced ordering. |
| Router stubs won't compile before P06/P07 | Med×Low | P04 creates real stub files; P06/P07 replace bodies (sequential, not parallel). |
| Redirect loop | Low×Med | Guard only redirects admin-only paths → /schedule (always allowed). |
| `roleLabel` fallthrough leaves F blank | Low×Low | Explicit `'F'` case added. |

## Security Considerations
- Client route guard is UX only; real authorization is server-side (P02/P03 role checks). Note: never rely on hidden tabs for security.

## Next Steps
Unblocks P06, P07, P08. Depends on nothing hard (can scaffold once endpoints' contracts known from P02/P03).

## Unresolved
- (d) show self-arrange tab to M? Plan: no (M uses admin schedule override). (g) F in nav same as T minus nothing extra.
