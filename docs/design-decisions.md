# Design Decisions

Owner-confirmed decisions that shape the system. Several **override the spec**
(`PROJECT_OVERVIEW.md`) — do NOT "fix" these back without re-confirming with the
customer. Recorded 2026-06-11; amended 2026-11-07 with the owner's decisions of
2026-11-06 (D1–D8 in `docs/superpowers/specs/2026-11-06-review-remediation-spec.md`)
and the review remediation that followed (#24–#38).

| # | Decision | Rationale | Spec relation |
|---|----------|-----------|---------------|
| 1 | **Scheduler = OR-Tools CP-SAT**, rule-based, no ML/AI | Right tool for shift-rostering; tiny instance solves in ms | §2, §9.6 (EU AI Act) |
| 2 | **Always-feasible / slack architecture**: staffing & off-day rules are SOFT with heavily-penalized slack vars (weight 10 000); only "exactly one status/day" + approved-off pins stay HARD. `slack > 0` → a `Violation` | The engine must never "die silently"; it returns a complete schedule plus the list of broken rules for admin review | §5.6 #12–14 |
| 3 | **Engine schedules everyone with role-specific domains**: A→`{A,D,X,CD}`, T/F→`{AD,X,CD}`, M→`{O/D,X,CD}` (`scheduler/role_codes.py`); flight demand counts only role A. CD joined the T/F/M domains on 2026-11-06 because holiday work earns a comp day for every role (#5, #13) | Prevents codes belonging to one role from leaking into another role's automatic roster | §3, §5.3 #4 |
| 4 | **"2 days off (X) per week" is counted SEPARATELY from approved leave (AL/CD)** — the block target is raised by the number of pinned leave days, so a week with leave still gets its 2 genuine X | Owner: leave is not a substitute for the weekly rest entitlement (re-confirmed 2026-11-06, D5: keep as coded) | §5.3 #2 |
| 5 | **Holidays (PH) = NORMAL WORKING DAYS** — never auto-pinned off. Holiday rows are *premium-off markers* (#6) and, since 2026-11-06, *comp-day triggers*: anyone of **any role** who works on a holiday (any working code: A, D, A/D, AD, O/D, T, B) earns **+1 CD**, which the engine schedules in the next generated month (#13). Only holidays on or after `HOLIDAY_COMP_EFFECTIVE_FROM` (default 2026-11-06) earn it, so a live database does not suddenly owe back-dated CDs | **OVERRIDES** spec F-13/§7 ("PH = X = off"). Owner decision: weekends/holidays are worked; being *off* on one is the perk (see #6); working one is compensated (owner D1, confirmed twice on 2026-11-06) | F-13, §7, §5.3 #6 |
| 6 | **Premium-off fairness across months**: an OFF landing on Sat/Sun/holiday is "premium"; `users.carry_premium_off` accumulates and a soft objective (weight 30) balances it so the perk rotates | Owner: whoever already enjoyed premium offs yields to others next period | extends §5.4 #8 |
| 7 | **Week quota uses 7-day blocks anchored at day 1**, plus a separate rule requires at least 2 rest days in **every rolling 7 calendar days**, including windows crossing month boundaries | Preserves the owner's block layout while preventing 2 workdays at month end followed by 5 more at the start of the next month | §5.1, §5.3 #2/#3 |
| 8 | **Shift-change requests = full feature**: a user requests `change_code` or `swap_with` on their OWN cell → admin decides → applied to the schedule with a hard-rule re-check. A1–A4 requests carry a `strict_review` flag | Implements §3 "fixed can request but admin may refuse; flexible request freely" | §3 |
| 9 | **Monthly autorun** (APScheduler, daily check at **00:05 in `TIMEZONE`**, default Europe/Berlin; config `AUTORUN_ENABLED`, `AUTORUN_DAY` default 20): registration for M+1 stays open through the whole of day `AUTORUN_DAY`; at 00:05 on day **`AUTORUN_DAY + 1`** (default the 21st) the job generates next month's DRAFT, skipping a month that already has a schedule (it never clobbers a draft or published one). The autorun and the leave window read the date from `core/business_time.business_today()` (the business date in `TIMEZONE`), not the host clock, so a UTC container does not slip a day. Manual generate always available | Implements the "day 20 closes & schedules" rule without losing leave registered on the last day and without removing admin control (amended 2026-11-06, B8; was 02:00 on day 20) | §4.3 / F-07 |
| 10 | **Leave registration cycle**: during month M, days 1–`AUTORUN_DAY` (default 20), users register for month M+1 (#31) | Concrete reading of "register early month, close on the 20th" | §4.3, §7 |
| 11 | **Max 5 consecutive OFF days** (soft): the scheduler keeps ordinary off-runs (weekly X + monthly leave/CD) to ≤5 in a row; a run of >5 (≥6) off must be registered ANNUAL leave, which is exempt from this rule. Classification threshold also moved to >5 (≥6) → annual | Customer clarification 2026-06-12 ("các ngày nghỉ nối lại quá 5 ngày liên tục phải đăng ký nghỉ năm") | §4.3/F-06 (refines "≥5"→">5") |
| 12 | **Role F is T-like for rest rules** (2026-07-22): F obeys BOTH the weekly-2-off rule AND the max-5-consecutive-working / max-5-consecutive-OFF rules — exactly like T. Supersedes the 2026-07-09 "F = weekly-2-off only" exemption, which let offs cluster at 7-day-block edges and produced 6+ consecutive working days before 2 off | Owner 2026-07-22: "F giống y hệt T; tuần nghỉ 2 ngày thì làm tối đa 5 ngày" | §5.3 #2/#3 |
| 13 | **Compensation is derived from effective history for every role** (amended 2026-11-06): each A/D (role A only) earns 1 CD and any working code on a public holiday from `HOLIDAY_COMP_EFFECTIVE_FROM` earns 1 CD for every role (#5); each CD consumes one (`carry_over_math.comp_balance`). Actual attendance overrides the planned cell; AD on an ordinary day earns nothing. CD is in every role's solver domain, but the solver grants CD only against owed comp days (`constraints_comp_days`). Self-arrange cannot set CD. The stored `users.carry_comp` / `carry_streak` / `carry_premium_off` are used only for a user with no history at all | Makes next-month compensation automatic without a manual month-close step | §5.3 #6, F-14 |
| 14 | **Per-person role-A distribution**: on a full-month run every role-A person gets at least 2 pure A days; the objective minimizes that person's own `|A total - D total|` subject to flight demand | Prevents one role-A person receiving almost only D duties | §5.4 #7 |
| 15 | **Automatic role-A scheduling NEVER assigns A/D**: the solver domain is only `{A,D,X,CD}`. A/D is allowed only after the roster exists to cover a real unexpected absence (for example sickness), and then earns next-month CD | A planned double shift must not be imposed merely to make the generated roster fit | §5.3 #6, F-10 |
| 16 | **Weekend preference for the paired offs is dropped** (owner 2026-06-18 / 2026-07-01): `off_pairing` rewards adjacency only; `premium_off` rotates who gets Sat/Sun/holiday offs. Recorded here 2026-09-03 — previously only in code comments | Weekends are ordinary working days (#5/#6); forcing offs onto Sat+Sun contradicted that | **OVERRIDES** §5.4 #8 ordering for the engine. The T7+CN > T6+T7 > CN+T2 order survives only in leave-conflict ranking (#19). Re-opened as D6 (see Open questions) |
| 17 | **Sickness `S` never enters the planned schedule** (2026-09-03): manual override, shift-change and self-arrange reject S (`role_code_validation.validate_planned`); a legacy S of ANOTHER user is masked as X for non-admin readers of `GET /schedules`; S attendance rows never persist a note | The planned grid is visible to every active user; sickness is Art. 9 data. A person still sees their own S in `/attendance/me` (data-subject access) | §9.1 |
| 18 | **Audit is fail-loud** (2026-09-03): a failed audit write returns HTTP 500 and logs the full context; user create/update/delete, account approval, manual flight entry, month-close and the autorun (#9, actor = system) are audited. Known limitation: the business change commits before the audit row, so a failed audit can leave the change persisted with a 500 response | Silent audit loss defeats §9.5 | §9.5 |
| 19 | **Leave-conflict ranking applies all three §5.4 #9 criteria** (2026-09-03): carry_comp → fewer approved offs already held in the touched 7-day block(s) → weekend pairing (Sat+Sun > Fri+Sat > Sun+Mon) → created_at | Was carry_comp only | §5.4 #9, §5.4 #8 |
| 20 | **Retention and data-subject export are code** (2026-09-03): `DATA_RETENTION_MONTHS` (default 36, legal floor 24 per ArbZG §16(2)) drives `POST /compliance/retention/purge`; `GET /compliance/users/{id}/export` returns everything held about a person (self or admin). Erasure = existing `DELETE /users/{id}` | §9.3 data minimization and Art. 15/17/20 rights need a mechanism, not a paragraph | §9.3, §9.5 |
| 21 | **Production guard** (2026-09-03): `ENVIRONMENT=staging|prod` refuses to start while `SECRET_KEY` or `FIRST_ADMIN_PASSWORD` hold the dev defaults (or are too short); the seed-admin password reset is dev-only (`FIRST_ADMIN_RESET_ON_STARTUP`, ignored outside dev). The Docker image defaults to prod | Blocker #1 of the 2026-09-03 review | §9.5 |
| 22 | **`carry_premium_off` is derived from effective history** like comp/streak (2026-09-03); month-close persists the figures for reporting but is no longer a prerequisite for generation | F-14 end-to-end without a manual step | #6, #13, F-14 |
| 23 | **F-09 recheck mirrors every engine rule** (2026-09-03): added ≥2 pure A days, comp-day grant/excess, and ≤5 consecutive off days (annual leave exempt) to the four rules already re-checked | An admin edit could previously break these silently | §5.6 #14 |
| 24 | **Regenerate guard** (2026-11-06, B1): `POST /schedules/generate` answers **409** when the month is published (`schedule.published_locked`) or its draft carries manual edits (`schedule.has_overrides`), unless the request sets `force`. The Flutter Generate action catches the 409, asks the admin to confirm ("Regenerate") and retries with `force`. A forced run resets the month to draft and drops the edits; publishing it again re-syncs still-seeded actuals (#27) | Regenerating used to wipe hand edits and the published state without asking, and employees then got 404 | F-07, F-09 |
| 25 | **Self-registration carries no role** (2026-11-06, B2): `POST /auth/register` has no `role` field (one sent by the client is ignored); the account is created `pending` with role **T**. The admin picks the real role when approving (`POST /auth/users/{id}/approve` with `{"role": ...}`), which works **only on a pending account** (409 `user.not_pending`); role changes of active users go through `PATCH /users/{id}` with the last-admin and fixed-team guards. Approving as another role allocates a new code for that role (the provisional T code is never reused) | A self-registered account could choose role M and become admin on approval. Reverses the 2026-07-09 choice of offering T/F/A at sign-up | F-01, F-03 |
| 26 | **Leave type must match the span** (2026-11-06, B3): the span decides the bucket (≤5 days = monthly, >5 consecutive days = annual, #11); a client-sent `leave_type` that disagrees is refused with **422** `leave.type_span_mismatch`. The Flutter form checks the same rule before submitting | A 10-day leave sent as `monthly` used to dodge the prior-year annual-leave window | F-05, F-06 |
| 27 | **Edits to a published roster reach the seeded actuals** (2026-11-06, B5): a manual override, an approved shift change, an approved self-arrange and a leave decision (#28) on a PUBLISHED month also update the matching attendance row while it is still as seeded (`recorded_by` NULL); a row an admin recorded is never overwritten. Publishing inserts missing actuals and, on a re-publish, re-syncs still-seeded ones | The attendance grid kept the old plan after the roster changed | F-09, F-11 |
| 28 | **Leave decisions are written into existing schedules** (2026-11-06, B4): approving writes AL into the requester's cells in every month of the span that already has a schedule (draft or published; published months also move seeded actuals, #27). Revoking turns back to X **only the cells still on AL** — a CD or a cell re-coded after approval stays. Months not generated yet pick the approval up when generated. The decision returns `leave.schedule_applied`, a note per month not generated yet and each changed month's re-check warnings | Approving after generation used to change nothing but a warning, so the admin had to regenerate and lose edits | F-05, F-06, §5.6 #14 |
| 29 | **One source for carry values** (2026-11-06, B6): `carry_comp`, `carry_streak` and `carry_premium_off` come from `schedule_history.build_boundary_states` (planned cells with actual attendance on top) for the engine input, the F-09 re-check, the leave-conflict ranking (#19) and month-close; month-close only stores them for reporting | The ranking read the stored column, the engine its own history and month-close actuals only, so the three could disagree | F-14, §5.4 #9 |
| 30 | **Annual leave quota and remaining balance** (owner D4, 2026-11-06): each user has an admin-set `annual_leave_quota` (days per calendar year). Migration `0008` adds it (existing users get 30) and drops the never-used `annual_leave_balance`. New users start at `ANNUAL_LEAVE_DEFAULT_DAYS` = **30 — a placeholder until the customer gives the real figure** — unless the admin sets a quota on create; the Users page edits it per person. Remaining = quota − approved leave days in that calendar year (calendar days of every approved request, monthly or annual). `GET /leaves/balance?year=&user_id=` returns quota / used / pending / remaining (own balance; an admin may read anyone's). Approving past the quota is allowed with the **advisory** warning `leave.balance_exceeded`. The Leaves page shows an employee their own days left for the current business year | D4: the customer wants "annual leave left" per person. Nothing is stored, so approve / reject / revoke show up at once | F-06 |
| 31 | **Leave window and autorun share `AUTORUN_DAY`** (2026-11-06, B8): `AUTORUN_DAY` is validated **1–27** so day `AUTORUN_DAY + 1` exists in every month; `leave_windows.registration_last_day()` returns it, so the monthly window (days 1–`AUTORUN_DAY` of the month before) and the autorun (#9) cannot drift apart, and the window-closed error names the real day (`leave.window_closed_monthly` with `{day}`) | The autorun used to fire on day 20 while registration stayed open for the rest of day 20 | §4.3, F-05, F-07 |
| 32 | **Employee-readable directory and window** (2026-11-06, C4/C5): `GET /users/directory` gives any signed-in user the active users' `id`, `code` and `role` only (no names), ordered by code; the roster and the shift-change dialog show people by code. `GET /leaves/window` returns `monthly_open`, `monthly_target_year`/`monthly_target_month`, `annual_target_year`, `closes_on_day` and `enforced` (false in dev, where the window never closes); the Leaves page reads it instead of a hard-coded "open" | Employees saw "User 7" because `/users` is admin-only, and the client claimed registration was always open | §3, §9.1, F-05 |
| 33 | **Maintenance scripts refuse outside dev** (2026-11-06, B9): `scripts/reset_all_passwords.py` and `scripts/seed_demo_users.py` exit with code 2 unless `ENVIRONMENT=dev`, naming the environment and database host; `--allow-non-dev` overrides on purpose | One command could reset every production password to `admin123` | §9.5 |
| 34 | **The off-chain rule counts comp days** (2026-11-06, B7): the engine's ≤5-consecutive-OFF rule (#11) counts every rest code in the person's domain — X (approved leave is pinned as X) and CD — like the post-edit re-check; annual leave stays exempt | The engine counted only X, so a generated roster could fail its own re-check | §4.3, #11, #23 |
| 35 | **Recently-sick cover looks back 30 days** (2026-11-06, B10): when a sick day needs A/D cover, people with an S in the 30 days before it (`RECENTLY_SICK_LOOKBACK_DAYS`, rolling across month boundaries) are forced first, most recent first | The rule used to forget anyone who was sick in the previous month | §6, F-10 |
| 36 | **Flutter session restore** (2026-11-06, C6): at start-up the app signs back in with the stored token. Only a 401/403 drops it; when the server cannot be reached the token is kept for the next start and the login page says the server is unavailable | Users had to log in at every launch, and a backend outage must not sign everyone out | F-02 |
| 37 | **Employee self-service in the client** (2026-11-06, C1/C2/C9): an employee reads their own month on the Attendance page (`GET /attendance/me`, read-only), taps their own roster cells to request a shift change (code change or swap with a colleague picked by code, #32) and follows their requests in a panel under the roster; the Leaves page shows their comp days (`carry_comp`) and annual leave left (#30) | The shift-change dialog existed but nothing opened it, employees had no attendance view, and comp days were hard-coded to 0 | §3, #8, F-11 |
| 38 | **Role gating in the client** (2026-11-06, C3/C7/C8): Generate, Publish, roster cell edits, holiday management, attendance updates and month-close appear only for admins (a signed-out or employee view has none of them, and a non-admin sees a neutral "not published yet" message instead of a Generate hint). The admin's cell editor offers only the planned codes valid for that person's role — never S (#17), CD for every role (#13), A/D for role A only | Every role saw admin buttons that then failed on the server, and the picker offered S and other roles' codes | §3, §9.1 |

## Objective weights (engine)
`Minimize( slack·10000 + compDaySlack·2000 + individualADGap·300 + balanceAD·100 + premiumOff·30 + offPairing·15 )`
— `slack_registry.SLACK_WEIGHT`, `constraints_comp_days.COMP_WEIGHT` and
`objectives.WEIGHTS`. Rule slack (off days, rolling rest, consecutive working,
off-chain, staffing, pure-A days) dwarfs everything; comp-day shortfall/excess
slack sits below staffing (a CD yields to flight cover) but above every
objective. `offPairing` rewards adjacent weekly offs with no weekend bias
(#16). When ordinary A/Duty staffing is insufficient, the generated roster
reports a violation instead of creating an A/D double shift.

## Migration strategy
Alembic is authoritative; head is **`0008`**: `0001` baseline, `0002`
`carry_premium_off` + `shift_change_requests`, `0003` A1–A4 collapsed into A +
`users.code` + `role_code_counters`, `0004` `flight_presets`, `0005` role F,
`0006` `time_clock_entries`, `0007` `self_arrange_requests`, `0008`
`annual_leave_quota` (drops `annual_leave_balance`). `create_all` is kept ONLY
for fresh-DB convenience and never ALTERs existing tables; existing dev DBs are
stamped at `0001` then upgraded.

## Open questions (confirm with customer)

### Owner / customer decisions still open
- **D6 — weekend preference for the paired offs.** Undecided (2026-11-06): the
  owner's answers both asked for T7+CN > T6+T7 > CN+T2 and for keeping the
  code. The engine stays adjacency-only (#16); the order is used only by the
  leave-conflict ranking (#19).
- **D7 — staffing exact vs minimum.** §5.3 #4 is implemented as a MINIMUM
  (`constraints_staffing`). With 4 role-A people and 1 flight pair/day the
  engine legitimately produces days with 2A+2D or 3A+1D, because a role-A
  person who is not off can only carry A or D. If the customer wants "exactly
  1A+1D", decide what the extra role-A person does that day (e.g. a non-flight
  working code such as O/D) and how that day counts. Code unchanged until then.
- **Real annual-leave quota.** `ANNUAL_LEAVE_DEFAULT_DAYS` = 30 and the 0008
  migration default are placeholders (#30).
- **Betriebsrat (§9.2) presence — production-deploy gate.** The time-clock
  check-in/out and self-arrange features (owner 2026-07-09) are outside the
  original spec; check-in/out is behaviour monitoring in the §87(1) No.6 BetrVG
  sense, so the works-council question now covers them.

### Customer notes from the 2026-11 remediation
- Older leave rows whose `leave_type` disagrees with their span are neither
  migrated nor flagged (#26 applies to new requests only).
- Month-close counts planned cells where no actual exists yet; users with no
  history at all keep their stored carry values (#29).
- Recently-sick forced cover now lasts 30 days rolling across months, with no
  "already paid back" release (#35).
- Self-registration no longer offers T/F/A (reverses 2026-07-09); accounts that
  registered earlier and are still pending may carry role M — check the
  production database before deploying (#25).
- Approving a self-registered account as another role leaves a gap in the T
  codes (codes are never reused, #25).
- Deleting a user nulls `recorded_by` on the attendance rows that admin
  recorded, so they look seeded: a later roster edit, re-publish or
  `/attendance/seed` on a published month rewrites them (S included) to the
  roster code. Owner to choose an explicit "seeded" flag or never syncing over
  S (#27).
- Shift-change requests now accept CD for T/M/F (the admin approves; the
  re-check warns "more comp days than owed"); T (training) and B (business
  trip) on a holiday also earn a CD, like any working code (#5).
- Self-arrange lets T/M/F move an X off a holiday and work it, which earns a CD
  (the admin approves).
- Every existing user starts at the 30-day placeholder quota after migration
  0008.
- The quota counts calendar days (AL is written on every day of the span,
  weekends and holidays included); the 30-day placeholder lives in config and
  in the migration default; the Leaves page shows only the current business
  year.
- A CD that was in the grid before a leave approval is overwritten by AL and
  becomes X on revoke (the comp day disappears from the grid); revoke never
  restores the pre-approval code (#28).
- The admin's comp-day total on the Leaves page leaves out disabled and pending
  users.

### Carried over from earlier reviews
- Partial-week off-target rounding (decision #7).
- Whether M/T appear in the A/D balance objective (currently role A only).
- Real "WR JUN26" Excel layout for the importer.
- Final `DATA_RETENTION_MONTHS` figure (shipped 36; legal floor 24).
