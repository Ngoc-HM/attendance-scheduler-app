# Session report — Phases 01–05 complete (2026-06-11)

Plan: `plans/260611-1941-full-implementation/` — 5/12 phases done, backend test suite **78/78 green**.

## Done this session
| Phase | Result |
|---|---|
| 01 Foundation | `carry_premium_off`, `ShiftChangeRequest`+`SwapKind`, 7-day-block weeks + `partial_block_off_target`, holiday=workday docstring, Alembic 0001 baseline + 0002 delta; dev DB stamped+upgraded; fresh-DB path verified on tmp DB |
| 02 Flights (F-04) | CRUD + Excel import (openpyxl, row-errors, no partial commit), pair derivation 37↔36/31↔30→0/1/2, `flight_pairs_map`; 19 tests |
| 03 Leaves+Swaps (F-05/06,#8) | windows (1–20 of M for M+1; annual prior-year), classify ≥5d→annual, approve/reject + balance decrement, conflict resolver (carry_comp), `approved_off_map`, shift-change create/list/decide + strict_review; 27 tests |
| 04 Engine (§5) ⭐ | CP-SAT: uniform vocab {A,D,A/D,O/D,X}; HARD exactly-one+pins; SOFT+slack: 2X/block (target += pinned AL), ≤5 consecutive (+carry_streak boundary), staffing equality (A/D covers both, demand fixed-group only); objectives balance(100)>premium(30)>weekend(10), ad_usage 1000, slack BIG 10000; SlackRegistry→Violations. Verified: full-staff month 0 violations, spread≤1, auto A/D when 20<21 worker-days (real §5.3#6 case!), understaffed→full grid+violations+suggestion. 17 engine tests |
| 05 Schedule service (F-07/08/09,#9) | `schedule_input_builder` (ORM→SolverInput), generate (restore AL on pinned cells, regen guards published/overrides/force), get (G4: non-admin published-only), manual_override (save-always+recheck warnings), publish, `apply_shift_change` (change_code/swap_with + recheck; no-schedule→409), `schedule_violation_checker` (pure), day-20 autorun (APScheduler, 02:00, never clobbers) + config flags; integration tests incl. full pipeline |

## Deviations from plan (documented in phase files)
- Engine: uniform vocabulary thay vì per-person sets (đơn giản hơn, staffing equality chặn spurious flight codes ngày 0-pair); conflict_priority bỏ khỏi solver (xử lý ở leave layer).
- 2 test seam của phase 03 cập nhật theo semantics phase 05 (duyệt swap khi chưa có lịch = 409, không phải warning).

## Next: Phase 06 (xem mục Next-phase plan trong báo cáo chat)
Phases left: 06 attendance/sick/holidays → 07 calculations → 08 reports → 09 Flutter (lớn nhất) → 10 GDPR → 11 testing → 12 docs.

## Unresolved questions
- Mẫu Excel "WR JUN26" thật (importer đã document layout kỳ vọng).
- Betriebsrat (§9.2) — chặn deploy production.
- CD carry một phần? (phase 07 giả định carry toàn phần, floor 0).
