# WR roster export (customer workbook layout) and shift time frames

Date: 2026-11-18. Status: analysis and brief, nothing implemented.
Source analysed: the owner's file `WR NOV26 (3).xlsx` (an Excel-authored workbook, 2 sheets, no formulas, no images, no conditional formatting, no data validation, no defined names, no frozen panes).

Goal 1: the monthly report download produces a `.xlsx` with the same structure as that workbook. People's names become person codes (A1, F2, M1 ...). Daily codes come from the app.
Goal 2: the admin sets the working-time frame of each shift (about A 05:30-13:05, D 06:20-13:55; A+D works 05:30-13:55 and earns a comp day the following month).

---

## 1. Workbook structure

### 1.1 Workbook level

| Item | Value |
|---|---|
| Sheets | `NOV26` (the roster), `AL 26` (annual-leave overview, German) |
| Sheet name rule | roster sheet = month abbreviation upper-case + 2-digit year (`NOV26`); leave sheet = `AL 26` (`AL` + 2-digit year) |
| Defined names | none |
| Theme | Office-style theme: dk1 000000, lt1 FFFFFF, dk2 000000, lt2 FFFFFF, accent1 5B9BD5, accent2 ED7D31, accent4 FFC000, accent6 70AD47 |
| Doc properties | creator and lastModifiedBy are people; do not copy |

Theme colours resolve to these hex values (Excel "lighter" tints), use them as plain RGB when writing:

| Theme reference | Hex |
|---|---|
| theme9 (accent6) tint 0.6 | C6E0B4 (light green) |
| theme7 (accent4) tint 0.6 | FFE699 (light amber) |
| theme5 (accent2) tint 0.6 | F8CBAD (light salmon) |
| theme4 (accent1) tint 0.4 | 9DC3E6 (light blue) |
| theme3 (dk2) | 000000 (black, spacer rows) |
| theme0 (lt1) | FFFFFF (explicit white fill) |
| literal | FFFF00 yellow, FF99CC pink, CC99FF lavender (FFCC99FF), FF0000 red font |

### 1.2 Sheet `NOV26`

Used range `A1:Q79` (columns O..Q only hold stray content, see 1.2.9).

**Page / view**
- Paper size 9 (A4), portrait, `scale=68`, `fitToPage=1`, `fitToWidth=0` (automatic), `fitToHeight` not set (default 1, so everything fits on one page tall).
- Margins (inches): left 0.25, right 0, top 0.5, bottom 0.5, header 0.05, footer 0. No header or footer text, no print area, no print titles, no centring.
- View: zoom 80, no frozen panes, gridlines on (default).
- Default column width 9.140625, default row height 15.

**Column widths** (characters)

| Columns | Width |
|---|---|
| A, B | 7.7109375 |
| C | 8.7109375 |
| D | 10.7109375 |
| E | 23.7109375 |
| F..N (9 person columns) | 8.7109375 each |
| O.. | default 9.140625 |

**Row heights** (points; none hidden; no hidden columns)

| Rows | Height |
|---|---|
| 1 | 18.75 |
| 2 | 31.5 |
| 3..54 (day block) | 15.75 each |
| 55 (black spacer) | 5.1 |
| 56..70 (legend/totals) | 15.75 each |
| 71, 73 | default (15) |
| 72 (signature line) | 18.75 |
| 74 | 15.75 |
| 75 (tiny spacer, empty) | 5.1 |
| 76..79 | default (15) |

**Fonts**: everything the author formatted is Times New Roman; unformatted merged-away cells and the notes block at the bottom are Calibri 11 (those carry no content in the roster body; keep Calibri on A74:A79 and P17).

#### 1.2.1 Title block
- `A1:M1` merged. Text: `WR NOV26 // (TTL 21 WORKING DAYS)`. Pattern: `WR <MON><YY> // (TTL <n> WORKING DAYS)`. Times New Roman 14 bold, black, centred horizontally and vertically, white fill (FFFFFF), number format `@`, no border.
- n = number of working days in the month for the station, here 21 = 30 calendar days - 9 X days (see legend row 65 and total row 66).

#### 1.2.2 Header row 2
All cells Times New Roman 12 bold, black, white fill, centred both ways, number format `@` (N2 is `General`), thin borders on all four sides. Heights 31.5.

| Cell | Text |
|---|---|
| A2 | `Date` |
| B2 | `Day` |
| C2 | `FLT #` |
| D2 | `STA/STD LT FRA` (wrap text on) |
| E2 | `NOTES` |
| F2..N2 | one cell per person: name 1 .. name 9 (names to be replaced by person codes) |

Left/right border exceptions on the person header cells (same exceptions apply down the whole column block, see 1.2.4): thick LEFT border on H2 and J2; thick RIGHT border on M2; thick LEFT and RIGHT on N2.

