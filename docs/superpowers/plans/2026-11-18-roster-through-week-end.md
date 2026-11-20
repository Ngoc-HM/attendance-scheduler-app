# Plan — a month's roster runs to the end of its last week

Owner rule, confirmed 2026-11-18 ("Đúng, làm đi").

## The rule, in the owner's words

- Generating a month also plans the days of the next month up to the Sunday
  that ends the month's last week. November 2026 ends on Monday the 30th →
  the roster runs to Sunday 6 December. October 2026 ends on Saturday the
  31st → it also plans Sunday 1 November. A month that ends on a Sunday has
  no such days.
- Those extra days ("carried days") take their flight count by weekday when
  the next month's flight plan is not entered yet ("số lượng chuyến bay đối
  chiếu theo thứ, thường nó sẽ cố định"). Real flight data for a day wins
  when it exists.
- Generating the next month keeps the carried days exactly as they are and
  continues after them ("check xem lịch đã được ấn định tháng trước có mấy
  ngày của tháng tạo lịch rồi thì tạo tiếp theo").
- Publishing a month publishes its carried days too: staff see them at
  once, and the month's roster download (customer workbook layout) prints
  them.
- Rules counted per month stay per CALENDAR month; the carried days count
  in their own month as facts already decided.

## Design (decided by the lead — follow it unless it cannot work; then stop and report)

### Storage: a cell stays in the schedule of its calendar month
- Carried days are `ShiftAssignment` rows of the NEXT month's
  `MonthlySchedule` (created as a draft when it does not exist yet), marked
  with a new boolean `carried` (migration after the latest one; default
  false). Every month-scoped feature (re-check, attendance, time clock,
  leave written into the roster, swaps, reports, dashboard) keeps working
  because a cell is still found through its own month.
- A schedule whose cells are ALL carried counts as "not generated yet":
  Generate needs no force for it, the dashboard shows it as not created,
  and the autorun treats it as missing.

### Generation window for month M
- Days of M (the carried ones pinned to their stored cells) plus the days
  of M+1 up to the Sunday ending M's last week.
- Carried cells of M are hard facts: never rewritten, never re-planned,
  admin edits on them kept. A carried code outside the person's solver
  domain (AL, S, A/D, T, B …) must not break the model: an off-type code is
  pinned as rest and treated like approved leave for the counts; a working
  code is pinned as a working day. The stored cell is never overwritten.
- Month-counted rules apply per calendar month inside the window:
  - ordinary X entitlement (groups A, T, M): M's days get M's target as
    today (carried X count); the M+1 days get NO minimum of ordinary X and
    at most as many X per person as they contain Saturdays and Sundays
    (soft, with slack, same leave adjustment, mirrored in the re-check).
    December then counts its carried days as facts and makes up the rest
    over its own remaining days. (Corrected 2026-11-18: an exact count on
    the sub-list forced every tail of one to five days below the flights'
    cover with four group-A people.)
  - comp days owed (CD): granted inside M only; no CD on the M+1 days.
  - at least two pure A days (group A): counted over M.
- Rules that run along the calendar need no change, they just see more
  days: max 5 working days in a row, max 3 rest days in a row, flight
  staffing per day, group F (duty per day, two X per Monday–Sunday week —
  every week in the window is now complete, the first one read through the
  previous month's codes as today), and the objectives.
- Inputs must cover the whole window: approved leave, annual-leave days,
  holidays and flight pairs of the M+1 days. Flight pairs of an M+1 day
  without a `FlightDay` row: the count of the most recent earlier day of
  the same weekday that has one (look back up to five weeks); none → 0.
- Regenerating M (force): the M+1 carried days are re-planned with it,
  UNLESS M+1 has already been generated (has non-carried cells) — then M+1
  is left untouched and only M's own days are re-planned; breaches this
  creates in M+1 are reported through the existing "following month"
  warnings.

### Reading and publishing
- `GET /schedules/{year}/{month}` also returns the carried cells that M's
  generation put into M+1 (a separate list, e.g. `carry_assignments`), so
  the month view and the roster download show M through its last Sunday.
- Visibility of month M+1 for employees while its own schedule is still a
  draft: only its carried cells, and only when month M is published.
  Published M+1 → everything, as today.
- The roster grid (admin and employee) shows the carried days of the next
  month as extra rows after the month's last day, dated day/month, same
  cell style. The grid must place cells by DATE, not by list position (a
  person with cells for only some days is currently drawn shifted to the
  top — fix that as part of this work).
- The roster download in the customer's workbook layout prints the carried
  days after the last day of the month, same row layout.

## Not in scope
- No change to the rules themselves, to check-in/out, or to leave windows.
- No new buttons or labels in the app beyond the extra day rows.

## Acceptance
1. Usual flight plan (two pairs a day, one on Tuesday and Friday), people:
   4 A, 2 F, 2 T, 1 M. Generate November 2026 → cells from 1 Nov to 6 Dec,
   December schedule exists as a draft holding only 1–6 Dec marked carried,
   no rule violation, group F keeps its weekly swap across 30 Nov–6 Dec.
2. Generate December 2026 after it → 1–6 Dec unchanged cell for cell, the
   rest planned, runs to 3 Jan 2027, no violation; every A/T/M person has
   as many X in December as it has Saturdays and Sundays.
3. A carried day without flight data takes the weekday's usual count; one
   with data uses it.
4. Employee: with November published and December a draft, December shows
   exactly 1–6 Dec; with November a draft, nothing.
5. Regenerate November with December already generated → December
   untouched.
6. The re-check of each month on the persisted cells agrees with the
   generator (no new violation types appear only in the re-check).
7. Full backend suite, ruff, mypy, flutter analyze and flutter test pass.

## Amendment 2026-11-20 (decision #74)

"Regenerating M … UNLESS M+1 has already been generated — then M+1 is left
untouched" is replaced: a generated next month that is still a draft gets
its carried days re-planned by M (the rest of it stays; breaches are
reported as next-month warnings). Only a published next month is left
untouched. Reason: with months generated out of order the carried days
never appeared.
