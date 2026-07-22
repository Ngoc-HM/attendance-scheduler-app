# Bug Audit — attendance-scheduler-app

Date: 2026-07-06 · Method: 5 parallel read-only reviews (scheduler engine · lịch/nghỉ/chấm-công services · calculations/reports/flights · core/API/auth · Flutter) + xác minh trực tiếp bằng code cho các mục nghiêm trọng. Không chạy được engine/tests (thiếu venv ortools trên máy này) — mục scheduler là hand-traced arithmetic.

## Tổng quan mức độ
| # | Sev | Bug | File |
|---|-----|-----|------|
| 1 | **CRITICAL** | Self-register leo thang quyền (role mass-assignment) | `auth.py:26`, `user.py:14`, `user_service.py:53` |
| 2 | HIGH | Shift-change: không kiểm ownership + counterpart tùy ý (IDOR) | `shift_change_service.py:46-82` |
| 3 | HIGH | `swap_with` hoán mã không validate role-domain → cell bất hợp lệ | `schedule_service.py:163` |
| 4 | HIGH | Không thể reject leave đã duyệt → mất số dư phép vĩnh viễn | `leave_service.py:146,165` |
| 5 | HIGH | Off-day X-target không cap → violation ảo + ép thiếu người tuần có leave | `constraints_off_days.py:39` |
| 6 | MED | "Max 5 ngày nghỉ liên tục" bỏ sót CD | `constraints_off_chain.py:50` |
| 7 | MED | Thiếu unique `(day, flt_number)` → dup row + `MultipleResultsFound` 500 | `models/flight.py:32-42` |
| 8 | MED | `apply_presets` mất 1 leg khi 2 preset trùng flt_number | `flight_service.py:317-334` |
| 9 | MED | Không enforce ≤2 preset/ngày phía server | `schemas/flight.py:78` |
| 10 | MED | Default SECRET_KEY/admin-pass/CORS yếu, không guard prod | `config.py:31,41,55` |
| 11 | MED | Flutter roster tổng A/D/OFF sai cho role-T (AD) và role-M (O/D) | `schedule_page.dart:201-205` |
| 12 | MED | Flutter không xử lý 401/token hết hạn → app kẹt "đã đăng nhập" | `api_client.dart:21-37` |
| 13 | MED | `generate()` restore ghi đè AL lên ngày working | `schedule_service.py:81-87` |
| 14 | MED | Sick backfill: cửa sổ "recently sick" reset ở ranh giới tháng | `attendance_service.py:168-188` |
| 15 | MED | `disabled` user vẫn qua `get_current_user` (latent) | `deps.py:26-43` |
| — | LOW | Excel parser abort cả file vì 1 cell lạ / không parse time-fraction | `flight_excel_parser.py` |
| — | LOW | off_pairing penalty âm → thưởng dồn ngày nghỉ | `objective_off_pairing.py:66` |
| — | LOW | leave decide không row-lock → race double-decrement | `leave_service.py:149-159` |
| — | LOW | `created_at` None làm crash sort conflict | `leave_conflict_resolver.py:41` |
| — | LOW | Flutter: export ghi đè file trùng tên; leaves hiện "User {id}" | reports/leaves providers |
| — | NIT | Comment `enums.py` LeaveType ghi ">=5" nhưng code đúng ">5" | `enums.py` |

---

## CRITICAL

### 1. Self-registration privilege escalation (role mass-assignment)
`api/v1/endpoints/auth.py:26` → `schemas/user.py:11-20` → `services/user_service.py:45-58,71-77`

- `POST /auth/register` nhận `UserCreate` kế thừa `role: Role` từ `UserBase`. `_persist_new` gán thẳng `role=payload.role`. `approve()` chỉ đổi `status=active`, **không đụng role**.
- **Khai thác:** người lạ `POST /auth/register {"username","full_name","password","role":"M"}` → account `pending` mang sẵn role M (admin). Admin duyệt hàng chờ F-01 (UI không hiện role) ⟹ attacker thành admin đầy đủ: đọc/ghi dữ liệu sức khỏe `S` (special-category GDPR), toàn bộ user/schedule/report. Kể cả không leo lên M, user tự chọn A/T cũng là sai lệch dữ liệu (không review).
- **Giảm nhẹ:** cần 1 admin bấm approve account pending (không phải remote-admin tức thì) — nhưng admin không có tín hiệu nào để nghi ngờ.
- **Fix:** tách schema self-register KHÔNG có field `role` (ép `Role.T` phía server); giữ `role` chỉ ở path admin `create()`. Cân nhắc cho admin set/confirm role khi approve.

