# Design Decisions

Owner-confirmed decisions that shape the system. Several **override the spec**
(`PROJECT_OVERVIEW.md`) — do NOT "fix" these back without re-confirming with the
customer. Recorded 2026-06-11.

| # | Decision | Rationale | Spec relation |
|---|----------|-----------|---------------|
| 1 | **Scheduler = OR-Tools CP-SAT**, rule-based, no ML/AI | Right tool for shift-rostering; tiny instance solves in ms | §2, §9.6 (EU AI Act) |
| 2 | **Always-feasible / slack architecture**: staffing & off-day rules are SOFT with heavily-penalized slack vars (weight 10 000); only "exactly one status/day" + approved-off pins stay HARD. `slack > 0` → a `Violation` | The engine must never "die silently"; it returns a complete schedule plus the list of broken rules so the admin can fix them (A/D fallback / manual edit) | §5.6 #12–14 |
| 3 | **Engine schedules everyone** (incl. M/admins) with one vocabulary `{A, D, A/D, O/D, X}`; flexible-vs-fixed lives in the leave/swap layer, not the solver. M/T are steered to O/D on working days; flight-duty demand counts only the fixed group A1–A4 | Keeps the model uniform & simple; matches "A1–A4 strict, M/T flexible" by handling change-requests downstream | §3, §5.3 #4 |
| 4 | **"2 days off (X) per week" is counted SEPARATELY from approved leave (AL/CD)** — the block target is raised by the number of pinned leave days, so a week with leave still gets its 2 genuine X | Owner: leave is not a substitute for the weekly rest entitlement | §5.3 #2 |
| 5 | **Holidays (PH) = NORMAL WORKING DAYS** — never auto-pinned off. Holiday rows are *premium-off markers* only | **OVERRIDES** spec F-13/§7 ("PH = X = off"). Owner decision: weekends/holidays are worked; being *off* on one is the perk (see #6) | F-13, §7 |
| 6 | **Premium-off fairness across months**: an OFF landing on Sat/Sun/holiday is "premium"; `users.carry_premium_off` accumulates and a soft objective (weight 30) balances it so the perk rotates | Owner: whoever already enjoyed premium offs yields to others next period | extends §5.4 #8 |
| 7 | **Week = 7-day blocks anchored at day 1** (1–7, 8–14, …), NOT Monday–Sunday. Final partial block target X = `round(k/7*2)` | Owner preference; consistent, simple month partition | §5.1 (week definition) — *confirm partial-block rounding with customer* |
| 8 | **Shift-change requests = full feature**: a user requests `change_code` or `swap_with` on their OWN cell → admin decides → applied to the schedule with a hard-rule re-check. A1–A4 requests carry a `strict_review` flag | Implements §3 "fixed can request but admin may refuse; flexible request freely" | §3 |
| 9 | **Day-20 autorun** (APScheduler, 02:00, config `AUTORUN_*`): closes M+1 registration and generates next month's DRAFT, never clobbering an existing schedule. Manual generate always available | Implements the "day 20 closes & schedules" rule without removing admin control | §4.3 / F-07 |
| 10 | **Leave registration cycle**: during month M, days 1–20, users register for month M+1 | Concrete reading of "register early month, close on the 20th" | §4.3, §7 |
| 11 | **Max 5 consecutive OFF days** (soft): the scheduler keeps ordinary off-runs (weekly X + monthly leave/CD) to ≤5 in a row; a run of >5 (≥6) off must be registered ANNUAL leave, which is exempt from this rule. Classification threshold also moved to >5 (≥6) → annual | Customer clarification 2026-06-12 ("các ngày nghỉ nối lại quá 5 ngày liên tục phải đăng ký nghỉ năm") | §4.3/F-06 (refines "≥5"→">5") |

## Objective weights (engine)
`Minimize( slack·10000 + balanceAD·100 + premiumOff·30 + weekendPair·10 + adUsage·1000 + nonFixedFlightDuty·1 )`.
Balance of A/D shifts is the top *soft* priority (§5.4 note); slack dwarfs all
so it is only ever used under a genuine shortage. A/D ("bất đắc dĩ" double
shift, §5.3 #6) carries its own discouragement so the solver prefers real
coverage but reaches for A/D before leaving a shift uncovered.

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
- Whether comp days (CD) may partially carry across months.
