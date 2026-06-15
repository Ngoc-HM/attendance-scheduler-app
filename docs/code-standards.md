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
  (en/vi kept in sync). Pure helpers raise nothing — they return data.
- Engine code is pure compute over dataclasses (`scheduler/domain.py`); no DB,
  no PII beyond `user_id`; rule-based only (no ML — §9.6).
- Schema changes go through **Alembic**, never ad-hoc `create_all`.
- RBAC via `deps.AdminUser` / `ensure_self_or_admin`; audit every admin
  mutation via `audit_service.record(...)` (best-effort, never aborts).

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

## Testing
- Backend: `pytest` against an isolated SQLite test DB (`tests/conftest.py`);
  every hard engine rule has a *bind* test and a *slack-reports-violation*
  test. Assert invariants (counts, no-6-run), not exact assignments
  (solver determinism via fixed seed).
- Do not skip/ xfail to hide real failures. Run the full suite before merge.

## Commits
- Conventional commits (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`);
  no AI references; never commit secrets/.env.
