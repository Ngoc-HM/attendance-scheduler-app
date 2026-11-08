# Review-2 Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix every finding of the 2026-11-08 whole-system review except A1 (the dev-mode admin password reset, which the owner keeps on purpose).

**Architecture:** Same monorepo, same layering. Backend fixes stay inside the service that owns the rule; engine fixes keep engine, violation checker and month-close counting the same way; Flutter fixes stay in the feature that shows the bug. No new frameworks.

**Tech Stack:** FastAPI, SQLAlchemy 2, Alembic, OR-Tools CP-SAT, pytest; Flutter 3.47.7 (Riverpod, Dio, go_router); GitHub Actions.

**Spec:** `docs/superpowers/reviews/2026-11-08-system-review.md` (finding ids A2–F below refer to it). Owner decisions: `docs/design-decisions.md`.

## Global Constraints

- Do not change the dev-mode admin reset in `backend/app/core/bootstrap.py:100-110` (owner 2026-11-08: "bỏ qua phần pass admin bị đặt lại vì đang chế độ dev").
- Never load `backend/.env` in tests or probes (it points at the shared PostgreSQL). Run backend commands with `DATABASE_URL=sqlite:///<scratch>/x.db ENVIRONMENT=dev`.
- Python venv: `/private/tmp/claude-501/-Users-hmngoc-project-attendance-scheduler-app/9b2a97bf-bb6f-4aa7-a138-34c1e79eb82e/scratchpad/venv/bin/python`. Flutter: `~/develop/flutter/bin/flutter` (3.47.7).
- Run pytest as `python -m pytest -p no:cacheprovider -o addopts="" <files>`; run only the test files you touch plus their neighbours (the full suite takes 15 min; the coordinator runs it after merging).
- Every HTTPException `detail` is an i18n key present in both `en` and `vi` maps of `backend/app/core/i18n.py`; every Flutter user-facing string is a key in both maps of `attendance_scheduler_app/lib/i18n/app_localizations.dart`.
- Use `business_today()` / `settings.TIMEZONE`, never `date.today()` or a hardcoded zone.
- Commits: conventional commits, no AI references, no `Co-Authored-By` trailer (docs/code-standards.md).
- New migration number is `0009`; only Task 3 creates a migration.
- Engine weights stay: slack 10 000, comp 2 000, A/D gap 300, balance 100, premium-off 30, off-pairing 15.

## Owner rulings made for this plan (recorded in design-decisions by Task 13)

- **R1 (C3):** an off run that contains a pinned annual/monthly leave day (AL) is exempt from the "more than 5 consecutive off days must be annual leave" rule, in engine and checker. The weekly X days next to an approved leave are therefore legal.
- **R2 (F9):** the premium-off objective counts only X days the engine chooses; pinned AL on Sat/Sun/holiday is not premium (matches `premium_off_count`).
- **R3 (F10):** comp-day consumption is counted from `HOLIDAY_COMP_EFFECTIVE_FROM`, like earning.
- **R4 (F13):** admin manual override may create the missing cell of an active user; the re-check flags A/D cells of disabled users and does not count them as cover.
- **R5 (F15):** no holiday-work penalty (design suggestion, not a bug); listed as an open question.
- **R6 (goldens):** goldens are tagged `golden` and run only on a macOS CI job; Ubuntu runs `--exclude-tags golden`; the Windows build no longer waits for goldens.
- **R7 (B1):** reports list only active users; cells starting with `= + - @ TAB CR` are prefixed with `'`.
- **R8 (deleting users):** requests the deleted user decided keep their row with `decided_by_id = NULL`; requests where the deleted user is the swap counterpart are deleted when pending and kept with `counterpart_user_id = NULL` when decided.

## Review Focus

- PostgreSQL foreign keys: any delete path (users, schedules, flights) must pass with FK enforcement on; tests must run with `PRAGMA foreign_keys=ON`.
- Month edges: day 1 and the last day of a month, with history from the previous month (streaks, off chains, comp).
- An employee who logs out and another who logs in on the same app instance must never see the first one's data.
- Out-of-range input from any authenticated user (month 0/13, huge strings, unknown ids) returns 4xx, never 500.
- A 1-worker solver run on a busy CI machine must not invent violations.

---

## Wave 1 (alone, everything else depends on it)

### Task 1: Foreign keys in tests, safe user deletion, test DB guard

**Findings:** B2, B3, B9, CI "Tests on PostgreSQL".

