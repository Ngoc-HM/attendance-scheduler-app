# Monthly scheduling agreement — 2026-11-15

## Binding requirements

- A and D are ordinary shifts with different hours, not arrival/departure duties. Example hours supplied by the user are illustrative, not configuration.
- Flight-day demand remains a minimum: 0 pairs -> 0A/0D; 1 -> 1A/1D; 2 -> 1A/2D. Only role A covers this demand. Automatic scheduling never creates emergency A/D.
- Standard monthly working days = calendar days minus Saturdays and Sundays, including 20 days in some Februaries.
- No weekly quota: one week can have one day off and another three. A single day off may break the pattern. At most five consecutive working days, including month boundaries.
- Balance A versus D for EACH role-A person over the month. First reduce the worst individual absolute gap, then distribute imbalance across everyone, then improve aggregate balance. Greater D demand can prevent equality.
- Rotate Fri+Sat, Sat+Sun and Sun+Mon independently, in that preference order. Prefer fewer prior turns of that kind, then longest waiting. Consider turns already assigned earlier in the SAME month. An unavailable member keeps priority. Remember history across months. No 3:2:1 conversion between kinds; no top-three-only fairness.
- A valid roster must meet demand, consecutive-rest and monthly entitlement rules. If these conflict, return explicit violations rather than silently claiming success. Existing admin override/publish-with-warning policy remains.

## Implementation rulings

- Preserve existing approved-leave and CD entitlements. The standard work count is for an ordinary full month without leave; AL/CD reduce actual duties under existing rules. Do not make employees work back approved leave. Preserve current weekend-leave adjustment and holiday compensation policy.
- Common work/rest rules apply to existing scheduler roles; A/D balance only role A. Turn fairness compares within a role group.
- Effective history uses actual attendance when available, otherwise planned cells; derive state rather than increment mutable counters. Use existing 12-month history horizon, separate counts and last date for each kind. Only X+X earns a turn; AL/CD/S excluded. A Fri–Sun X run earns one turn of each contained kind. Boundary pairs count once in the month containing their second day.
- Equal counts/last dates may use stable user ID as final tie-break; never override a lower-count or longer-waiting person merely by ID. Feasibility constraints may prevent a turn; avoid hard greedy assignments which make otherwise valid rosters impossible.
- Monthly quota and max-five remain diagnostic-capable: prioritize zero violations, and explain nonzero violations. Monthly quota must be mirrored in recheck, unlike today's silent soft preference.
- Remove weekly-rest-derived lookahead; keep cross-month consecutive-work protection. Do not invent next-month flight demand when unknown.
- Use ordered objective stages with shared solver time budget and report proof/time-limit status honestly. Lower stages may not worsen achieved higher-stage values. Preserve best incumbent if later stage times out.
- Keep existing API compatibility; additive diagnostic fields allowed. Changes to existing rosters happen only through existing explicit generate/edit flows.

## Acceptance

Monthly 28/29/30/31-day tests; one-rest/three-rest weeks; six consecutive work days detected; boundary 5+1 detected; monthly work/leave/CD accounting; balanced gaps preferred to concentrated gaps; chronological rotation and per-kind independence; six-person fairness; history actual-over-plan and rerun idempotence; infeasible staffing warnings; timeout fallback; same violations after generation and edit; multi-month regression.

## Owner correction: ordinary rest spacing

Ordinary rest must never silently pass a four-day run: maximum three consecutive
non-working ordinary-rest days, including X/CD and month boundaries. Approved AL
remains exempt. Prefer two-day rest and use triples only when operational rules
and monthly entitlements require them. After minimizing rule violations, minimize
ordinary three-day windows before shift balance and preferred weekday turns, so
extra weekend awards cannot purchase an unnecessary longer break. Existing
diagnostic architecture still reports infeasible entitlements/coverage explicitly.
