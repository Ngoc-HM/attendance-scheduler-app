# Code Standards

## General
- **File size**: keep code files < 200 lines; split by concern (the scheduler
  is split into `constraints_*`, `objective_*`, `slack_registry`; services have
  focused helpers like `sick_backfill`, `carry_over_math`, `leave_windows`).
- **Naming**: descriptive, self-documenting. Python/Dart files use
  `snake_case` / `lower_snake`; classes `PascalCase`.
- **Principles**: YAGNI, KISS, DRY. No fake data / mocks to pass tests.
- **Comments**: explain the *why* and cite the spec clause (`§5.3 #4`,
  `F-10`, `decision #6`) so intent survives.

## Backend (FastAPI + SQLAlchemy)
- Layering is strict: `endpoints` (thin HTTP + RBAC + audit) → `services`
  (business logic) → `models`. Endpoints never embed business rules.
- DTOs are Pydantic schemas; ORM objects never leak past the service boundary
  except via `model_validate`.
- Errors: raise `HTTPException` with an i18n key from `app.core.i18n.t(...)`
  (en/vi kept in sync); `tests/test_input_bounds.py` fails on any literal
  `detail` string. Pure helpers raise nothing — they return data.
- Input: year/month parameters use the bounded aliases in `app/api/params.py`
  (`YearQuery`, `MonthPath`, …); free-text schema fields carry a
  `max_length` equal to their column, so out-of-range years/months and
  over-long text answer 422 instead of 500. Known gap: an id path parameter
  above the 64-bit range (e.g. `schedule_id`) still answers 500 on
  PostgreSQL.
- Engine code is pure compute over dataclasses (`scheduler/domain.py`); no DB,
  no PII beyond `user_id`; rule-based only (no ML — §9.6).
- Schema changes go through **Alembic** (one numbered migration per change,
  working on SQLite and PostgreSQL: batch mode for constraints,
  `sa.func.now()` for defaults), never ad-hoc `create_all`; CI's `alembic
  check` fails when models and migrations drift.
- RBAC via `deps.AdminUser` / `ensure_self_or_admin`; audit every admin
  mutation via `audit_service.record(...)`, which is **fail-loud**: a failed
  write is logged with its full context and raised as HTTP 500 (decision #18).
- Business dates (leave window, autorun, leave-balance year, schedule-month
  limit, retention purge, time clock) come from
  `core.business_time.business_today()` / `business_now()` — the date in
  `TIMEZONE` — never from `date.today()` or a hard-coded zone, because the
  container may run in UTC.
- Rows another request may change concurrently (leave / shift-change
  decisions, the role-code counter) are read with
  `with_for_update()`, and a decision commits its status together with the
  cells it changes.

## Frontend (Flutter, feature-first clean architecture)
- Per feature: `data/{datasources,models,repositories}`,
  `domain/{entities,repositories,usecases}`, `presentation/{providers,pages}`.
  `auth` is the canonical template.
- State via **Riverpod** `StateNotifier<AsyncValue<...>>`; one shared
  `dioProvider` (JWT interceptor) — never construct `Dio` directly.
- All REST paths come from `core/constants/api_endpoints.dart`.
- UI strings via `AppLocalizations.text(key)` (en + vi); reuse `design_system`
  `Ds*View` widgets — pages map provider state into the view's data classes.
- RBAC in the UI: gate admin-only actions on `auth.user.isAdmin`.
- A provider that holds one person's data is added to
  `resetUserScopedProviders` (`auth_provider.dart`), so logout and session
  expiry clear it. Controllers check `mounted` before setting state after an
  `await`.
- Error messages shown to the user go through one helper,
  `apiErrorMessage` (`core/network/api_error_message.dart`): no response →
  translated "server unavailable", 5xx → translated `requestServerError`
  (never the server's text), other errors → the backend's translated
  `detail`, anything else → a translated fallback key. Controllers store the
  error object, not a string; never show `toString()` of an exception.

## Testing
- Backend: `pytest` against an isolated SQLite test DB with foreign keys
  enforced (`tests/conftest.py`; it refuses a non-local `DATABASE_URL`);
  every hard engine rule has a *bind* test and a *slack-reports-violation*
  test. Assert invariants (counts, no-6-run), not exact assignments: the
  solver is reproducible only with 1 worker inside the time limit, so tests
  that compare plans pin `num_workers=1`. Fixtures delete child rows before
  parents (foreign keys are on).
- Flutter: `flutter analyze` must report no issues and `flutter test` must
  pass. Pixel goldens are tagged `golden` and only match on macOS: run
  `flutter test --tags golden` there and `flutter test --exclude-tags golden`
  elsewhere. After an intended visual change, refresh them on macOS with
  `flutter test --update-goldens --tags golden`, look at the new PNGs, and
  never commit `test/failures/` (ignored).
- Do not skip/ xfail to hide real failures. Run the full suite before merge.

## Commits
- Conventional commits (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`);
  no AI references; never commit secrets/.env.