**Files:**
- Modify: `backend/app/core/database.py` (SQLite connect event `PRAGMA foreign_keys=ON`, applied for every SQLite engine, app and tests)
- Modify: `backend/tests/conftest.py` (test DB guard), `backend/tests/test_user_admin_guard.py` (fixture cleans child rows), any other fixture that breaks once FKs are enforced
- Modify: `backend/app/services/user_service.py:300-325` (`delete`), `backend/app/api/v1/endpoints/users.py:71-76`
- Test: `backend/tests/test_user_delete.py` (new)

**Interfaces:**
- Produces: `user_service.delete(db, user_id, acting_admin_id) -> None` unchanged signature; the endpoint writes the audit row before the delete commits. Self-delete audit uses `actor_id=None` and detail `self`.

- [ ] Step 1: write failing tests in `test_user_delete.py`: `test_delete_admin_keeps_decided_shift_changes` (row survives, `decided_by_id is None`), `test_delete_admin_who_decided_self_arrange_returns_204`, `test_delete_counterpart_pending_request_removed_decided_kept`, `test_admin_self_delete_returns_204_and_audits` (one `user.delete` audit row exists), `test_sqlite_foreign_keys_enforced` (`PRAGMA foreign_keys` returns 1 on a session).
- [ ] Step 2: run them, expect FAIL.
- [ ] Step 3: implement the connect event, ruling R8 in `delete`, audit-before-delete in the endpoint.
- [ ] Step 4: conftest: if `DATABASE_URL` is already set and `script_guard.is_local_database(url)` is False, `pytest.exit("refusing to run tests against a non-local database")`; otherwise keep today's behaviour (CI's localhost PostgreSQL stays allowed).
- [ ] Step 5: run the whole backend suite once (this task alone is allowed to, it is the FK baseline): every test passes with FKs on. Fix fixtures, never production code paths, unless a failure is a real bug (then report it).
- [ ] Step 6: commit.

## Wave 2 (parallel; each task owns the files listed; i18n maps are merged by union)

### Task 2: Shift-change and leave-decision hardening

**Findings:** B4, E (validation of shift-change create, double approve, long strings).

**Files:** `backend/app/services/shift_change_service.py`, `backend/app/services/schedule_service.py` (only `apply_shift_change`, lines ~199-262), `backend/app/services/leave_service.py` (`decide`, `revoke` locking only), `backend/app/schemas/{leave,shift_change,self_arrange,attendance,user}.py`, tests `backend/tests/test_shift_change_service.py`, `backend/tests/test_leave_service.py`.

- [ ] Tests first:
  - `test_change_code_on_al_cell_refused` (create → 422 `swap.cell_locked`-style key; same check again at approval for an old pending request).
  - `test_change_code_on_cd_cell_refused`.
  - `test_create_swap_unknown_counterpart_404`, `test_create_swap_with_self_422`, `test_create_swap_other_role_422`, `test_create_swap_disabled_counterpart_422`, `test_create_request_without_own_cell_409` (uses the existing `swap.own_cell_only` key).
  - `test_second_approve_is_409` (approve twice sequentially → second 409 `swap.not_pending`; cells swapped once).
  - `test_note_longer_than_column_422` for leave note, shift-change note, self-arrange note, attendance note, user `full_name`.
- [ ] Implement: current cell must be in `role_code_validation.requestable_codes(role)` for `change_code` (create and approval); create-time checks above; lock the request row with `with_for_update()` and commit cells + status in one transaction (shift change and leave decide); `Field(max_length=N)` equal to each column length.
- [ ] Replace the hardcoded English at `schedule_service.py:230` with an i18n key.
- [ ] Run touched test files; commit.

### Task 3: Reports and flight import

**Findings:** B1, B5, flight parser i18n (E).

**Files:** `backend/app/services/report_service.py`, `backend/app/services/report_serializers.py`, `backend/app/services/flight_service.py`, `backend/app/services/flight_excel_parser.py`, `backend/app/models/flight.py`, `backend/alembic/versions/0009_flight_unique_day_number.py` (new), tests `backend/tests/test_report_service.py`, `backend/tests/test_flight_service.py`.