---

## HIGH

### 2. Shift-change không kiểm ownership + counterpart tùy ý (IDOR)
`services/shift_change_service.py:46-82`

- `create_request` set `requester_id = current_user_id` nhưng **không** kiểm requester có cell nào vào `work_date` (message `swap.own_cell_only` tồn tại nhưng không bao giờ dùng). `counterpart_user_id` nhận từ client, không validate (tồn tại? active? ≠ self? có cell hôm đó?).
- Guard `ensure_self_or_admin` (`deps.py:68`) được định nghĩa nhưng **0 call-site** — không có lưới an toàn ownership ở đâu cả.
- **Khai thác:** user thường gửi `swap_with` với `counterpart_user_id` tùy ý. Admin approve → `apply_shift_change` hoán code 2 người ⟹ user chỉnh được cell của đồng nghiệp khác (đẩy ca xấu sang người khác / cướp ngày OFF của họ) mà người kia không đồng ý.
- **Fix:** create-time yêu cầu requester có cell vào `work_date`; validate counterpart là user active ≠ requester và có cell hôm đó; gọi `ensure_self_or_admin` ở mọi handler nhận user id lạ.

### 3. `swap_with` hoán mã không validate role-domain → cell bất hợp lệ
`services/schedule_service.py:159-167`

- `mine.code, theirs.code = theirs.code, mine.code` vô điều kiện. Domain theo role loại trừ nhau (`role_codes.py`: A→{A,D,A/D,X,CD}, T→{AD,X}, M→{O/D,X}). Hoán 1 mã "A/D" của role-A sang role-M ⟹ M giữ "A/D" (mã role-M không bao giờ có). `_recheck_violations` chỉ check consecutive/off-quota/staffing, **không** check tính hợp lệ mã theo role ⟹ cell bẩn được lưu im lặng.
- **Fix:** reject swap trong `apply_shift_change` khi mã kết quả nằm ngoài `codes_for(role)` của user đích (raise 409), hoặc chỉ cho swap cùng role.

### 4. Không thể reject leave đã duyệt → mất số dư phép vĩnh viễn
`services/leave_service.py:137-162, 165-174`

- `decide()` guard `if req.status != pending → 409`, nên KHÔNG thể reject một request đã approved. Hàm bù `revoke_balance_on_reject` tồn tại nhưng **0 call-site** (dead code). Docstring hứa "restore balance on reject of approved" không bao giờ chạy tới.
- **Hệ quả:** approve 1 kỳ annual leave 10 ngày (balance 20→10). Cần hủy → không có đường; balance kẹt ở 10, 10 ngày mất luôn.
- **Fix:** cho phép transition `approved → rejected` và gọi `revoke_balance_on_reject` trên path đó.

### 5. Off-day X-target không cap → violation ảo + ép thiếu người
`scheduler/constraints_off_days.py:39`

- `target = partial_block_off_target(len(block)) + pinned_in_block`, không cap ở `len(block)`. `approved_off_map` pin CẢ monthly LẪN annual leave (không filter `leave_type`).
- **Hệ quả:** role-A nghỉ annual cả tháng → mỗi block 7 ngày: `target = 2+7 = 9` nhưng `sum(X) ≤ 7` → ép `under=2`/block → violation ảo "cần 9 ngày off" + ~90k slack lãng phí cho người đang nghỉ trọn. Tuần có 5 AL + 2 ngày còn lại: ép 2 ngày đó thành X, chống lại staffing chuyến bay → có thể đẩy thiếu người thật.
- **Fix:** `target = min(len(block), partial_block_off_target(len(block)) + pinned_in_block)`; và/hoặc loại ngày annual khỏi `pinned_in_block` (đồng bộ với miễn trừ ở off_chain).

---

