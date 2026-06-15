# Phase 08 — F-15 Reports (Monthly / Yearly Export)

## Context Links
- Spec: §4.7 / F-15, §7 (codes), §2 (export by month/year). F-15 layout DEFERRED — build flexible/extensible exporter.
- Files: `backend/app/services/report_service.py`, `backend/app/api/v1/endpoints/reports.py`.

## Overview
- Priority: P2. Depends on 06 (actuals) + 07 (carry totals).
- Export attendance by month and by year in a flexible, format-pluggable way (CSV first, Excel optional).

## Key Insights
- Layout undecided (locked: defer). Design = a neutral tabular data model + pluggable serializers (CSV/Excel), so a new layout is a new serializer, not a rewrite (extensibility = the actual F-15 requirement).
- Data source = AttendanceRecord (actuals); summary columns = working days (sum of workday_value), off days, A/D count, comp carry, premium-off.
- §9.1: reports for non-admin must EXCLUDE S detail (or show generic "off"); admin reports may include S. RBAC in phase 10.

## Requirements
Functional:
- `monthly_report(year, month)` → tabular rows: per user × day grid + per-user totals (working days, A/D, X, CD, premium-off).
- `yearly_report(year)` → per user × month totals.
- Serializer interface: `to_csv(report)`, optional `to_xlsx(report)`.
- Endpoints stream the file with correct content-type/filename.

Non-functional: adding a format = implementing one serializer; no change to data assembly.

## Architecture
Data flow: actual_records_map + carry summary → `ReportTable` (neutral dataclass: headers, rows, totals) → serializer → bytes → HTTP StreamingResponse. Monthly vs yearly differ only in aggregation step.

## Related Code Files
Modify:
- `backend/app/services/report_service.py` — assemble monthly/yearly ReportTable.
- `backend/app/api/v1/endpoints/reports.py` — wire (GET monthly, GET yearly; ?format=csv|xlsx; RBAC-filtered).

Create:
- `backend/app/services/report_table.py` — neutral `ReportTable` dataclass + aggregation helpers (<200 LOC).
- `backend/app/services/report_serializers.py` — `to_csv` (+ `to_xlsx` via openpyxl) (<200 LOC).

Delete: none.

## Implementation Steps
1. `report_table.py`: `ReportTable` (title, headers, rows, totals); `build_monthly(records, users, days, carry)`; `build_yearly(records_by_month, users)`.
2. `report_serializers.py`: `to_csv(table) -> bytes`; `to_xlsx(table) -> bytes` (openpyxl).
3. `report_service.monthly_report` / `yearly_report` → ReportTable.
4. Endpoints: pick serializer by `format`, StreamingResponse with filename `attendance_{year}_{month}.csv`.
5. RBAC: non-admin → only own row; S masked for non-admin (phase 10).

## Todo List
- [ ] ReportTable + monthly/yearly aggregation
- [ ] CSV serializer
- [ ] XLSX serializer (optional, openpyxl)
- [ ] monthly_report / yearly_report
- [ ] endpoints with ?format + StreamingResponse
- [ ] RBAC filter + S masking for non-admin

## Success Criteria
- Monthly CSV downloads with one row per user, per-day codes, correct working-day totals (A/D counts as 2).
- Yearly report aggregates 12 months per user.
- Switching `?format=xlsx` returns a valid workbook with identical data.
- Non-admin export contains only own data with S masked.

## Risk Assessment
- Layout churn when customer decides format (Med/Low) → serializer pattern absorbs it.
- Large yearly export performance (Low/Med) → stream; query per month.

## Security Considerations
- Non-admin: own data only; S masked. Admin: full. Audit export action.

## Next Steps
Unblocks phase 09 (reports_page wiring: trigger + download).