- [ ] Tests first: `test_csv_formula_cell_is_escaped` (`=HYPERLINK(...)` name → `'=HYPERLINK(...)`, also `+ - @`), `test_xlsx_formula_cell_is_text` (openpyxl cell `data_type == "s"`), `test_reports_exclude_pending_and_disabled`, `test_import_duplicate_rows_kept_once`, `test_unique_flight_day_number_constraint`.
- [ ] Implement ruling R7; de-duplicate parsed rows by `(day, flt_number)` (last row wins, plus a row warning); `UniqueConstraint("day_id"/"day", "flt_number")` matching the actual model columns; migration 0009 first deletes duplicates keeping the lowest id, then adds the constraint (batch mode for SQLite, downgrade drops it); parser row errors become i18n keys with parameters.
- [ ] Verify migration: `alembic upgrade head` then `alembic downgrade 0008` then `upgrade head` on a scratch SQLite DB.
- [ ] Run touched tests; commit.

### Task 4: Attendance, sick cover, input bounds, i18n, business time

**Findings:** B6, E (sick note privacy, seed only published, month/year 500s, hardcoded English, host-clock dates, time-clock zone).

**Files:** `backend/app/services/attendance_service.py`, `backend/app/services/sick_backfill.py`, `backend/app/services/time_clock_service.py`, `backend/app/services/compliance_service.py`, `backend/app/services/role_code_validation.py`, `backend/app/services/audit_service.py`, `backend/app/api/v1/endpoints/{attendance,time_clock,flights,holidays,reports,calculations,leaves,shift_changes,self_arrange,schedules}.py` (query/path bounds and "Admin only"/"Decision status" strings only), `backend/app/core/i18n.py`, tests `backend/tests/test_attendance_sick.py`, `backend/tests/test_time_clock.py` (new), `backend/tests/test_input_bounds.py` (new).

- [ ] Tests first: `test_sick_cover_skips_disabled_users`, `test_sick_cover_note_has_no_health_text` (cover row note is None), `test_seed_refuses_draft_schedule` (409 new key), `test_month_13_returns_422` parametrised over every year/month endpoint (employee and admin ones), `test_year_out_of_range_422`, `test_check_in_twice_409`, `test_check_out_without_check_in_409`, `test_punch_near_midnight_uses_business_day` (freeze business time), `test_every_http_exception_detail_is_catalog_key` (walk `app/` source for `HTTPException(` details that are string literals → none).
- [ ] Implement: active users only as cover candidates; no note on the cover row; seed only `published`; `Annotated[int, Query(ge=1, le=12)]` / `Path(...)` for month and `ge=2000, le=2100` for year on every endpoint listed; i18n keys for every hardcoded detail (including `audit.write_failed`, `role_code_validation`, `sick_backfill` messages); `business_today()` in `schedules.py:36` and `compliance_service.py`; `ZoneInfo(settings.TIMEZONE)` in `time_clock_service`.
- [ ] Run touched tests; commit.

### Task 5: Engine solve phases, status, staffing edge cases

**Findings:** C1, F4, F5, F6.

**Files:** `backend/app/scheduler/engine.py`, `backend/app/scheduler/domain.py` (`SolverOutput` fields), `backend/app/scheduler/constraints_staffing.py`, `backend/app/core/config.py` (one new setting only), tests `backend/tests/test_engine_solve_phases.py` (new), `backend/tests/test_engine_staffing.py`.

**Interfaces:**
- Produces: `SolverOutput.status: str` (`"optimal" | "feasible" | "infeasible" | "unknown"`) and `SolverOutput.slack_proven_minimal: bool`; `settings.SOLVER_NUM_WORKERS: int = 8` (`ge=1`).

