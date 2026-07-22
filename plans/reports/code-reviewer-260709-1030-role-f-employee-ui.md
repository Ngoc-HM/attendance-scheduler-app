# Code Review — Role F split + employee UI (self-arrange, time clock, T+2 cap)

Date: 2026-07-09 | Reviewer: code-reviewer | Plan: plans/260709-1030-employee-ui-role-f-self-arrange/

## Scope
- Backend: enums/role_codes/constraints (Role.F), self_arrange (model/schema/service/endpoint), time_clock (model/schema/service/endpoint), schedules T+2 cap, i18n, migrations 0005–0007, demo seed. ~600 new LOC.
- Flutter: user entity + role gating (home_shell, router), self-arrange feature (6 files), time-clock feature (3 files), weekend tint, register/users role F, i18n en+vi. ~1190 new LOC.
- Verification given: 156/156 pytest pass, flutter analyze clean, 4 pre-existing test failures out of scope.

## Overall Assessment
Solid work. Ownership derived from token everywhere (no user-id spoofing paths), published-only enforced via `schedule_service.get(include_draft=False)`, validation runs at create AND approve, migrations are PG-safe (verified: enum type is named `role`; `ALTER TYPE role ADD VALUE IF NOT EXISTS 'F'` in `autocommit_block` is correct; 0007 reuses `leave_status` with `create_type=False` and doesn't drop it on downgrade). Route collision comment verified false-alarm-free: attendance router only has single-segment paths (`""`, `/me`, `/seed`, `/sick-cover`), so `/attendance/clock/*` never shadows. Quota math matches scheduler semantics: solver pins leave as X but raises target by pin count, persisted grid stores AL/S/CD as own codes, so counting genuine X against `partial_block_off_target` is consistent with `check_off_quota`. Role-F exemption sites audited via full `Role.` grep: consecutive/off-chain/violation-checker skip F; staffing/comp-days/premium-off/balance are Role.A-scoped (F correctly excluded); `sick_backfill` + `shift_change strict_review` use `is_fixed` (F correctly non-strict); weekly-off constraint iterates all people (F correctly included). No missed site found.

## Critical Issues
None.

## High Priority

**H1. Self-arrange can silently overwrite approved-leave cells (AL/S) — leave/schedule consistency bypass.**
`self_arrange_service._validate` (backend/app/services/self_arrange_service.py:76-89) checks the NEW code is in the role domain but never checks the CURRENT code of the target cell. A T/F employee with a pinned AL/S day can submit `AL-day → AD` (quota passes — X count unchanged), or pair `AL-day → X` with `X-day → AD` (quota preserved). Admin approval applies it, converting an approved leave day into a working day (or hiding AL as X) while the LeaveRequest stays approved — corrupts leave accounting and downstream calculations (an S day flipped to AD becomes paid working credit). The Flutter client blocks this (`toggle` only flips X↔AD), but the API does not — trust boundary lives on the server. Admin sees only "5→AD" in the pending panel, no signal the cell was leave.
Fix: in the changes loop, require `own[c.work_date].code in {AttendanceCode.AD, AttendanceCode.X}` (mirror the client guard; for M it'd be {O_D, X} — use `set(codes_for(role))` as the editable set). Add a test: submit change on an AL cell → 4xx.

## Medium Priority

**M1. Time-clock "today" is server UTC date — misattribution around local midnight (severity: real but bounded).**
`time_clock_service._today()` uses UTC. User in Frankfurt (UTC+1/+2): a 00:30 local check-in lands on the previous calendar day's row; conversely someone who checked out late can't produce two distinct local-day entries within one UTC day (409). History rows render `workDate` (UTC day) next to `.toLocal()` times, so a 00:30 local check-in shows under the wrong weekday. For a day-shift workforce this bites only midnight-adjacent clocking; it is NOT data loss — timestamps are stored tz-aware UTC and remain correct. Decide the business timezone for day bucketing (e.g. derive work_date from a configured `Europe/Berlin`/`Asia/Ho_Chi_Minh` tz) before anyone works night shifts.

**M2. Approval recheck warnings dropped by the admin UI.**
Backend computes `warnings` (hard-rule recheck) on approve and returns them in `SelfArrangeRead.warnings`; `SelfArrangePendingPanel._decide` shows only the generic "Request decided." toast. Admin never learns the batch broke staffing/consecutive rules — undermines the whole "informational recheck" contract (F-09 parity). Surface `updated.warnings` in the toast/dialog when non-empty.

**M3. `decide()` TOCTOU — no atomicity on status transition.**
backend/app/services/self_arrange_service.py:170-207: read `req.status != pending`, mutate, commit — two concurrent decisions both pass the guard under READ COMMITTED. Approve+reject race can apply cells to the schedule yet record status=rejected. Single-admin (Role.M) reality makes this unlikely; still, a `WHERE status='pending'` conditional UPDATE or `with_for_update()` on the request row is cheap insurance. Same pattern exists in `check_in` (double-tap → unique-constraint IntegrityError → unhandled 500 instead of 409).

**M4. `TimeClockState.copyWith` cannot reset `today` to null — stale-state trap.**
time_clock_provider.dart:32 `today: today ?? this.today`. Session open across the UTC-midnight boundary: `load()` gets `null` from `/clock/today` but state keeps yesterday's entry → `checkedIn/checkedOut` stay true → check-in stays disabled on the new day until app restart. Use a sentinel/`clearToday` flag or model `today` load as a fresh state object instead of copyWith.

**M5. Self-arrange `load()` has no stale-response guard.**
Rapid month navigation: response for month N can arrive after month N+1's and overwrite `myAssignments` with the wrong month (draft was cleared, but grid shows stale data for the displayed month). Add a request sequence token or compare (year,month) captured at call time before applying state.

## Low Priority

- **L1.** `self_arrange_service` calls `schedule_service._recheck_violations` (private). Promote to a public helper — DRY-correct but crosses the underscore boundary.
- **L2.** Provider `load()` catch treats every error (network down, 500) as `notPublished` → page shows "not published yet" for a dead network. Branch on ApiException statusCode (403/404 → friendly; else show error).
- **L3.** T+2 client/server mismatch: client caps with device-local `DateTime.now()`, server with `date.today()` (server tz). At month boundaries across timezones the client may allow a month the server 403s; degrades gracefully into the (misleading, see L2) notPublished state. Also `get_schedule` doesn't validate `month` 1–12 for the cap arithmetic — `month=13` passes the cap formula oddly but falls to 404; harmless.
- **L4.** `UserRole.fromApi` unknown → `t` (canSelfArrange=true). Forward-compat hazard: a future restricted role letter on an old client silently gains self-arrange UI (server still blocks). Consider defaulting unknowns to the most restricted role.
- **L5.** self_arrange_provider.dart is 252 LOC (>200 guideline) — two controllers in one file; split employee/admin.
- **L6.** Endpoint param `all` shadows the Python builtin (endpoints/self_arrange.py:56); rename `scope`/`all_users`.
- **L7.** Pending panel shows "User {requesterId}" — numeric id, admin must mentally map. Include username/full name (requester relationship or join).
- **L8.** Self-arrange create isn't capped at T+2 (only the schedule view is). Published-only makes it moot today; note if publishing ever runs further ahead.
- **L9.** `objective_off_pairing` + weekly-off leave pinning apply to F (soft objectives). Consistent with "F keeps weekly-2-off," but the "ONLY the weekly-2-off rule" comments overstate — X-pairing preference also shapes F rosters. Confirm intended.
- **L10.** HomeShell null-user branch renders the 6-tab admin nav while auth loads → brief wrong-nav flash for non-admins (router guard prevents access). A minimal/neutral loading nav would be cleaner.

## Edge Cases Scouted
- Route shadowing `/attendance/{...}` vs `/attendance/clock/*`: verified safe (attendance router has no multi-segment path routes).
- PG enum name verified (`role`) — 0005 targets the right type; downgrade no-op is the correct call for PG enums.
- 0007 `postgresql.ENUM(create_type=False)` is PG-only; consistent with the existing PG-only migration chain (tests use `create_all` on SQLite, never alembic).
- Draft `Map<DateTime,String>` key equality: safe — keys are always the parsed `a.workDate` instances themselves (local-midnight, no UTC flag mixing); page never constructs synthetic DateTimes for lookups.
- `selected < 0 ? 0 : selected` in HomeShell guards the admin-visits-/self-arrange case (no nav item → -1).
- December rollover in leaves `firstAllowed` (`month+1=13`) — Dart normalizes; fine.
- `blockOffCounts` mirrors `build_weeks`/`partial_block_off_target` exactly (incl. `(len/7*2).round()` == Python `round` for these values: .29→0, .57→1, .86→1, 1.14→1).

## Positive Observations
- Both-ends validation (create + approve) against the CURRENT schedule is the right call; approve even re-checks role (handles role changed to A mid-flight).
- Own-data derivation from token throughout time-clock and self-arrange; admin listing gated on Role.M matching existing deps pattern.
- Batch JSON shape is justified (single-cell change can never satisfy the quota) and documented in the model docstring.
- `leaves_remote_datasource` DRY cleanup to `ApiException.fromDio` — nice drive-by.
- Test coverage hits the important auth/ownership/quota/404/403 paths.

## Recommended Actions (priority order)
1. H1: server-side guard — target cell's current code must be within the employee-editable set; add regression test.
2. M2: show `warnings` after approve in the pending panel.
3. M4: fix `copyWith` null-reset for `today`.
4. M3: conditional-update/row-lock on decide; map check-in IntegrityError → 409.
5. M1: decide business tz for time-clock day bucketing (owner decision needed).
6. M5/L2/L3: stale-response token + error-vs-notPublished branching in self-arrange provider.

## Metrics
- Backend tests: 156/156 pass (given). Flutter analyze: clean (given).
- New/changed LOC: ~1,800. Files >200 LOC: self_arrange_provider.dart (252).
- Linting issues: 0 reported.

## Unresolved Questions
1. M1 timezone: what is the operating timezone for check-in day bucketing — Frankfurt, Vietnam, or per-user? Owner decision needed before fix.
2. L9: should F be excluded from the X-pairing soft objective to honor "only weekly-2-off," or is pairing desirable for F too?
3. H1 scope: should M (admin) be allowed through self-arrange at all (`is_fixed` check admits M "technically")? Suggest restricting to `canSelfArrange` roles (T/F) server-side for symmetry with the client.
