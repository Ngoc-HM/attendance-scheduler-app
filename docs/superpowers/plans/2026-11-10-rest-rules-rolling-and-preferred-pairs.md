# Rest rules: rolling 7 days, preferred pairs, fair turns (2026-11-10)

> Amended on 2026-11-12 (decision #64): the rolling "2 rest days in ANY 7
> consecutive days" rule described below became a calendar-week rule (at
> most 5 working days per Monday–Sunday week) next to "no more than 5
> working days in a row"; the good pairs now take turns with a 12-month
> memory; a third group-A person is kept in reserve on flight days. The rest of this plan stands as the record of 2026-11-10.

Owner rulings of 2026-11-10, taken in one working session, and the design
that follows from them. This replaces the fixed 7-day blocks of the month.

## What the owner said

1. "Miễn sao 7 ngày liên tục không làm việc quá 5 ngày là được, không nhất
   thiết phải trong 1 tháng. Nếu tháng trước không có [dữ liệu] thì mặc định
   không quan tâm." — the rest rule is: in ANY 7 consecutive calendar days
   nobody works more than 5, across month boundaries, ignoring days with no
   history.
2. There is no rule that the month's leftover days (29–31) need a day off.
3. "Ưu tiên các nhân sự nghỉ T6–T7, T7–CN, CN–T2 để đảm bảo nếu được nghỉ họ
   được nghỉ 2 ngày liên tiếp, theo mức độ ưu tiên lần lượt 1, 2, 3, đảm bảo
   không tị nạnh ai." — days off come as two consecutive days, preferred in
   the order Fri+Sat, then Sat+Sun, then Sun+Mon, and the good pairs are
   shared out fairly.
4. "Code cũ làm ngon vụ chia này rồi" — reuse the approach of the removed
   `objective_weekend.py` (commit `4ada352`, 2026-06-15; deleted in `dee0f96`,
   2026-06-25): calendar-based adjacent-pair rewards by weekday, next to the
   premium-off fairness with its carry across months.

## Rules after the change

Kept exactly as they are (all soft with slack, decision #2):

- `rolling_seven_min_two_rest` — at most 5 working days in every rolling 7
  calendar days; the six days before the month come from history, a day with
  no history counts as not worked (already so).
- `max_consecutive_working` (+ carry) — implied by the rolling rule, kept as
  a second, clearer message.
- `max_consecutive_off`, `flight_staffing`, `comp_day_*`,
  `role_a_minimum_a_days`, the pins of approved leave.

Removed:

- `two_days_off_per_week` — the "exactly 2 X per block 1–7, 8–14, …" quota,
  the pro-rated leftover block, and with them `SolverInput.weeks`,
  `calendar_utils.build_weeks` / block targets wherever nothing else needs
  them, `schedule_violation_checker.check_off_quota`, the two
  `schedule.violation.two_days_off_per_week_*` texts.

Consequences the owner was told about:

- An approved leave day is a rest day for the 7-day rule like any other.
  Leave on working days does not reduce the month's X (decision #4 in a new
  form: per month instead of per block).
- How many X a person gets follows the customer's paper roster (WR JUL26:
  "TTL 23 WORKING DAYS", 8 X for every person, with or without leave): the
  number of Saturdays and Sundays of the month, the same for every role. A
  weekend day inside an approved leave is one of them. The 7-day rule may
  add a day when a person's rhythm needs it.

## Soft objectives (what shapes the days off)

Existing, unchanged: `individual_shift_gap` 300, `balance_shifts` 100,
`premium_off` 30 (fair share of Sat/Sun/holiday X, with carry).

New or changed (weights are starting points — tune them on the scenarios in
"Acceptance", keep the stated order of priority, justify the final numbers in
`objectives.py`):

| key | meaning | weight (final) |
|---|---|---|
| `monthly_off_target` | per person, the distance between the X the engine chooses and the month's target: the number of Saturdays and Sundays in the month, minus the person's pinned leave days that fall on one | 1000 per day |
| `group_cover` | per role group of 2+ people and per day: penalty when every member is off | 200 |
| `off_pairing` | calendar-based: 1 point per X next to another X, plus the weekday bonus Fri+Sat +3, Sat+Sun +2, Sun+Mon +1; a pair may start on the previous month's last day (history) | 15 per point |
| `pair_points_fair` | reward for the weekday-bonus points of the least-served member of a role group (max-min: penalising the spread levelled everyone down to weekday pairs) | 20 per point |

