# Scheduler role-aware rebuild

Owner-confirmed model (2026-06-26). Fixes the "all-A, D=0" bug: the WIP refactor
removed O/D and scheduled every role with A/D. Real WR JUL26 shows only role A
is flight-scheduled; M/T are flexible. "Ràng buộc vào role A."

## Role → code domain (per-person var domain)
- **A** (fixed group, A1–A4): `{A, D, A/D, X, CD}`. Full §5.3 constraints.
- **T** (flexible): `{AD, X}` — every working day = AD (full day, no shift split, no comp). Still 2 X/week.
- **M** (admin): `{O/D, X}` — working day = O/D (office). Still 2 X/week.

## Role A rules
- **Per-person A ≈ D mandatory**: each role-A person's A-count ≈ D-count within the month (strong). (A/D counts toward both.)
- **Cross-people balance** (F-08): minimise spread of A and of D across role-A people.
- **A/D** double shift = last resort only (sick cover), heavy penalty.
- Flight staffing demand (DEMAND table) scoped to role A only.
- Respect approved leave / annual long-leave pins (unchanged).

## Constraint scoping
- staffing (flight A/D), balance (A≈D + spread), ad_usage, comp_days → **role A only**.
- off_days (2 X / 7-day block), consecutive (max 5 working), off_chain → **all roles**, role-safe (working = person's non-{X,CD} codes).
- O/D and AD restored as auto-assignable (per role).

## Files
engine.py (per-role var domains) · constraints.py (one_status_per_day per role) ·
constraints_staffing.py (role-A sum) · objective_balance.py (role-A + per-person A≈D) ·
objectives.py (ad_usage role-A) · constraints_off_days/consecutive/off_chain/comp_days
(role-safe `if key in x`) · new role_codes helper · tests.

## Verify
pytest scheduler tests + a sample solve (4 A + 3 T + 2 M, a month, flights on some
days): role-A → balanced A/D, T → AD, M → O/D, everyone ≥2 X/week.