## MEDIUM

### 6. "Max 5 ngày nghỉ liên tục" bỏ sót CD — `scheduler/constraints_off_chain.py:50`
Window chỉ đếm `AttendanceCode.X`; `CD` cũng là rest-day (trong `OFF_CODES`) nhưng không đếm. Run `[CD,X,X,X,X,X]` = 6 ngày off liên tục, `sum(X)=5 ≤ 5` → không flag. Fix: đếm cả X + CD (hoặc `WINDOW − sum(working)`).

### 7. Thiếu unique `(day, flt_number)` — `models/flight.py:32-42`
Chỉ có `index=True` trên `day`, không có composite unique. `upsert_flight`/`import_excel` query `(day,flt_number)` rồi `.one_or_none()`. Import 1-request an toàn nhờ autoflush, nhưng race 2-request hoặc ghi trực tiếp có thể tạo dup → lần edit sau `.one_or_none()` gặp `MultipleResultsFound` → 500. Fix: thêm `UniqueConstraint("day","flt_number")` + migration.

### 8. `apply_presets` mất 1 leg khi preset trùng flt_number — `flight_service.py:317-334`
Legs dedup vào `dict[flt_number]` "later wins". 2 preset dùng chung số hiệu → 1 leg bị đè mất; preset có `flt_arr == flt_dep` → chỉ tạo 1 leg thay vì 2. 2 preset seed mặc định (37/36, 31/30) không đụng, nhưng preset custom thì có. Fix: raise 422 khi collision, guard `flt_arr != flt_dep` lúc tạo preset.

### 9. Không enforce ≤2 preset/ngày phía server — `schemas/flight.py:78`
`preset_ids: list[int]` không có `max_length`. Client (`month_batch_dialog.dart`) có chặn ≤2, nhưng server không → gọi trực tiếp API có thể apply 4+ preset (tới 8 leg/ngày). `derive_pairs` clamp về 2 nên scheduler an toàn, nhưng dữ liệu leg dư. Fix: `Field(max_length=2)`, defense-in-depth.

### 10. Default bảo mật yếu, không guard prod — `core/config.py:31,41,55`
`SECRET_KEY="CHANGE_ME_dev_only_secret"`, `FIRST_ADMIN_PASSWORD="admin123"`, `BACKEND_CORS_ORIGINS=["*"]` + `allow_credentials=True`. Không có validator raise khi `ENVIRONMENT=prod` mà vẫn dùng default → deploy quên set env ⟹ ai biết hằng số public trong source có thể forge JWT admin. Fix: `model_validator` raise nếu prod mà còn default; CORS default `[]`.

### 11. Flutter roster tổng A/D/OFF sai cho role-T & role-M — `features/schedule/.../schedule_page.dart:201-205`
`arrivals = a|aD`, `departures = d|aD`, `off = x`. Nhưng role-T toàn `AD`→`ShiftCode.ad` (khác `aD`), role-M toàn `O/D` — cả hai KHÔNG được đếm ở arrivals/departures; OFF chỉ đếm X (bỏ CD/AL). ⟹ nhân viên role-T hiện A=0/D=0 dù đi làm ~20 ngày. Fix: đếm `ShiftCode.ad` vào cả arr+dep; OFF = `!isWorking`.

### 12. Flutter không xử lý 401/token hết hạn — `core/network/api_client.dart:21-37` + router
`_AuthInterceptor` chỉ có `onRequest`, không có `onError`/401; router không có redirect guard; token chỉ in-memory. Token hết hạn hoặc backend restart (seed-admin reset) → mọi request 401, `AuthState.user` vẫn non-null nên app trông "đã đăng nhập", user không bị đưa về login → phải kill app. Fix: `onError` clear token + reset auth + redirect `/login`.

### 13. `generate()` restore ghi đè AL lên ngày working — `schedule_service.py:81-87`
Sau solve, mỗi code bị thay bằng `approved_off.get(user).get(day, code)` vô điều kiện. Nếu solver (vì slack/feasibility) đặt ngày pinned-leave thành working code, restore vẫn ép "AL" ⟹ grid publish lệch với cái engine đã validate. (Solver-dependent, cần chạy engine để chắc.) Fix: chỉ override khi code engine cho cell đó là OFF/X placeholder.