#### 1.2.3 Day block (rows 3..54): row structure
- One calendar day occupies **one or two rows**, one row per flight pair that flies that day:
  - first row: pair `31/30` with times `0650/1305` (the SGN pair),
  - second row: pair `37/36` with times `0600/1355` (the HAN pair).
- A day with both pairs uses two rows (31/30 first, then 37/36). A day with only 37/36 uses one row. In Nov 2026: 31/30 flies Sun, Mon, Wed, Thu, Sat (22 days); 37/36 flies every day (30 days). Total rows 3..54 = 52 = 22 two-row days + 8 one-row days (Tue/Fri). No day in this month has zero flights or only 31/30.
- Time exception: day 28 (Sat) shows `0630/1345` for 31/30 (a schedule change for that day); the 37/36 row stays `0600/1355`.
- Cell layout per row:

| Col | Content | Merge | Notes |
|---|---|---|---|
| A | day number as TEXT (`'1'`, `'2'` ...) | merged over the 2 rows of a two-row day (e.g. `A3:A4`); single cell on a one-row day | `@` format, TNR 12, centred |
| B | weekday, 3 letters upper-case: `SUN MON TUE WED THU FRI SAT` as text | same merge as A | same style |
| C | `FLT #`: `31/30` or `37/36` (text) | never merged | one per row |
| D | `STA/STD LT FRA`: `<STA arrival leg>/<STD departure leg>` as 4-digit times without colon, e.g. `0650/1305` | never merged | one per row |
| E | NOTES, empty all month | merged per day like A/B | wrap on |
| F..N | the person's daily code (text) | each person cell merged over the 2 rows on two-row days (`F3:F4` etc.), single on one-row days | centred, TNR 12 |

- Total number of merged ranges in the sheet is 275 (see 1.2.8).
- The second row of a two-row day has empty A/B/E/F..N cells (they belong to the merge). Their un-merged style cells are Calibri 11 with borders thin left/right/bottom and NO top border; they are covered by the merge so only the top-left cell matters when rebuilding.

#### 1.2.4 Borders of the person block
- All cells of A2:N54: thin on all sides.
- Group separators (thick): a thick LEFT border on column H and column J, a thick RIGHT border on column M and on column N (N also thick LEFT in rows 2, 55..64, 66..70 in the original; rows 3..54 have thin left, thick right on N). Meaning: person groups are `{F,G} {H,I} {J,K,L,M} {N}` = 2 + 2 + 4 + 1 people. In app terms this is almost certainly per role group; the 4-person group {J..M} matches role A (A1..A4), see section 2.
- Day-block cells are not otherwise thick.

