# Design Decisions

Owner-confirmed decisions that shape the system. Several **override the spec**
(`PROJECT_OVERVIEW.md`) — do NOT "fix" these back without re-confirming with the
customer. Recorded 2026-06-11.

| # | Decision | Rationale | Spec relation |
|---|----------|-----------|---------------|
| 1 | **Scheduler = OR-Tools CP-SAT**, rule-based, no ML/AI | Right tool for shift-rostering; tiny instance solves in ms | §2, §9.6 (EU AI Act) |
| 2 | **Always-feasible / slack architecture**: staffing & off-day rules are SOFT with heavily-penalized slack vars (weight 10 000); only "exactly one status/day" + approved-off pins stay HARD. `slack > 0` → a `Violation` | The engine must never "die silently"; it returns a complete schedule plus the list of broken rules for admin review | §5.6 #12–14 |
| 3 | **Engine schedules everyone with role-specific domains**: A→`{A,D,X,CD}`, T/F→`{AD,X}`, M→`{O/D,X}`; flight demand counts only role A | Prevents codes belonging to one role from leaking into another role's automatic roster | §3, §5.3 #4 |
| 4 | **"2 days off (X) per week" is counted SEPARATELY from approved leave (AL/CD)** — the block target is raised by the number of pinned leave days, so a week with leave still gets its 2 genuine X | Owner: leave is not a substitute for the weekly rest entitlement | §5.3 #2 |
| 5 | **Holidays (PH) = NORMAL WORKING DAYS** — never auto-pinned off. Holiday rows are *premium-off markers* only | **OVERRIDES** spec F-13/§7 ("PH = X = off"). Owner decision: weekends/holidays are worked; being *off* on one is the perk (see #6) | F-13, §7 |
| 6 | **Premium-off fairness across months**: an OFF landing on Sat/Sun/holiday is "premium"; `users.carry_premium_off` accumulates and a soft objective (weight 30) balances it so the perk rotates | Owner: whoever already enjoyed premium offs yields to others next period | extends §5.4 #8 |
| 7 | **Week quota uses 7-day blocks anchored at day 1**, plus a separate rule requires at least 2 rest days in **every rolling 7 calendar days**, including windows crossing month boundaries | Preserves the owner's block layout while preventing 2 workdays at month end followed by 5 more at the start of the next month | §5.1, §5.3 #2/#3 |
| 8 | **Shift-change requests = full feature**: a user requests `change_code` or `swap_with` on their OWN cell → admin decides → applied to the schedule with a hard-rule re-check. A1–A4 requests carry a `strict_review` flag | Implements §3 "fixed can request but admin may refuse; flexible request freely" | §3 |
| 9 | **Day-20 autorun** (APScheduler, 02:00, config `AUTORUN_*`): closes M+1 registration and generates next month's DRAFT, never clobbering an existing schedule. Manual generate always available | Implements the "day 20 closes & schedules" rule without removing admin control | §4.3 / F-07 |
| 10 | **Leave registration cycle**: during month M, days 1–20, users register for month M+1 | Concrete reading of "register early month, close on the 20th" | §4.3, §7 |
| 11 | **Max 5 consecutive OFF days** (soft): the scheduler keeps ordinary off-runs (weekly X + monthly leave/CD) to ≤5 in a row; a run of >5 (≥6) off must be registered ANNUAL leave, which is exempt from this rule. Classification threshold also moved to >5 (≥6) → annual | Customer clarification 2026-06-12 ("các ngày nghỉ nối lại quá 5 ngày liên tục phải đăng ký nghỉ năm") | §4.3/F-06 (refines "≥5"→">5") |
| 12 | **Role F is T-like for rest rules** (2026-07-22): F obeys BOTH the weekly-2-off rule AND the max-5-consecutive-working / max-5-consecutive-OFF rules — exactly like T. Supersedes the 2026-07-09 "F = weekly-2-off only" exemption, which let offs cluster at 7-day-block edges and produced 6+ consecutive working days before 2 off | Owner 2026-07-22: "F giống y hệt T; tuần nghỉ 2 ngày thì làm tối đa 5 ngày" | §5.3 #2/#3 |
| 13 | **Role-A compensation is derived from effective history**: every A/D earns 1 CD in the next month; actual attendance overrides the planned cell, and AD for non-A roles earns nothing | Makes next-month compensation automatic without a manual month-close step | §5.3 #6, F-14 |
| 14 | **Per-person role-A distribution**: on a full-month run every role-A person gets at least 2 pure A days; the objective minimizes that person's own `|A total - D total|` subject to flight demand | Prevents one role-A person receiving almost only D duties | §5.4 #7 |
| 15 | **Automatic role-A scheduling NEVER assigns A/D**: the solver domain is only `{A,D,X,CD}`. A/D is allowed only after the roster exists to cover a real unexpected absence (for example sickness), and then earns next-month CD | A planned double shift must not be imposed merely to make the generated roster fit | §5.3 #6, F-10 |

## Objective weights (engine)
`Minimize( slack·10000 + individualADGap·300 + balanceAD·100 + premiumOff·30 + weekendPair·15 )`.
Slack dwarfs the balancing objectives. When ordinary A/Duty staffing is
insufficient, the generated roster reports a violation instead of creating
an A/D double shift.

## Migration strategy
Alembic is authoritative (`0001` baseline, `0002` adds `carry_premium_off` +
`shift_change_requests`). `create_all` is kept ONLY for fresh-DB convenience and
never ALTERs existing tables; existing dev DBs are stamped at `0001` then
upgraded.

## Open questions (confirm with customer)
- Partial-week off-target rounding (decision #7).
- Whether M/T appear in the A/D balance objective (currently fixed-group only).
- Real "WR JUN26" Excel layout for the importer.
- Betriebsrat (§9.2) presence — production-deploy gate.
