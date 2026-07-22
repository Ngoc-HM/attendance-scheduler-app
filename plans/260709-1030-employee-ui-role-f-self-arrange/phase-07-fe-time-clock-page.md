# Phase 07 — FE check-in / check-out page

## Context Links
- Plan: [plan.md](plan.md); blocked by [P03](phase-03-backend-time-clock.md) (endpoints) + [P04](phase-04-fe-shell-routing.md) (shell/route/i18n/stub)
- Pattern: `lib/features/attendance/data/datasources/attendance_remote_datasource.dart`
- Endpoints: `POST /attendance/clock/check-in`, `POST /attendance/clock/check-out`, `GET /attendance/clock/me`

## Overview
Priority P2. Status pending. Finalize stub `time_clock_page.dart`: employee sees
today's clock status + Check-in / Check-out buttons + month history list.

## Key Insights
- Simple feature: 2 action buttons + list. Follow existing attendance feature dir layout (data/domain/presentation).
- Buttons disabled by state: check-in disabled if already checked in; check-out disabled until checked in / after checked out.
- Own files only → parallel-safe with P06/P08.

## Requirements
- Show today's `check_in_at` / `check_out_at` (or "—").
- Check-in button → POST check-in; Check-out → POST check-out; refresh after.
- Month history list (GET /me) newest first.
- Errors (409 already/not checked in) surfaced via `DsFeedback`.

## Architecture
Data in: authed user taps button; server `now()`. Transform: datasource POST → refresh GET. Data out: status card + list. No admin data.

## Related Code Files
**Create:**
- `lib/features/attendance/data/models/time_clock_model.dart` — `TimeClockModel(userId, workDate, checkInAt?, checkOutAt?)` + JSON.
- `lib/features/attendance/data/datasources/time_clock_remote_datasource.dart` — `checkIn()`, `checkOut()`, `listMe(year,month)`.
- `lib/features/attendance/presentation/providers/time_clock_provider.dart` — state (today + history) + actions.
**Finalize (stub from P04):**
- `lib/features/attendance/presentation/pages/time_clock_page.dart` — status card + buttons + history list.

## Implementation Steps
1. Model + JSON parse (ISO8601 timestamps).
2. Datasource 3 methods; error mapping `ApiException.fromDio`.
3. Provider: `load(year,month)` (today + history), `checkIn()`, `checkOut()`; refresh on success.
4. Page: `DsPage` with status `DsSurface`/card, two `DsPrimaryButton`/`DsSecondaryButton` (disabled per state), `DsDataTable`/list for history, month switcher.
5. i18n keys already added in P04 (`clockCheckIn`, `clockCheckOut`, `clockCheckedInAt`, `clockNotYet`, `clockHistory`, errors).
6. `flutter analyze`.

## Todo List
- [ ] time_clock_model
- [ ] time_clock_remote_datasource
- [ ] time_clock_provider
- [ ] time_clock_page (finalize stub)
- [ ] button enable/disable state
- [ ] analyze

## Success Criteria
- Check-in records time, button then disabled, status shows time.
- Check-out enabled only after check-in; records time.
- History list shows own month entries; other users never shown.

## Risk Assessment
| Risk | L×I | Mitigation |
|------|-----|-----------|
| Timezone display (UTC vs local) | Med×Med | Parse tz-aware, display local via `toLocal()`. |
| Double-tap race on check-in | Low×Low | Disable button while request in-flight; server 409 guard backstops. |
| Endpoint path clash `/attendance` vs `/attendance/clock` | Low×Med | P03 verified distinct prefix; datasource uses full path. |

## Security Considerations
- Own data only (server-scoped GET /me). No S/health codes involved.

## Next Steps
Depends P03+P04. Parallel with P06, P08.

## Unresolved
- (e) semantics timestamps-only. Whether history shows duration (checkout-checkin) — nice-to-have, YAGNI unless asked.
