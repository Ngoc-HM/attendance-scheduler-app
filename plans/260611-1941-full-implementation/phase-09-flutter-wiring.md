# Phase 09 — Flutter Wiring (Flights, Leaves, Schedule, Attendance, Reports + i18n)

## Context Links
- Spec: §2 (Flutter Windows client, EN primary + VI), all F-xx UI.
- Pattern reference: `lib/features/auth/**` and `lib/features/users/**` (full clean architecture: data/datasources, data/models, data/repositories, domain/entities, domain/repositories, domain/usecases, presentation/providers, presentation/pages).
- Mockups to replace: `lib/features/{flights,schedule,attendance,leaves,reports}/presentation/pages/*`.
- i18n: `lib/i18n/app_localizations.dart` (custom EN/VI, 535 lines).

## Overview
- Priority: P1. Depends on backend phases 02,03,05,06,08 (the endpoints to call).
- Replace static mockups with real API-wired pages following the auth/users architecture pattern. Build the MISSING data/domain/provider layers for each feature (currently only a pages mockup exists).

## Key Insights
- flights/schedule/attendance/leaves/reports have ONLY a presentation/pages mockup — NO datasource/repository/provider. Each needs the full stack built (mirror auth feature).
- Design system (`lib/design_system`) is rich/reusable (DsFlightRowData etc.) — reuse widgets, swap hardcoded `_rows` for provider state.
- Snackbar-only buttons must call real usecases.
- RBAC in UI: hide admin actions (generate/publish/approve/holiday CRUD/import) from non-admin; users see own data.

## Requirements
Functional per feature:
- Flights: list days for month, manual upsert day, Excel import (file picker → POST), refresh.
- Leaves: submit request (own), list own/all, admin approve/reject.
- Schedule: view month grid (non-admin: published only), admin generate (show violations + A/D suggestions), manual edit cell (show warnings), publish.
- Shift-change (decision #8): user taps OWN cell → "request change" (new code or swap-with-colleague picker) → submit; admin sees pending requests list (strict_review badge for A1–A4) → approve (show re-check warnings) / reject. Lives in schedule feature stack.
- Attendance: view actuals, admin record/update status (incl. S), sick backfill prompt.
- Reports: pick month/year + format, trigger download/save file.
- i18n: add EN+VI strings for all new labels/errors.

Non-functional: loading/error states; reuse existing API client + auth token interceptor.

## Architecture
Per feature (mirror auth): `data/datasources/<f>_remote_datasource.dart` (Dio calls) → `data/models/<f>_model.dart` (JSON ↔ entity) → `data/repositories/<f>_repository_impl.dart` → `domain/entities`, `domain/repositories`, `domain/usecases` → `presentation/providers/<f>_provider.dart` (state) → page consumes provider.

## Related Code Files
Modify (replace mockup data with provider state):
- `lib/features/flights/presentation/pages/flights_page.dart`
- `lib/features/leaves/presentation/pages/leaves_page.dart`
- `lib/features/schedule/presentation/pages/schedule_page.dart`
- `lib/features/attendance/presentation/pages/attendance_page.dart`
- `lib/features/reports/presentation/pages/reports_page.dart`
- `lib/i18n/app_localizations.dart` (new EN/VI keys)

Create (per feature, mirror auth layout; kebab/lower_snake per Dart convention):
- `lib/features/<f>/data/datasources/<f>_remote_datasource.dart`
- `lib/features/<f>/data/models/<f>_model.dart`
- `lib/features/<f>/data/repositories/<f>_repository_impl.dart`
- `lib/features/<f>/domain/entities/<entity>.dart`
- `lib/features/<f>/domain/repositories/<f>_repository.dart`
- `lib/features/<f>/domain/usecases/<action>_usecase.dart`
- `lib/features/<f>/presentation/providers/<f>_provider.dart`
(for f ∈ flights, leaves, schedule, attendance, reports)

Delete: none.

## Implementation Steps
1. Confirm shared API client + auth interceptor location (from auth feature) and reuse.
2. Flights: build stack → wire list/upsert/import (file_picker) → replace `_rows`.
3. Leaves: build stack → submit/list/approve-reject → wire page.
4. Schedule: build stack → generate (render violations/suggestions), manual edit (render warnings), publish → wire grid.
5. Attendance: build stack → record/update-status/sick prompt → wire page.
6. Reports: build stack → trigger export, save file (path_provider) → wire page.
7. i18n: add all EN+VI keys; replace hardcoded strings.
8. RBAC gating in UI by current user role.
9. `flutter analyze` clean; `flutter build windows` (or compile check) passes.

## Todo List
- [ ] Reuse shared API client/interceptor
- [ ] Flights stack + page wiring + import
- [ ] Leaves stack + page wiring
- [ ] Schedule stack + page wiring (violations/warnings/publish)
- [ ] Shift-change request UI (own-cell request + admin approval list w/ strict_review badge)
- [ ] Attendance stack + page wiring (sick)
- [ ] Reports stack + page wiring (download)
- [ ] i18n EN+VI keys
- [ ] RBAC UI gating
- [ ] flutter analyze + build passes

## Success Criteria
- Each page loads live data from the backend (no hardcoded `_rows`).
- Admin can import flights, generate/publish schedule, approve leave, record attendance, export report from the UI.
- Non-admin sees only own data; admin-only buttons hidden.
- All visible strings have EN+VI; `flutter analyze` passes.

## Risk Assessment
- Backend response shape drift vs Flutter models (Med/Med) → build after backend phases; align on schemas.
- Schedule grid complexity (month × users + edit) (Med/High) → reuse design system grid widgets; incremental.
- File picker/save on Windows (Med/Low) → use file_picker + path_provider; test on Windows target.

## Security Considerations
- Token attached via interceptor (existing). S/sick data only shown to admin. No PII cached beyond session.

## Next Steps
After wiring, phase 11 adds Flutter widget tests; phase 12 documents UI flows.
