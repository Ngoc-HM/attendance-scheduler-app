# Phase 01 — Backend Role F (scheduler-exempt except weekly-off)

## Context Links
- Plan: [plan.md](plan.md)
- Enum: `backend/app/models/enums.py`; domains: `backend/app/scheduler/role_codes.py`
- Constraints: `constraints_consecutive.py`, `constraints_off_chain.py`, `constraints_off_days.py`, `constraints.py`
- Recheck: `backend/app/services/schedule_violation_checker.py`
- Seed: `backend/app/services/demo_user_seed.py`; migration pattern: `alembic/versions/0003_*.py`

## Overview
Priority P1 (blocker). Status pending. Add role **F**: no admin rights; in solver F
has NO constraints EXCEPT 2-off-days-per-7-day-block. Split from T; default code
domain = **{AD, X}** (same as T).

## Key Insights
- Schema managed by **Alembic** (`upgrade head`), not create_all in prod (`bootstrap.py:70` comment). Tests use SQLite create_all → F auto-present, migration is Postgres-only.
- Postgres role is a real ENUM (`SAEnum(Role, name="role")`); need `ALTER TYPE role ADD VALUE 'F'`.
- Constraints scoped `Role.A` only (`staffing`, `comp_days`, `objective_balance`, `objectives`) auto-exclude F — no change.
- Constraints iterating ALL people: `off_days` (KEEP for F), `consecutive` + `off_chain` (must SKIP for F).
- `one_status_per_day` / `respect_approved_off` use `codes_for(p.role)` → need `ROLE_CODES[Role.F]`.
- `RoleCodeCounter.role` is String(2); `next_user_code` auto-creates counter → "F1", "F2" with no migration.
- `is_flexible` currently only self-referenced (no consumers) — add F for semantic correctness.

## Requirements
- F selectable as a role everywhere Role is accepted (schemas auto-allow via enum).
- Solver: F gets `{AD, X}` domain, exactly-one-per-day, approved-off pin, weekly-2-off; NO consecutive, NO off-chain, NO staffing, NO comp-days.
- Manual-override recheck must NOT flag F for consecutive; still checks F weekly-off.
- Prod migration additive + reversible-safe.

## Architecture
Data in: `User.role == Role.F`. Transform: `schedule_input_builder` passes role → engine builds vars from `codes_for(F)`; `constraints.add_all` wires rules but consecutive/off-chain early-`continue` on F. Data out: draft assignments with F rows honoring weekly-off only.

## Related Code Files
**Modify:**
- `backend/app/models/enums.py` — add `F = "F"`; `is_flexible` → `{M, T, F}`.
- `backend/app/scheduler/role_codes.py` — `ROLE_CODES[Role.F] = (AD, X)`.
- `backend/app/scheduler/constraints_consecutive.py` — skip `p.role is Role.F` in the `for p` loop.
- `backend/app/scheduler/constraints_off_chain.py` — skip `p.role is Role.F`.
- `backend/app/services/schedule_violation_checker.py` — `check_consecutive`: skip uids whose role is F (pass roles dict; already available).
- `backend/app/services/demo_user_seed.py` — convert 2 demo T users (c, d) → `Role.F` for coverage.
**Create:**
- `backend/alembic/versions/0005_add_role_f.py` — PG `ALTER TYPE role ADD VALUE IF NOT EXISTS 'F'`; SQLite no-op.

## Implementation Steps
1. `enums.py`: add `F = "F"` after `A`; update `is_flexible` to include `Role.F`. Do NOT add to `is_admin`/`is_fixed`.
2. `role_codes.py`: add `Role.F: (AttendanceCode.AD, AttendanceCode.X)` to `ROLE_CODES`.
3. `constraints_consecutive.py::add`: `for p in inp.people:` → `if p.role is Role.F: continue` (import Role). Same in `constraints_off_chain.py::add`.
4. `schedule_violation_checker.py::check_consecutive`: skip `uid` where `roles.get(uid) is Role.F`.
5. `demo_user_seed.py`: change specs c,d to `Role.F`.
6. Migration 0005: `down_revision="0004"`; `upgrade`: if PG `op.execute("ALTER TYPE role ADD VALUE IF NOT EXISTS 'F'")`; else pass. `downgrade`: raise NotImplementedError (enum value removal unsafe) — document.
7. Run `python -c "import app.main"` + `alembic upgrade head` on a scratch PG (or note) to confirm importable.

## Todo List
- [ ] enums F + is_flexible
- [ ] role_codes F domain
- [ ] consecutive skip F
- [ ] off_chain skip F
- [ ] violation_checker consecutive skip F
- [ ] demo seed 2×F
- [ ] migration 0005
- [ ] compile import check

## Success Criteria
- `Role.F` importable; `codes_for(Role.F) == (AD, X)`.
- Engine solve with an F person yields only AD/X, respects weekly-off, ignores consecutive (unit test in P09).
- `alembic upgrade head` succeeds on fresh PG; F row insertable at runtime.

## Risk Assessment
| Risk | L×I | Mitigation |
|------|-----|-----------|
| PG `ADD VALUE` inside alembic tx unusable same-tx | Med×Low | Migration only adds value, never inserts F rows; runtime insert is a later tx. PG12+ ok. |
| Missed a `Role.A`-only site that should include F | Low×Med | Grep audit done (staffing/comp/objectives are A-only by design; F correctly excluded). |
| off_chain dropped → F gets long OFF runs | Med×Low | Intended per owner "only weekly-off"; weekly-2-off still caps X per block. Flag Q(h). |
| SQLite CHECK constraint for enum on test DB | Low×Low | Tests create_all from current enum → F included; migration SQLite branch no-op. |

## Security Considerations
- F is non-admin (`is_admin` False) → cannot reach `AdminUser` routes. No privilege escalation.
- No PII added.

## Next Steps
Unblocks P02 (self-arrange needs F domain/exemption), P08 (role F UI), P09 (tests).

## Unresolved
- (a) F domain {AD,X}? (h) drop off-chain for F? (g) F self-registerable?