- [ ] Tests first: `test_one_worker_finds_zero_slack` (9-user instance from the review: 1M 2T 1F 5A, 1–2 pairs/day, carries; `num_workers=1` → `violations == []`), `test_status_reported`, `test_one_role_a_on_leave_two_pair_day_is_feasible` (returns feasible with a staffing violation), `test_no_role_a_users_reports_shortfall` (violations count equals the checker's for the same grid), `test_same_input_same_output_with_fixed_workers` (two runs equal when `num_workers=1`).
- [ ] Implement two phases: phase 1 minimises slack only (time share 40 %); fix the slack sum to the phase-1 value (`<=`); phase 2 minimises soft terms with the phase-1 solution as hint. `num_workers` from settings; keep `random_seed=42`. Bound `under` by `demand`; register the shortfall when there are no role-A users.
- [ ] Run engine test files; commit.

### Task 6: Engine, checker and month-close count the same way

**Findings:** C3 (ruling R1), F7, F8, F9 (R2), F10 (R3), F14.

**Files:** `backend/app/scheduler/constraints_off_chain.py`, `backend/app/scheduler/objective_premium_off.py`, `backend/app/services/schedule_violation_checker.py`, `backend/app/services/carry_over_math.py`, `backend/app/services/schedule_history.py`, `backend/app/services/schedule_input_builder.py`, `backend/app/scheduler/domain.py` (only a `prev_codes`/boundary field on the per-user input; coordinate names with Task 5: add fields, do not rename), tests `backend/tests/test_engine_cross_month_rules.py`, `backend/tests/test_violation_checker.py`, `backend/tests/test_schedule_history.py`, `backend/tests/test_engine_checker_agreement.py` (new).

**Interfaces:**
- Produces: `UserBoundaryState.prev_codes: tuple[str, ...]` (last 6 codes of the previous month, oldest first; empty when no history) consumed by the engine off-chain constraint and the checker.

- [ ] Tests first: `test_five_day_monthly_leave_in_one_block_no_violation` (AL Tue 9–Sat 13 Feb 2027, engine and checker both clean), `test_checker_flags_carry_streak_six_then_work`, `test_checker_flags_off_chain_after_annual_leave_start`, `test_off_chain_crosses_month_boundary` (AL 27–31 Jul then X on 1 Aug flagged by both), `test_premium_off_ignores_pinned_al`, `test_pre_cutoff_cd_does_not_consume_post_cutoff_comp`, `test_engine_clean_grid_passes_checker` (property-style over 3 seeded random small instances), `test_boundary_states_query_count_bounded` (count SQL statements with an event listener: constant in number of users).
- [ ] Implement R1/R2/R3; checker uses `run >= 6` with a per-run flag; off-chain windows include `prev_codes`; `build_boundary_states` indexes the grid by user and limits history (comp/premium aggregated in SQL; 6-day window for streaks).
- [ ] Run engine/checker/history test files; commit.

### Task 7: Schedule lifecycle — violations visible, regenerate, roster changes

**Findings:** C2, F11, F13 (ruling R4), schedule_service hardcoded strings 153/171.

**Files:** `backend/app/services/schedule_service.py` (`generate`, `manual_override`, `publish`, new `violations_for`; not `apply_shift_change`), `backend/app/api/v1/endpoints/schedules.py` (new route only), `backend/app/services/attendance_service.py` is owned by Task 4: call its existing `seed_from_schedule`/`sync_planned_cell` only, tests `backend/tests/test_schedule_service.py`.

**Interfaces:**
- Produces: `GET /api/v1/schedules/{schedule_id}/violations` → `list[ConstraintViolation]` (admin only), computed by `schedule_service.violations_for(db, schedule_id)` (same as `_recheck_violations`). `publish` response unchanged; publish still allowed with violations (admin decision), but the endpoint result of `POST /schedules/{id}/publish` keeps `MonthlyScheduleRead`.

- [ ] Tests first: `test_violations_endpoint_returns_recheck`, `test_violations_endpoint_admin_only`, `test_force_regenerate_published_resyncs_seeded_actuals` (seeded rows `recorded_by IS NULL` follow the new plan, admin rows untouched), `test_override_creates_missing_cell_for_active_user`, `test_override_missing_cell_for_disabled_user_404`, `test_recheck_flags_disabled_user_ad_cells`.
- [ ] Implement; i18n keys for lines 153/171.
- [ ] Run `test_schedule_service.py` and `test_attendance_sync.py`; commit.

### Task 8: Backend runtime and operations

**Findings:** B7, B8, C4/F12, E (prod guard gaps, alembic `%`, `now()` in migrations, script guard bypass, docs/openapi in prod, `ensure_database_exists`).

**Files:** `backend/app/core/bootstrap.py` (seed-admin creation only; the dev reset stays), `backend/app/main.py`, `backend/app/core/config.py` (`validate_for_environment`, TIMEZONE validator), `backend/app/core/database.py` is owned by Task 1 — call it, don't edit, `backend/app/services/schedule_autorun.py`, `backend/alembic/env.py`, `backend/alembic/versions/0001..0007` (`sa.text('now()')` → `sa.func.now()` only), `backend/app/core/script_guard.py`, `backend/scripts/*.py`, tests `backend/tests/test_production_guard.py`, `backend/tests/test_bootstrap.py` (new), `backend/tests/test_schedule_service.py` autorun tests (only the autorun section), `backend/tests/test_script_guard.py`.

- [ ] Tests first: `test_deleted_seed_admin_not_recreated_when_another_active_admin_exists`, `test_create_all_skipped_when_alembic_version_table_exists`, `test_prod_guard_refuses_sqlite_cors_star_autocreate_short_retention`, `test_invalid_timezone_refused_at_startup`, `test_autorun_catches_up_after_missed_day` (day 23, no schedule → generates), `test_autorun_logs_failure_when_infeasible`, `test_autorun_warns_without_flight_data`, `test_alembic_url_with_percent`, `test_guard_rejects_query_host`, `test_scripts_load_backend_env_by_absolute_path`, `test_sqlite_upgrade_head_then_insert` (fresh SQLite via alembic accepts inserts).
- [ ] Implement: seed admin only when no active role-M user exists; skip `create_all` with a warning when `alembic_version` exists; logging configured at INFO for `app.*` in `main.py`; prod guard refuses SQLite/default URL, CORS `*`, `AUTO_CREATE_TABLES=true`, retention below `DATA_RETENTION_MIN_MONTHS`; TIMEZONE validated always; `/docs` and `/openapi.json` disabled in prod; `ensure_database_exists` only outside prod; autorun runs on any day `>= AUTORUN_DAY+1` when the next month has no schedule, `misfire_grace_time=3600`, plus a startup check, logs failures as errors, warns when next month has no FlightDay rows; alembic URL `%` escaped; script guard rejects `host`/`hostaddr`/`service` query params, scripts load `backend/.env` by absolute path and read the password with `getpass` when `--password` is omitted.
- [ ] Run touched tests; commit.

### Task 9: Repository, CI and packaging

**Findings:** A4 (CI), B10, E (lock files, `.gitignore`, `.DS_Store`, compose, backup scripts, action pinning).

**Files:** `.github/workflows/ci.yml`, `.gitignore`, `backend/.dockerignore` (new), `docker-compose.yml`, `scripts/backup_db.sh`, `scripts/restore_db.sh`, `attendance_scheduler_app/pubspec.lock` (track it), `backend/requirements.lock` (new, `pip freeze` of the venv filtered to requirements-dev names), `attendance_scheduler_app/test/visual_golden_test.dart` (tags only), `attendance_scheduler_app/dart_test.yaml` (new, declares tag `golden`), remove tracked `.DS_Store` files.

- [ ] CI: Flutter version `3.47.7`; runner `ubuntu-24.04`; Flutter job runs `flutter test --exclude-tags golden`; new `flutter-goldens` job on `macos-latest` runs `flutter test --tags golden`; `windows-build` needs only `flutter`; backend installs with `-c requirements.lock`; add `alembic check` after the PostgreSQL migration step; production guard smoke runs with `if: always()`; actions pinned to full commit SHAs with the tag in a comment.
- [ ] `.gitignore`: `*.db`, `.DS_Store`, and `!attendance_scheduler_app/pubspec.lock`.
- [ ] Backup/restore: password via `PGPASSWORD` from the parsed URL, URL printed redacted, optional `age`/`gpg` encryption flag documented in the script header.
- [ ] Compose: Postgres healthcheck, `condition: service_healthy`, `restart: unless-stopped`.
- [ ] Verify: `flutter test --exclude-tags golden` and `flutter test --tags golden` both pass locally; `actionlint` if available, else `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"`.
- [ ] Commit.

### Task 10: Flutter schedule screen and shift-change panel

**Findings:** A3, D3, swap picker (E), schedule toasts (E), C2 client side.

**Files:** `lib/features/schedule/presentation/providers/schedule_provider.dart`, `lib/features/schedule/presentation/pages/schedule_page.dart`, `lib/features/schedule/presentation/widgets/shift_change_dialog.dart`, `lib/features/schedule/data/datasources/schedule_remote_datasource.dart`, `lib/core/constants/api_endpoints.dart` (one constant), i18n map, tests under `test/features/schedule/`.

**Interfaces:**
- Consumes: Task 7's `GET /schedules/{id}/violations` → JSON list of `{day, user_id, rule, message}`.

- [ ] Tests first: `switching_to_ungenerated_month_clears_grid` (admin sees empty state, Publish disabled), `publish_targets_month_on_screen`, `pending_panel_shows_requester_and_counterpart_codes`, `approve_shows_warnings_and_reloads_grid`, `swap_picker_lists_same_role_active_colleagues_only`, `publish_shows_violations_before_confirm` (non-empty list → dialog lists them, admin can still publish).
- [ ] Implement: clear `schedule` on load start/failure (`copyWith(clearSchedule: true)`); admin error/empty state; Publish/override check year+month; violations panel on load for admins and before publish; store `ApiException.message` instead of `toString()`.
- [ ] `flutter analyze` + run schedule tests; commit.

### Task 11: Flutter session, users and configuration

**Findings:** D1, D2, D6, 403 inactive user (E), self-demotion refresh (E).

**Files:** `lib/features/auth/presentation/providers/auth_provider.dart`, `lib/core/network/api_client.dart`, `lib/core/config/app_config.dart`, `lib/features/users/data/user_management_datasource.dart`, `lib/features/users/presentation/pages/users_page.dart`, `lib/features/users/presentation/widgets/create_user_dialog.dart`, i18n map, tests under `test/features/auth/`, `test/features/users/`.

- [ ] Tests first: `logout_then_login_other_user_refetches_every_user_scoped_provider` (leaves, attendance, time clock, self-arrange, schedule providers are invalidated), `inactive_403_ends_session`, `user_errors_surface_backend_detail` (through the real `UserManagementDataSource` with a Dio `HttpClientAdapter` fake: 409 last-admin, duplicate username, not_pending, quota 422), `dart_define_wins_over_bundled_env`, `editing_self_refreshes_me`.
- [ ] Implement: a `resetUserScopedProviders(Ref)` helper in `auth_provider.dart` called on logout and session expiry; 403 with detail `auth.inactive_user` (check the real key in `backend/app/api/deps.py`) ends the session; datasource rethrows `ApiException.fromDio`; error mapping by status code; `String.fromEnvironment('API_BASE_URL')` wins when non-empty.
- [ ] `flutter analyze` + run tests; commit.

### Task 12: Flutter attendance, leaves, reports, flights

**Findings:** A2, D4, D5, leave dates, attendance dialog codes, flights batch month, raw toasts (E), missing i18n keys.

**Files:** `lib/features/attendance/data/datasources/attendance_remote_datasource.dart`, `lib/features/attendance/presentation/widgets/attendance_upsert_dialog.dart`, `lib/features/attendance/presentation/pages/attendance_page.dart`, `lib/features/leaves/presentation/{pages/leaves_page.dart,providers/leaves_provider.dart}`, `lib/features/reports/presentation/{pages/reports_page.dart,providers/reports_provider.dart}`, `lib/features/reports/data/datasources/reports_remote_datasource.dart`, `lib/features/flights/presentation/providers/flights_provider.dart`, `lib/features/flights/data/datasources/flights_remote_datasource.dart`, i18n map, tests under `test/features/{attendance,leaves,reports,flights}/`, plus `test/i18n_keys_used_exist_test.dart` (new).

- [ ] Tests first: `sick_cover_body_contains_code_S` (Dio adapter fake), `attendance_dialog_offers_role_codes_plus_S_active_users_only`, `leaves_page_reloads_on_entry_and_refresh_button`, `end_date_resets_when_start_moves_past_it`, `monthly_picker_bounded_to_target_month`, `reports_selectors_on_page_full_year_uses_null_month`, `flights_batch_failure_keeps_previous_month`, `error_toast_shows_backend_detail_not_exception_text`, `every_t_key_used_in_lib_exists` (scan `lib/` for `t('...')`/`.tr('...')` style calls, whatever pattern the app uses).
- [ ] Implement accordingly; datasources use the backend `detail` (flatten 422 lists to their `msg`s).
- [ ] `flutter analyze` + run tests; commit.

## Wave 3

### Task 13: Documentation

**Findings:** F (all docs drift), rulings R1–R8.

**Files:** `README.md`, `backend/README.md`, `docs/{deployment-guide,development-roadmap,system-architecture,codebase-summary,project-changelog,design-decisions,code-standards}.md`, `docs/superpowers/test-guide-2026-11-07.md`, `DESIGN/README.md`, `backend/app/main.py:7-8` and `backend/app/core/config.py:5` docstrings, `backend/.env.example` (missing keys), `alembic/versions/0001_baseline.py:4-5` and `bootstrap.py:73-74` comments ("stamp head").

- [ ] Every number and claim checked against the merged code (test counts from the final gate run).
- [ ] Deployment guide describes the real setup (workstation backend, Tailscale PostgreSQL, process manager, migrations before start) and keeps Docker as an option.
- [ ] design-decisions: rulings R1–R8 as new numbered decisions; R5 and C3 in Open questions for customer confirmation.
- [ ] Commit.
