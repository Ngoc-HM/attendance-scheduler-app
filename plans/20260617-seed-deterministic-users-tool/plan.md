---
title: "Seed deterministic backend users"
description: "Add a rerunnable backend tool that seeds 10 deterministic users with a 4 T / 6 A split."
status: pending
priority: P2
effort: 2h
branch: "main"
tags: [backend, seed, users, idempotent]
created: 2026-06-17
---

# Seed deterministic backend users

**Status:** DONE
**Summary:** Short implementation plan for a backend tool that seeds 10 deterministic users, with safe reruns and no duplicates.

## Likely entry point
- No existing seed CLI/management command is present in `backend/`, so the smallest new surface is a tiny `python -m ...` command under `backend/app/` or `backend/scripts/`.
- Reuse the existing user creation path in `backend/app/services/user_service.py` instead of writing raw ORM inserts.
- Keep startup bootstrap unchanged unless the tool should also be callable from app startup later.

## Files to inspect or modify
- `backend/app/services/user_service.py` for the existing create flow and username uniqueness guard.
- `backend/app/models/user.py` and `backend/app/models/enums.py` to confirm the role/status contract.
- `backend/app/core/bootstrap.py` to mirror the current seed pattern and avoid duplicating database/session handling.
- `backend/app/core/database.py` or the chosen CLI entry module for session management.
- `backend/tests/test_auth_users.py` or a new backend test file for rerun/idempotency coverage.

## Implementation TODO
- [ ] Define a fixed 10-user roster with usernames `nguyenvana` through `nguyenvanj`.
- [ ] Assign exactly 4 users role `T` and 6 users role `A` in the roster.
- [ ] Add a small backend command entrypoint that can be run from the `backend/` workspace, ideally via `python -m ...`.
- [ ] Make the command idempotent by checking `username` before creating each user and skipping existing rows.
- [ ] Reuse `user_service.create()` or the same validation/path so password hashing, code assignment, and status handling stay consistent.
- [ ] Add a focused test that runs the tool twice and asserts the user count stays at 10 with the expected role split.

## Validation steps
- Run the new command once and confirm 10 users are created.
- Run the same command again and confirm no duplicates are added.
- Verify the final roster contains 4 `T` users and 6 `A` users with the expected usernames.
- Run the narrow backend test file for the seed tool, then a backend type/lint check if the new module adds imports or a CLI wrapper.

## Risks and rollback
- If the tool is wired too deeply into startup, it could create unwanted side effects; keep it as an explicit command first.
- If the username list is generated dynamically, reruns could drift; keep the roster hard-coded and deterministic.
- Rollback is simple: remove the new command module and its test, since no schema change is needed.