### 14. Sick backfill reset ranh giới tháng — `attendance_service.py:168-188`
`_recently_sick` filter `work_date >= first_of_month` → quy tắc §6 "ai ốm trước bị buộc cover" chỉ trong cùng tháng lịch. Người ốm 31/1 không thể bị buộc cover đồng nghiệp ốm 1/2. Fix: dùng rolling N-day lookback thay vì `>= first_of_month`.

### 15. `disabled` user vẫn qua `get_current_user` — `api/deps.py:26-43`
`get_current_user` không check `status`; chỉ `get_current_active_user` check. Hiện mọi endpoint dùng `ActiveUser`/`AdminUser` nên latent, nhưng disable user không thu hồi được token đang sống (tới 24h). Fix: check `status==active` ngay trong `get_current_user` (single choke point).

---

## LOW / NIT (chi tiết ngắn)
- **Excel parser** (`flight_excel_parser.py`): row có 1 cell lạ ở cột route (vd footer "Total") → `parse_date_cell(None)` lỗi → **abort cả import**. Cell time dạng số Excel (0.25=06:00) không có nhánh float → abort. Fix: skip row khi date+flt_number đều rỗng; thêm nhánh float→time.
- **off_pairing** (`objective_off_pairing.py:66`): `weight*((target-1)-sum(both))` không clamp 0 → khi X liên tục > target-1 thành penalty âm (thưởng dồn nghỉ). Weight 15 << staffing 10000 nên hiếm lật kế hoạch. Fix: shortfall IntVar ≥ 0.
- **leave decide** (`leave_service.py:149-159`): không `with_for_update` → 2 admin approve song song cùng lúc có thể double-decrement âm balance. Thấp (desktop 1 admin). Fix: row-lock hoặc CHECK `balance >= 0`.
- **conflict sort** (`leave_conflict_resolver.py:41`): key `(-carry, created_at, id)`; `created_at` chưa refresh có thể None → `TypeError` khi sort → 500. Fix: `(req.created_at or datetime.min)`.
- **annual window** (`leave_windows.py:52-58`): `today.year == leave_start_year-1` chỉ cho Y+1, mâu thuẫn docstring "Y+1 or later". Fix: thống nhất semantics.
- **Flutter LOW**: export ghi đè file cùng tên (reports_provider) · leaves hiện "User {id}" nếu chưa mở Users page (leaves_provider) · roster index theo dense list, latent misalign nếu 1 user thiếu 1 ngày.
- **NIT**: `enums.py` LeaveType comment "`>= 5 → annual`" lệch với code đúng `span > 5` (`leave_windows.py:28`). Chỉ sửa comment.

## Non-bug đã kiểm tra & OK (để đối chiếu)
Vocabulary code {A,D,A/D,O/D,X…} backend↔frontend đồng bộ · mọi endpoint frontend gọi có route backend khớp (path-level) · JWT có `exp`, alg pin `[HS256]`, không alg-confusion · `UserRead` không lộ `hashed_password` · bcrypt 72-byte truncation cố ý · seed-admin reset cố ý · staffing A/D double-cover đúng · carry_streak head-window đúng · premium-off engine↔month-close nhất quán · comp-days yield đúng · month-nav `DateTime(y,m±1)` roll year đúng · ≤2 preset client-side enforce đúng · OAuth2 form-urlencoded body khớp.

## Câu hỏi chưa chốt (cần xác nhận owner)
1. Bug #5: annual leave có nên nâng target X tuần không? off_chain miễn annual (coi như thay kỳ nghỉ dài) ⟹ có vẻ annual KHÔNG nên đòi thêm 2 X/tuần. Monthly leave thì nâng target (có cap) đúng?
2. Bug #3: swap chỉ cho phép cùng role, hay cho khác role rồi remap mã?
3. Bug #8: `flt_arr == flt_dep` có phải preset hợp lệ (turnaround cùng số hiệu)? collision là hard-error hay last-wins?
4. Bug #11: tổng roster ý nghĩa là "coverage A/D theo cột" hay "ngày công mỗi người"? (quyết định cách đếm AD).