#### 1.2.5 Weekend / holiday marking and code styling (day columns)
- Weekends: on Saturday and Sunday the merged date/weekday cells (A and B only, top-left cell of the merge) get a light green solid fill C6E0B4. In Nov 2026: days 1, 7, 8, 14, 15, 21, 22, 28, 29 (A and B of those days).
- Holidays: no holiday marking exists in this month (no public holiday in the file). Nothing observed for how a holiday would look.
- Daily codes that appear in F3:N54 (counts over the file): `D` 96, `X` 90, `A/D` 39, `A` 22, `AL` 14, `T` 4, `CD` 3, plus typos `'A '` (A, trailing space) and `'A /D'` (inner space). The app must write clean codes: `A`, `D`, `A/D`, `X`, `CD`, `AL`, `T`, `O/D`, `B`, `S`.
- Styling of the codes in the file is hand-applied and inconsistent (the author painted by hand, mostly in Joachim's column K, i.e. one A-group person with leave):
  - `AL`: yellow FFFF00 fill (14 cells, column K only).
  - `X` on weekend days in column K: FFE699 fill (K13, K15, K17, K25, K27, K37, K39, K49, K51).
  - `CD`: F8CBAD fill (K12, L34, L36).
  - `D` or `A` cells K5 and M5 (day 2): lavender CC99FF fill (manual marker).
  - Everything else has no fill (white background from the sheet).
  - Bold font on some cells (F/G/I/J columns), red font FF0000 on a few cells (G12 `X`, I37 `X`, I39 `X`, J19, J27, J43, J44 `A`, and the day-9 row text in A17:D18). These are hand highlights for manual changes, not rule-based.
- The legend (1.2.6) shows the intended colour per code: A/D pink FF99CC, CD F8CBAD, O/D 9DC3E6, AL FFFF00. Recommended app behaviour: paint by code using the legend colours (plus C6E0B4 for weekend A/B, FFE699 for X on a weekend/holiday if the owner wants it), no manual red/bold.

#### 1.2.6 Spacer, legend and totals (rows 55..70)

Row 55: `A55:N55` solid black (theme dk2 = 000000), height 5.1, thin top, no bottom border, number format `@`.

Legend block `A56:D66`: each of rows 56,57,59..66 has `A:D` merged (`A56:D56`, `A57:D57`, `A59:D59` .. `A66:D66`); row 58 is NOT merged (A58, B58, C58, D58 each pink-filled with the same style). All legend text is Times New Roman bold, left aligned, number format `@`, thin borders.

| Cell | Text | Font | Fill |
|---|---|---|---|
| A56 | `A= ARR duty // till STD - 60 Minutes` | 10 bold black, wrap on, left/top | FFFFFF |
| A57 | `D = DEP duty  // Briefing Time - 40MIN` (two spaces before `//`) | 10 bold, **red FF0000**, left/centre | FFFFFF |
| A58:D58 | `A/D = ARR and DEP duty // 2 working days` (text in A58 only) | 10 bold black | FF99CC |
| A59 | `CD = compensation days ` (trailing space) | 10 bold | F8CBAD |
| A60 | `O/D = office duty` | 10 bold | 9DC3E6 |
| A61 | `T = online/trainings course` | 10 bold | FFFFFF |
| A62 | `S = reported SICK` | 10 bold | FFFFFF |
| A63 | `B = Business Trip` | 10 bold | FFFFFF |
| A64 | `AL = on leave` | 10 bold | FFFF00 |
| A65 | `X = OFF DAY (INCL PH): 09 DAYS` (the `09` is the month's X count; TNR 9 bold, bottom border none) | 9 bold | FFFFFF |
| A66 | `TTL DAYS` (centre/centre, 12 bold, merged `A66:D66`) | 12 bold | FFFFFF |

Per-person count columns in the same rows. They exist ONLY for the five last people (J..N: the A-group plus the 9th person); F..I are empty (styled but blank) in rows 56..70.

| Row | Meaning (row label in column A) | Cells | Number format | Font |
|---|---|---|---|---|
| 56 | count of `A` | J56..N56 | `0` (N56 General) | TNR 12 bold |
| 57 | count of `D` | J57..N57 | `0` | TNR 12 bold |
| 58 | count of `A/D` | J58..N58 (N58 is text `'0'`) | `0` | TNR 12 bold |
| 59 | count of `CD` | J59..M59 salmon F8CBAD fill, N59 no fill | `0` | TNR 12 bold |
| 60 | count of `O/D` | J60..N60 | `0` | TNR 12 bold |
| 61 | count of `T` | J61..N61 | `0` | TNR 12 bold |
| 62 | count of `S` | J62..N62 EMPTY in the file | `0` | TNR 12 bold |
| 63 | count of `B` | J63..N63 | `0` | TNR 12 bold |
| 64 | count of `AL` | J64..M64 yellow FFFF00, N64 no fill | `0` | TNR 12 bold (L64 is 9 pt) |
| 65 | (X row) nothing | empty cells | `0` | |
| 66 | `TTL DAYS` = working days of the month | J66..N66 = 21 | `0` | TNR 12 bold |

Rows 67..70 are a second table "compensation days". Label in A (TNR 12 bold, left, `@`), B and C empty bordered cells, D left bold; label text overflows across B..D (no merge). Values J..N (text `'0'` style `@` in rows 67, 68, 70; numeric in row 69), TNR 12 bold:

| Row | Label (A) | Meaning |
|---|---|---|
| 67 | `compensation days present month` | comp days earned in this month (all 0 in the file: A/D earned in the month are listed on the NEXT month's sheet, see below) |
| 68 | `compensation days previous month ` (trailing space) | comp balance carried in from the previous month |
| 69 | `compensation days (CD) used this month` | number of CD codes in the month |
| 70 | `compensation days (CD) in TTL` | balance after the month = previous + present - used |

**Formulas: there are none.** All counts and totals are typed constants (J56:N70). The file is internally inconsistent in places (for example the person in J has `D`=14 and `A/D`=2 in the grid but 13 and 3 in the totals; K has `AL`=14 in the grid, 13 in the totals; K70 shows 0 where 1+0-0 = 1). So the app must compute the counts from its own data, not copy them from a formula. Cached values equal the constants (the file was saved with `data_only` identical to normal load).

#### 1.2.7 Signature line and notes block

| Cell | Text | Font |
|---|---|---|
| A72 | `Checked by Mr Toan on:` (contains the name of the first person column; a person name in fixed text) | TNR 14 bold, left/centre, white fill, row 72 height 18.75 |
| J72 | `Approved by GM on:` | TNR 14 bold black |
| A74 | `Compensation Days from October 26 as follows:` (previous month name + year) | Calibri 12 bold |
| A76..A79 | one line per person who has outstanding comp days: `<name>: <n> - <date list with reason>`, e.g. `Name: 2 - 03OCT A/D instead of A // 04OCT D instead of off-duty`. Reasons seen: `A/D instead of A`, `D instead of off-duty`, `A/D duty assigned`, `T instead of off-duty` | Calibri 11, no wrap, overflow to the right |

The four lines mirror row 68 (previous-month comp balances) for the people J..M. Each line starts with the person's NAME (replace by code).

#### 1.2.8 Merged ranges (275 total)
- `A1:M1`.
- For every two-row day with first row r: `A{r}:A{r+1}`, `B{r}:B{r+1}`, `E{r}:E{r+1}`, and `F..N{r}:F..N{r+1}` (9 person columns). 22 two-row days x 12 ranges = 264.
- Legend: `A56:D56`, `A57:D57`, `A59:D59`, `A60:D60`, `A61:D61`, `A62:D62`, `A63:D63`, `A64:D64`, `A65:D65`, `A66:D66` (10 ranges; row 58 is not merged).
- Total = 1 + 264 + 10 = 275. One-row days have no merges.
- C and D are never merged (one value per flight pair).

#### 1.2.9 Stray content (not part of the structure)
- `P17` = `CAAV and SQD audit` (Calibri 11): a free note beside day 9, in column P, outside the table and print width. Not exported (no data); optional.
- `Q11`, `Q23`, `Q35`, `Q47` = a single space `' '` (Thursday rows). Not exported.
- No images, charts, comments or hyperlinks.

#### 1.2.10 What changes per month vs what is fixed

| Changes monthly | Fixed |
|---|---|
| Sheet name, title month/year, `TTL n WORKING DAYS` | Column set A..N, widths, header texts (except person cells) |
| Number of day blocks (28..31) and their rows (row count = 1 or 2 per day, so last row is not constant) | Row 2 headers, legend text, signature texts, spacer rows (positions shift with the day block, see below) |
| Weekday text, weekend green fill, flight rows per day, STA/STD, day-28 style exceptions | Fonts, borders, group separators |
| Daily codes, per-person counts, comp-day rows | Legend colours |
| `X = OFF DAY ... : nn DAYS` number, previous-month name in A74, notes A76+ | |

Because rows 3..54 is a function of the flights, **everything below the day block moves**: the spacer is `last_day_row + 1`, legend rows start at +2, etc. For Nov 2026 the offsets are 55/56..66/67..70/72/74/76... The relative offsets (spacer, 11 legend rows, 4 comp rows, blank, signature, blank, notes heading, blank, notes) are fixed.

### 1.3 Sheet `AL 26` (annual leave overview)

Used range `B4:G20`. No merges, no frozen panes, default page setup (no orientation, margins 0.7/0.7/0.787/0.787/0.3/0.3), no print area. Column widths: B 25.7109, C..F 25.7109, G 24.2890625; default 11.4257. Rows: 4 = 21, 6 = 15.75, 19 = 15.75.

| Cell | Content |
|---|---|
| C4 | `Urlaubstageübersicht 2026` (Calibri 16 bold, centred) |
| C6:G6 | five person names (name 1..5 = the A group and the fifth person), Calibri 12 bold, centred, thin top/left/right |
| B7 | `Monat / U Tage` (centred, thin box) |
| C7:G7 | the annual quota, here `25` for every person, bold |
| B8:B19 | month names in German: `Januar Februar März April Mai Juni Juli August September Oktober November Dezember` (centred, thin box) |
| C8:G19 | days of leave taken in that month, per person (numbers, blank if none; one cell holds text `11 +2 von 25`) |
| B20:G20 | `Rest` row: bold, medium top border, values 21, 5, 9, 23, 14 (typed constants, remaining days) |

All cells Calibri 11 unless stated, thin borders on all sides, centred horizontally and vertically, no fills. No formulas. The names in C6:G6 are replaced by codes.

---

## 2. Mapping workbook -> app data, with gaps

| Workbook part | App data | Status |
|---|---|---|
| Person header F2..N2 (name -> code) | `User.code` (`models/user.py`: `String(8)`, unique, e.g. `A1`, `T2`, `F1`, `M1`) via `UserRow` (`report_service._user_rows`, currently carries `full_name` and `role`) | Available. Needs `code` added to `UserRow`/writer input. |
| Order of the person columns | Role + code. Workbook order is {2}{2}{4}{1} with thick separators, and the 4-person group matches `Role.A` (fixed group A1..A4). Which role each of the other groups is cannot be known from the file | Partly known. Proposed: sort by role in a fixed list, then code; ask owner to confirm (Q1). |
| Group separators (thick borders) | role change between neighbouring columns | Derivable. |
| Title `WR NOV26 // (TTL 21 WORKING DAYS)` | `calendar` month name + year; working days = days in month - X days per person | Derivable only if "X days" is the same for everybody; 9 here. See Q3. |
| Day number, weekday, weekend green | `calendar_utils.month_days` | Available. |
| Holiday marking | `holiday_service.holiday_dates` / `Holiday` | Data available, but the workbook shows no holiday style, so nothing to copy (Q6). |
| FLT # and STA/STD per day (one row per pair) | `Flight` rows (`models/flight.py`: `day`, `flt_number`, `sta`, `std`, `route`) via `flight_service.list_flights_for_days`; `FlightDay.flight_pairs` | Available. A pair `31/30` = legs 31 and 30: show `31/30` and `STA(31)` + `/` + `STD(30)` as `HHMM/HHMM`. Pair order: 31 before 37 (by `flt_number` ascending is the reverse, so order explicitly: 31/30 first). Needs a rule for how to join two `Flight` rows into one pair (arr number = odd, dep = arr-1), and for a day with 0 pairs (Q4). |
| Daily codes in F..N | `attendance_service.actual_records_map(db, year, month)` -> `{(user_id, day): AttendanceCode}` (already used by `report_service.monthly`) | Available. Planned roster `ShiftAssignment` (`models/schedule.py`) only if no actual exists (Q5 default: actual, falling back to published plan). |
| Code meanings / legend | `AttendanceCode` (A, D, A/D, AD, X, CD, O/D, T, B, S, AL) | Available. The app has two codes the workbook does not: `AD` (two shifts, no comp day) is NOT in the legend; export it as `A/D` or `AD`? (Q7). The workbook has all other codes. |
| Counts A/D/A-D/CD/O-D/T/S/B/AL per person (rows 56..64) | computable from the same grid | Available. Only for some people in the file (Q2). |
| `TTL DAYS` row 66 | working days of the month | Derivable (days - X days). |
| Comp rows 67..70 | `User.carry_comp` is the balance carried from the last closed month (`calculation_service`, `carry_over_math.comp_balance`); earned = each A/D (+1 for any working code on a holiday from `HOLIDAY_COMP_EFFECTIVE_FROM`), used = each CD | Available for TTL/used; "previous" requires the carry as at the START of the month (the stored `carry_comp` is the value after the last close, i.e. possibly already updated for this month, so recompute with `comp_balance` over records up to the month start). Workbook shows "present month" = 0 because earned comp is posted the next month; app earns it at month close. |
| Notes A74..A79 ("Compensation Days from October 26 as follows", per person dates and reasons) | no stored reason. Dates of previous-month A/D are derivable; the reason text (`A/D instead of A`, `D instead of off-duty`, `A/D duty assigned`) is derivable only by comparing planned (`ShiftAssignment.code`) with actual (`AttendanceRecord.code`) | **Gap (partial).** Default: list `<code>: <n> - <DDMON> A/D` for each A/D date, with "instead of <planned code>" when the plan differs. Free-text reasons beyond that: no data. |
| `NOTES` column E | `AttendanceRecord.note` is per person-day; there is no per-DAY note | **Gap.** Default: leave E empty. |
| `P17` note `CAAV and SQD audit` | none | **Gap**, not exported. |
| Signature `Checked by Mr Toan on:` / `Approved by GM on:` | none (fixed text; one person name inside) | **Gap**, export labels only, no date (Q8). |
| Sheet `AL 26` months x people | `leave_balance.summaries(db, users, year)` gives quota/used/pending/available per person; per-month leave days derive from `LeaveRequest` (approved) or from `AL` codes in `AttendanceRecord` | Data available; there is no existing per-month-per-person aggregation (small new function). Quota in the file is 25, app default `ANNUAL_LEAVE_DEFAULT_DAYS` is 30 and is per person (`annual_leave_quota`). `11 +2 von 25` style comments: no data. |
| Hand colours (red/bold, lavender) | none | **Gap by design** (manual author marks); not reproduced. |

---

## 3. Proposed implementation (export)

### 3.1 How the app exports today

- `backend/app/api/v1/endpoints/reports.py`: three admin-only GET routes `/reports/monthly/{year}/{month}`, `/reports/yearly/{year}`, `/reports/leave-balance/{year}`, each with `?format=csv|xlsx` (anything else falls back to csv). A `_stream` helper picks the media type and `Content-Disposition` filename (`attendance_{year}_{month:02d}.xlsx`) from `report_serializers.CONTENT_TYPES` and wraps the bytes in a `StreamingResponse`; each call writes an audit row (`report.export`).
- `services/report_service.py`: `monthly()` reads `attendance_service.actual_records_map`, lists active (and disabled-with-actuals, never pending) users ordered by id into `UserRow(user_id, name=full_name, role)`, and calls `build_monthly`. `yearly()` and `leave_balance_report()` do the same for their views (leave includes `Code, User, Role, Quota, Approved, Pending, Left, Comp days`).
- `services/report_table.py`: format-neutral `ReportTable(title, headers, rows)` of strings. `build_monthly` makes `User | Role | 1..N | Work days | A/D | Off (X)` (one row per person, days across, A/D = 2 workdays); `build_yearly` makes person x month totals.
- `services/report_serializers.py`: `to_csv` (UTF-8 BOM) and `to_xlsx` (openpyxl `Workbook`, header row + rows, no styling); `escape_cell` neutralises formula-looking cells (ruling R7, CSV injection). `serialize(table, fmt)` dispatches on the format key. Names are currently written (full names), codes are not in the monthly table.
- Flutter: `features/reports/**` = `ReportsRemoteDataSource` (Dio GET with `ResponseType.bytes`, filename from `Content-Disposition`), `ReportsController` (Riverpod; runs the fetch and writes the bytes with `saveToDownloads` from `core/utils/file_download.dart`, surfacing the path in a snackbar) and `ReportsPage` (month/year pickers, `CSV`/`XLSX` dropdown, Export button; `selectedFormat` is `'csv' | 'xlsx'`).

### 3.2 Proposal: smallest change that gives a structurally identical sheet

The generic path (`ReportTable` of strings -> `to_xlsx`) cannot express merged cells, fills, borders, widths, print setup or 1-2-row days. The workbook is a presentation layout, so it needs its own writer. Recommended shape:

1. **New serializer module** `backend/app/services/roster_xlsx.py` (next to `report_serializers.py`) exposing `build_roster_workbook(data: RosterSheet) -> bytes`, written with openpyxl (already a dependency; `to_xlsx` uses it). `RosterSheet` is a plain dataclass built by a new `report_service.wr_roster(db, year, month)`; keep it separate from `ReportTable` so CSV and the existing xlsx stay untouched.
   - Inputs of `RosterSheet`: `year, month`, `people: list[Person(code, role)]` already in column order, `days: list[Day(date, weekend: bool, holiday: bool, pairs: list[Pair(flt_label, sta_std)])]`, `grid: {(user_id, date): AttendanceCode}`, `previous_comp: {user_id: int}`, `comp_notes: {user_id: list[str]}`, `leave_months: {user_id: {month: int}}` and quotas for sheet 2.
2. **Wire it in** `reports.py`: a new route `GET /reports/roster/{year}/{month}` (admin only, xlsx only, filename `WR_NOV26.xlsx` = `WR_<MON><YY>.xlsx`, audit `report.export` with `detail="roster ..."`) rather than changing `format` semantics of `/monthly`. Optionally make `format=wr` on `/monthly` an alias. Keep `_stream` and its content-type table; add a `"wr"` entry only if aliasing.
3. **Flutter**: in `ReportsPage` add a report-type choice or a third format entry `WR roster (XLSX)`; `ReportsRemoteDataSource` gets one more method hitting the new endpoint with the same bytes + filename handling; no other client logic changes (the file is saved by the existing `saveToDownloads`). Add the l10n string(s) to `app_localizations.dart`.
4. **Writing rules** (apply section 1 exactly): sheet `<MON><YY>` and sheet `AL <YY>`; widths and row heights as in 1.2; day block with merged day/weekday/NOTES/person cells on two-row days; thick separators at role changes; black spacer; legend block with its fills; count rows only for the same people the workbook counts (see Q2); comp rows; signature and notes block; page setup `paperSize=9, orientation=portrait, scale=68, fitToPage, fitToWidth=0`, margins .25/0/.5/.5/.05/0, zoom 80; no frozen panes. Write colours as plain RGB hex (table in 1.1). Cell values are strings for codes and day numbers (workbook stores them as text with format `@`), counts as ints.
5. **Cell safety**: codes and labels come from enums and the code column, but any free text (comp notes, if built from names) should still pass `escape_cell`. Person codes like `A1` are never formula-like.
6. **Tests**: `backend/tests/test_report_roster.py` loads the produced bytes with openpyxl and asserts: sheet name, A1 text, merged ranges for a month with one- and two-row days, column widths, `F2..` = codes in order, weekend fills on A/B, legend cells, row offsets after the day block, count rows equal grid counts, comp rows = recomputed balances, page setup. Run for months of 28, 30 and 31 days.

**Template file or openpyxl-from-scratch?** Shipping the owner's workbook as a template and filling it is NOT simpler here, and openpyxl-from-scratch is the recommended route:
- the layout is not fixed: the number of rows per day depends on the month's flights (1 or 2 per day), merged ranges, the spacer, legend, totals and notes all move, and months have 28-31 days; a template of one month would need rows inserted/deleted, which openpyxl does not do for merged cells, borders and row heights (it shifts nothing);
- the template contains the owner's real people (names in F2:N2, A72, A76..A79, `AL 26!C6:G6`) and leftover hand colouring, which would have to be scrubbed on every run and kept out of the repository;
- it would bind deployment to a data file (packaging in the Windows installer and Docker) for no layout gain.
A template only wins if the owner wants to hand-edit the look later without code (a small approach: store a template for styles only and read fonts/fills from it). Not worth it for a single fixed layout; keep all styling constants in one dict at the top of `roster_xlsx.py` so edits are one-line.

Effort estimate: one new module (~250 lines), one service function, one route, one Flutter method plus a dropdown entry, one test file.

---

## 4. Shift time frames

### 4.1 Current state (grep of backend and Flutter)

- **No shift start/end times exist anywhere.** No `05:30`, `13:05`, `06:20`, `13:55` as shift hours; no shift table; no setting. Searched: `backend/app`, `attendance_scheduler_app/lib` (including the time-clock pages and `clock_table.dart`).
- The only hard-coded clock times are the default flight presets in `core/bootstrap.py` (`ensure_default_flight_presets`): HAN-FRA 37/36 sta 06:00 / std 13:55, SGN-FRA 31/30 sta 06:30 / std 13:35 (the workbook shows 0650/1305, a different schedule). These are flight times (STA/STD in Frankfurt local time), editable in the flight presets page, not shift hours. Note the coincidence that `13:55` is the std of 37/36 and 13:05 the std of the 31/30 in the workbook.
- Workbook legend defines duty by rule instead of fixed hours: `A = till STD - 60 minutes`, `D = briefing time - 40 minutes`; the owner now wants explicit frames: A about 05:30-13:05, D about 06:20-13:55; A+D = 05:30-13:55, earning one comp day the following month. The app already earns that comp day at month close (`carry_over_math.comp_balance`: each A/D = +1 CD, counted into `User.carry_comp` by `calculation_service`) and describes `A/D` as "2 working days".
- **Time clock** (`models/time_clock.py`, `services/time_clock_service.py`, `time_clock_page.dart`, `clock_table.dart`): stores `check_in_at` / `check_out_at` (UTC, tz-aware, one row per person per day, bucketed in `settings.TIMEZONE`, default `Europe/Berlin`). The admin board compares punches only with the DAY CODE (`DUE_AT_WORK` codes: A, D, A/D, AD, O/D, T), producing `absent`, `missed_out`, `off_day`, `working`, `ok` and tints; it never compares a punch time with any shift start or end. `workedTime(checkIn, checkOut)` just subtracts. The admin correction form (`correct`) takes explicit in/out times, with no default from a shift. `business_time.local_hm` formats a moment in the business zone.
- **Settings**: no settings table, no admin settings screen. Configuration lives in environment variables via `core/config.py` (`Settings`: timezone, annual leave default, `HOLIDAY_COMP_EFFECTIVE_FROM`, autorun day, retention ...). Admin data screens in the app: users, flights, flight presets, holidays (`holidays_page.dart`), reports, attendance, dashboard. The closest existing pattern for a small admin-edited table is **holidays** (`models/holiday.py`, `holiday_service`, `endpoints/holidays.py`: `GET` for any active user, `PUT` admin upsert with audit, router + `holidays_page.dart` + nav entry in `home_shell.dart`) and **flight presets** (`FlightPreset` rows seeded by bootstrap if empty).

### 4.2 Minimal proposal

**Data model.** A new table `shift_times` (new Alembic revision after the current head; note `0013_swap_counterpart_consent.py` is still untracked in this checkout, so number the new revision after whatever is the head when the work starts):

| Column | Type | Notes |
|---|---|---|
| `id` | int PK | |
| `code` | `String(4)`, unique | `A`, `D` (only these two are editable rows) |
| `start_time` | `Time` not null | A 05:30, D 06:20 |
| `end_time` | `Time` not null | A 13:05, D 13:55 |
| timestamps | `TimestampMixin` | |

Seed both rows in bootstrap exactly like `ensure_default_flight_presets` (insert only when the table is empty, never overwrite admin edits). No row for `A/D`: its frame is derived = `min(start)` to `max(end)` of A and D (05:30-13:55), so it can never disagree with its parts. Validation: `start < end`, 5-minute resolution not required (any `HH:MM`).

**API.** `GET /shift-times` (any active user: `[{code, start, end}]` plus the derived `A/D` entry, `HH:MM` strings) and `PUT /shift-times/{code}` (admin only, body `{start, end}`, audit `shift_time.update`, 400 if `start >= end`, 404 for an unknown code). Same shape as `endpoints/holidays.py`; register a router in `api/v1`.

**Where the admin edits it.** A small card/section on an existing admin screen rather than a new page: put it on the Flight presets page (the same "station parameters" family: flight times and shift times), two rows `A  [05:30] - [13:05]` and `D  [06:20] - [13:55]` with time pickers and a Save, plus l10n strings. If the owner prefers a dedicated destination, a new `shift_times_page.dart` mirrors `holidays_page.dart`.

**Where the values are used (minimum).**
1. Time clock: show the day's frame on the time-clock page (`time_clock_page.dart`) under the code, e.g. `A 05:30-13:05`, and `A/D 05:30-13:55`; use it as the default for the admin's correction dialog (`PUT /attendance/clock/staff` default check-in/out).
2. Report legend: the WR roster legend lines `A= ARR duty` / `D = DEP duty` can append the times (only if the owner asks, because the workbook legend text has no times, Q9).
3. Optional later (not in the minimal scope): late / early-leave flags on the admin board by comparing punches with the frame (tolerance setting needed first), and the A/D comp-day explanation `05:30-13:55`.
Do not change the scheduler or `AttendanceCode` for this; the frames are display and time-clock data only.

---

## 5. Open questions for the owner (each with a recommended default)

1. **Column order and group separators.** The file has people in groups {2}{2}{4}{1}; the 4-person group is clearly the fixed group (role A). Which roles are the 2, the 2 and the 1? Default: order by role `M, T, F, A` then code, thick separator at every role change; today's role mapping is confirmed with the owner's own list before release.
2. **Count rows (A/D/A-D/CD/O-D/T/S/B/AL and comp rows).** In the file they are filled only for the 4 A-group people and the last person, blank for the other 4. Default: fill them for every person column (more complete, still the same structure); if the owner wants it identical, restrict to role A plus the 1-person group.
3. **`TTL n WORKING DAYS` and `X = OFF DAY (INCL PH): nn DAYS`.** In the file it is typed (21 and 09, the same for everybody). Default: n = days in the month minus the median number of `X` over the columns, `nn` = that median; same value in `TTL DAYS` row for everybody. If X counts differ per person, the per-person value is shown only in row 66.
4. **Flight rows when a day has no flight / a pair with only one leg.** Not present in the file. Default: still write one row with `C` and `D` empty so the day exists; a pair with a single leg shows only the leg it has.
5. **Source of the daily code when no actual exists.** Default: actual records first, then the published plan cell, then empty (a draft or missing roster gives an empty cell, never a guess).
6. **Holidays.** The file has no holiday styling. Default: no extra fill on holiday days (only weekends get the C6E0B4 fill); mention holidays only through `X (INCL PH)`.
7. **Code `AD`** (two shifts, no comp day) is not in the workbook legend. Default: export it as `A/D` so the workbook vocabulary is unchanged, count it into the `A/D` row but not into the comp earned figure.
8. **Signature line.** `Checked by Mr Toan on:` contains a person's name. Default: export `Checked by:` + `on:` without any name or date, and `Approved by GM on:` unchanged.
9. **Shift times in the legend.** Default: keep the legend text exactly as in the file (no times); the times appear only in the app (time clock and shift-time setting).
10. **Second sheet `AL 26`.** Default: export it (per-person leave days per month, quota from `annual_leave_quota`, `Rest` = quota - used), using codes for names, labels in German as in the file (`Urlaubstageübersicht <year>`, German month names), because the app has the data and the report is called a copy of the workbook. If the owner wants only the roster sheet, skip it.
11. **Comp notes below the table** (`Compensation Days from <previous month> as follows:` + one line per person). Default: generate `<code>: <n> - <DDMON> A/D duty assigned` from the previous month's A/D days, and `... A/D instead of <planned code>` when the plan had a different code; no free text.
12. **Weekend fill on A/B only** (as in the file) vs the whole row. Default: A/B only, as in the file.
13. **Do `A` and `D` frames overlap by definition?** A 05:30-13:05 and D 06:20-13:55 overlap; the A/D frame is 05:30-13:55. Default: confirm A/D = earliest start to latest end, computed, not stored.
14. **Is the shift frame the same on every weekday, or does it follow the day's flights?** The workbook legend ties duty to flight times (`STD - 60`, `briefing - 40`), and day 28 has different flight times. Default: one fixed frame per shift (as the owner described), the same on every day, editable by the admin.
15. **Comp day timing.** The workbook posts the comp day of an A/D the following month (shown in `previous month` and the notes), while the app earns it at month close. Default: keep the app behaviour; the report shows `present month` = comp earned this month, `previous month` = balance at the month start, `in TTL` = previous + present - used. (The workbook's `present month` row was all zeros, so a difference in those cells is expected.)