Found while building (2026-11-10): within one month a person's day-off
pattern can only move EARLIER in the week — moving it later would need 6
working days in a row or an extra day off. So with a fixed number of X the
good pairs cannot rotate inside a month (two people of one group: one keeps
Fri+Sat all month, the other a weekday pair). The turns even out across
months through `premium_off`'s carry of Sat/Sun X; a carry of pair points
would make that sharper and is not built.

Invariants the weights must respect:

- `monthly_off_target` outranks every other soft term: nobody gets a free
  day off, or loses one, for balance or for a nicer pair. Only the rolling
  rule (slack) may push a person's count above the target.
- Rest rules, staffing and comp days are slack (10 000 / 2 000): no soft term
  may buy a violation in the two-phase solve.
- A/D balance of group A stays above the day-off preferences.

Only X the engine CHOOSES counts in `monthly_off_target`, the
`off_pairing` bonus and `pair_points_fair` (ruling R2: pinned approved leave
is not a perk and not a choice).

## Self-arrange (employee moves own days off)

> Built as described, then the whole self-arrange feature was removed later
> the same day (owner, decision #63). Kept here as the record of the plan.

Blocks are gone, so the batch rule becomes:

- the number of X in the month stays the same (move, never add or remove);
- the batch must not create a `rolling_seven_min_two_rest` or
  `max_consecutive_working` violation for the requester that was not there
  before (checked with the same re-check code, history included).

Server: `self_arrange_service._validate_weekly_off` → replaced; error key
kept, text updated (en + vi). Client: `SelfArrangeState.blockOffCounts` /
`draftKeepsQuota` → month X count unchanged + no 7-day window of own cells
with more than 5 working days; the 7-day rows remain as layout only, the
per-row "X n/m" badge becomes one month badge.

## Acceptance (tests; solver tests that compare plans pin `num_workers=1`)

1. November 2026 shape — 4 group-A people, 21 two-pair days and 9 one-pair
   days as in the owner's data, 3 F, 2 M: fewer `flight_staffing` violations
   than the block model's 3; no rest-rule violation; nobody works 6 days in a
   row; every rolling 7-day window has ≥ 2 rest days.
2. Days off come in pairs: with a feasible load, no person has an isolated
   single X (except where staffing proves it impossible — assert on a
   scenario without staffing pressure).
3. Preference order: a lone person with no staffing floor gets Fri+Sat every
   week; when Fri+Sat is impossible (pinned work/leave), Sat+Sun; then
   Sun+Mon.
4. Fair turns: 3 people of one group over a 4-week month with `group_cover`
   on — each gets at least one Fri+Sat pair and the weekday-bonus points
   differ by at most one pair's worth.
5. Group cover: 2 M and 3 F never all off on the same day when avoidable.
6. Month target: every person's chosen X equals the number of Saturdays
   and Sundays of the month (November 2026: 9, July 2026: 8) when the
   rolling rule allows, for A, F, T and M alike; approved leave on three
   working days and the weekend in between gives target − 2.
7. Month boundary: history ending in 4 worked days → at most 1 more working
   day before a rest; no history → no constraint from before the month.
8. Engine and re-check agree (`test_engine_checker_agreement.py`).
9. Self-arrange: moving a pair is accepted; adding or removing an X is
   rejected; a move that creates a 6-day working run is rejected.

## Files

Backend: `scheduler/calendar_utils.py`, `constraints.py`,
`constraints_off_days.py` (delete), `objectives.py`,
`objective_off_pairing.py` (rewrite, calendar-based),
`objective_tail_off.py` (→ `spare_day_off`), new small `objective_*` modules
for cover / fairness, `domain.py` (`weeks`), `services/schedule_input_builder.py`,
`schedule_service.py`, `schedule_violation_checker.py`,
`self_arrange_service.py`, `core/i18n.py`, tests.
Client: `features/schedule/presentation/providers/self_arrange_provider.dart`,
`widgets/self_arrange_week_blocks.dart`, i18n, tests.
Docs: `PROJECT_OVERVIEW.md` §5.1 / §5.3 #2–#3 / §5.4 #8,
`docs/design-decisions.md` (new row superseding #4, #7, #16 and open
questions D2, D5, D6), `docs/project-changelog.md`, `docs/codebase-summary.md`.
