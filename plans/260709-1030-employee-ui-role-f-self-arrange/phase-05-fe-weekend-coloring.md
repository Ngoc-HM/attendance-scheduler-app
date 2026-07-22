# Phase 05 — FE weekend row coloring in DsScheduleView

## Context Links
- Plan: [plan.md](plan.md) — independent (Wave 1, parallel with P01/P03)
- Widget: `attendance_scheduler_app/lib/design_system/business_views.dart` (`DsScheduleView`, `_DsRosterTable._dayRow` ~L459)
- Tokens: `lib/design_system/tokens.dart` (`DsColors.surfaceSubtle` = 0xFFF3F6FB)

## Overview
Priority P3. Status pending. Sat + Sun get a distinct background. NOTE: roster is
**transposed** (days = rows, people = columns) — so weekend = **row** tint, not
column. One change covers BOTH admin and employee (shared widget → DRY).

## Key Insights
- Weekend detection already exists in `_dayRow` (`weekend` bool used for text color) — extend to a row background.
- `_dayRow` currently returns a `Padding`; wrap in a `Container(color: weekend ? DsColors.weekendTint : null)` (or `ColoredBox`).
- Header/summary rows use `surfaceSubtle`; pick a clearly different weekend tint (e.g., light blue/amber) so it's not confused with header shading.

## Requirements
- Sat/Sun day-rows visually distinct in the roster table.
- Applies to admin and employee schedule views (same widget).
- Token-based color (no hard-coded hex in widget) per token-discipline convention.

## Architecture
Data in: `date.weekday`. Transform: `weekend` → background token. Data out: tinted row. Pure presentational; no data/model impact.

## Related Code Files
**Modify:**
- `lib/design_system/tokens.dart` — add `static const weekendTint = Color(0x...)` (subtle, distinct from surfaceSubtle).
- `lib/design_system/business_views.dart` — `_dayRow`: wrap row content with weekend background; keep existing weekend text colors.

## Implementation Steps
1. Add `DsColors.weekendTint` (e.g. `Color(0xFFFFF4E5)` warm, or `Color(0xFFEAF2FB)` cool — pick per design_guidelines).
2. In `_dayRow`, change outer `Padding` → `Container(color: weekend ? DsColors.weekendTint : null, child: Padding(...))` preserving current padding/margins.
3. Verify column widths/dividers still align (Container spans full row width).
4. `flutter analyze`; visual smoke via running app or `/ck:preview` if desired.

## Todo List
- [ ] weekendTint token
- [ ] _dayRow background wrap
- [ ] alignment check
- [ ] analyze

## Success Criteria
- Sat & Sun rows render with the tint in both admin and employee schedule tables.
- No layout shift; dividers/columns still aligned.

## Risk Assessment
| Risk | L×I | Mitigation |
|------|-----|-----------|
| Tint clashes w/ shift badge colors (readability) | Med×Low | Choose low-saturation tint; verify against `DsShiftBadge` palette. |
| Holidays also want highlight (owner: holiday=workday) | Low×Low | Scope to Sat/Sun only per requirement; holidays untouched. |
| Owner literally meant "columns" | Low×Med | Transposed layout → rows ARE the days; note in PR. Flag. |

## Security Considerations
- None (presentational).

## Next Steps
Independent; can merge anytime. No downstream blockers.

## Unresolved
- Exact tint hex (design choice). Confirm "columns" vs transposed rows with owner.
