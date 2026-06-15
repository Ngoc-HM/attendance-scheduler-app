# Phase 02 — F-04 Flights (CRUD + Excel Import)

## Context Links
- Spec: §4.2 / F-04, §8 (FLT numbers, STA/STD LT FRA).
- Files: `backend/app/services/flight_service.py`, `backend/app/api/v1/endpoints/flights.py`, `backend/app/schemas/flight.py`, `backend/app/models/flight.py`.

## Overview
- Priority: P1 (produces `flight_pairs[d]`, a scheduler input).
- Status: pending. Depends on 01.
- Implement manual flight-day CRUD + Excel import → derive `flight_pairs` per day.

## Key Insights
- `FlightDay.flight_pairs` (0/1/2) is the only value the solver reads (`fixed_group_staffing`). `Flight` rows are display/detail.
- `flight_pairs` can be set directly (manual) OR derived from imported `Flight` rows (count distinct pairs/day; cap at 2).
- §8: 37/36 = HAN-FRA pair; 31/30 = SGN-FRA pair. A "pair" = one arrival+departure of a route.
- No sample "WR JUN26" Excel in repo → column mapping is an OPEN QUESTION; build importer against a documented expected layout, fail gracefully on mismatch.

## Requirements
Functional:
- List flight days for a month; upsert a day's `flight_pairs` (manual).
- Upsert individual `Flight` rows (flt_number, route, sta, std).
- Import Excel: parse rows → upsert `Flight` + recompute `FlightDay.flight_pairs`.
- `flight_pairs_map(days)` → `{date: int}` defaulting 0 for the scheduler.

Non-functional: importer validates types; partial-failure returns row-level errors, no partial commit on hard parse error.

## Architecture
Data flow: Excel/manual → `Flight` rows → derive pairs → `FlightDay.flight_pairs` → `flight_pairs_map` → `SolverInput.flight_pairs`. Pair derivation: group flights by day, match arrival (37/31) with departure (36/30) of same route; `pairs = min(2, matched_pairs)`.

## Related Code Files
Modify:
- `backend/app/services/flight_service.py` — implement all 5 functions (split derivation helper into `flight_pair_derivation.py` if >200 LOC).
- `backend/app/api/v1/endpoints/flights.py` — wire endpoints (GET days, PUT day, PUT flight, POST import, admin-guarded).
- `backend/app/schemas/flight.py` — confirm/extend `FlightDayUpsert`, `FlightUpsert`, import response schema.

Create:
- `backend/app/services/flight_pair_derivation.py` — pure pair-counting logic (testable, <200 LOC) IF derivation grows.
- `backend/requirements` entry: `openpyxl` (verify present).

Delete: none.

## Implementation Steps
1. Confirm `openpyxl` in deps (add if missing).
2. Implement `list_days`, `upsert_day`, `upsert_flight` (simple ORM upserts).
3. Implement `flight_pairs_map(db, days)` → dict default 0.
4. Implement pair-derivation: group `Flight` by day, count route pairs (37↔36, 31↔30), `flight_pairs = min(2, count)`; update `FlightDay`.
5. Implement `import_excel`: read workbook, map columns (day, flt_number, route, sta, std), validate, upsert rows, then recompute pairs for touched days.
6. Wire endpoints with admin role guard; import accepts `UploadFile`.
7. Document expected Excel columns in importer docstring + README.

## Todo List
- [ ] Verify openpyxl dependency
- [ ] Implement list_days / upsert_day / upsert_flight
- [ ] Implement flight_pairs_map
- [ ] Implement pair derivation (37/36, 31/30 → 0/1/2)
- [ ] Implement Excel import with validation
- [ ] Wire + guard endpoints
- [ ] Document expected Excel layout

## Success Criteria
- Manual upsert of a day sets `flight_pairs` and is read back.
- Import of a valid workbook creates Flight rows and sets correct `flight_pairs` (2 routes/day → 2; 1 route → 1; none → 0).
- `flight_pairs_map` returns 0 for unconfigured days.
- Bad workbook → 4xx with row errors, no partial commit.

## Risk Assessment
- Unknown Excel layout (High/High) → OPEN QUESTION; code to a documented layout, request sample. Mitigation: manual entry path always works without Excel.
- Pair double-counting (Med/Med) → unit-test derivation with mixed routes.

## Security Considerations
- Import endpoint admin-only (RBAC, phase 10). Validate file size/type to avoid resource abuse.

## Next Steps
Unblocks phase 05 (schedule generate reads flight_pairs) and phase 09 (flights_page wiring).
