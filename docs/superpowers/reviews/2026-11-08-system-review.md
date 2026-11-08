# Rà soát toàn hệ thống — 2026-11-08 (main @ 64a7532)

4 reviewer chạy song song (backend/API, engine, Flutter, vận hành/CI/docs), chỉ đọc, không sửa repo.
Probe tái hiện nằm trong scratchpad của phiên. Các mục "Open questions" trong `docs/design-decisions.md`
đã được loại khỏi danh sách này.

Ký hiệu bằng chứng: **TH** = đã tái hiện bằng chạy thật, **DV** = đã dò code từ đầu tới cuối,
**NG** = nghi ngờ, chưa xác minh. Dấu ✔ = đã tự kiểm lại trong code.

## A. Nghiêm trọng (sửa trước khi dùng thật)

| # | Vấn đề | Vị trí | BC |
|---|---|---|---|
| A1 ✔ | Backend chạy với DB thật nhưng `ENVIRONMENT=dev`: mỗi lần khởi động **đặt lại mật khẩu admin về mặc định**, bật lại admin, tắt cửa sổ đăng ký nghỉ, CORS `*`, `AUTO_CREATE_TABLES=true` | `backend/.env`, `app/core/bootstrap.py:100-110`, `config.py:36` | TH |
| A2 ✔ | Báo ốm + tự thay người luôn lỗi 422: app không gửi trường `code` bắt buộc | `attendance_remote_datasource.dart:92-96` vs `schemas/attendance.py:13-17` | TH |
| A3 ✔ | Admin chuyển sang tháng chưa tạo lịch vẫn thấy lưới tháng trước; bấm Publish sẽ **publish nhầm tháng trước** | `schedule_provider.dart:61-76`, `schedule_page.dart:116-119,519-524` | TH |
| A4 ✔ | CI trên main đỏ: 3 golden Flutter lệch 0,9–2,2% trên Ubuntu nên build Windows bị bỏ qua; bước "Tests on PostgreSQL" đỏ vì lỗi khoá ngoại (B2, fixture `test_user_admin_guard` xoá user còn ô lịch), production guard smoke bị bỏ qua | `test/visual_golden_test.dart`, `ci.yml` | TH |

## B. Quan trọng — backend

| # | Vấn đề | Vị trí | BC |
|---|---|---|---|
| B1 ✔ | Xuất CSV/XLSX: tên người tự đăng ký kiểu `=HYPERLINK(...)` thành công thức Excel (CSV injection); báo cáo còn gồm cả tài khoản pending/disabled | `report_serializers.py:32-48`, `report_service.py:16-18` | TH |
| B2 ✔ | Admin tự xoá mình: xoá xong mới ghi audit với actor đã bị xoá → 500 trên PostgreSQL, không có dòng audit | `endpoints/users.py:74-75` | TH |
| B3 ✔ | Xoá một admin: xoá luôn mọi đơn đổi ca người đó đã duyệt (của nhân viên khác); nếu admin đó từng duyệt self-arrange thì 500 vì khoá ngoại | `user_service.py:315-320` | TH |
| B4 ✔ | Đơn đổi mã (`change_code`) đè được ô AL/CD: phép vẫn bị trừ quota, ngày nghỉ bù biến mất | `schedule_service.py:223-236` | TH |
| B5 | Import Excel chuyến bay có 2 dòng trùng ngày + FLT → lưu 2 bản ghi; sau đó sửa tay 500, import lại 422 mãi | `flight_service.py:200-218`, `models/flight.py:32-42` | TH |
| B6 | Báo ốm tự thay người có thể chọn người đã bị disable | `attendance_service.py:156-162,207-208`, `sick_backfill.py:54-61` | TH |
| B7 | Seed admin bị xoá sẽ tự sinh lại mỗi lần khởi động, kể cả prod | `bootstrap.py:89-99` | TH |
| B8 | `AUTO_CREATE_TABLES` + Alembic: bật app trước khi migrate làm `alembic upgrade` lỗi DuplicateTable; hướng dẫn khôi phục "stamp 0001" sai (đúng là `stamp head`) | `config.py:54`, `deployment-guide.md:37-38` | TH |
| B9 | Test ghi vào bất kỳ DB nào `DATABASE_URL` trỏ tới (conftest dùng `setdefault`) | `tests/conftest.py:16` | DV |
| B10 | Dockerfile `COPY . .` không có `.dockerignore` → image chứa `backend/.env` thật | `backend/Dockerfile:18` | DV |

## C. Quan trọng — engine xếp lịch

| # | Vấn đề | Vị trí | BC |
|---|---|---|---|
| C1 ✔ | Một hàm mục tiêu gộp, giới hạn 30 s, không đặt số luồng; kết quả FEASIBLE coi như OPTIMAL → máy 1 CPU sinh vi phạm giả (7–14 slack) dù có lời giải sạch | `engine.py:65-79`, `config.py:82` | TH |
| C2 | Vi phạm của bản nháp autorun không được lưu hay hiển thị; Publish không chạy kiểm tra lại → admin có thể publish lịch thiếu người mà không biết | `schedule_service.py:104-139,186-196`, `schedule_autorun.py:62-72` | DV |
| C3 | Nghỉ tháng 5 ngày nằm trọn 1 block 7 ngày luôn sinh vi phạm "nghỉ liền quá dài" (xung đột D5 với luật chuỗi nghỉ) — **cần owner quyết** | `constraints_off_days.py:43`, `constraints_off_chain.py:48-59` | TH |
| C4 | Autorun: máy tắt lúc 00:05 ngày 21 là mất tháng, không chạy bù; log app không bao giờ in ra (không cấu hình logging) | `schedule_autorun.py:44,89` | TH |

## D. Quan trọng — Flutter

| # | Vấn đề | Vị trí | BC |
|---|---|---|---|
| D1 | Đăng xuất không xoá dữ liệu màn hình: người đăng nhập sau thấy đơn nghỉ/chấm công của người trước (máy dùng chung) | `auth_provider.dart:104-121` + các provider | TH |
| D2 | Lỗi quản lý user (409 admin cuối, trùng username, 422 quota) không hiện đúng, chỉ "Could not load users." | `user_management_datasource.dart:57-115` | TH |
| D3 | Bảng duyệt đổi ca không hiện ai xin, bỏ cảnh báo luật, không tải lại lưới sau khi duyệt | `shift_change_dialog.dart:206-273`, `schedule_page.dart:169` | DV |
| D4 | Màn Leaves chỉ tải 1 lần mỗi lần mở app, không có nút làm mới | `leaves_provider.dart:61-64,207` | TH |
| D5 | Reports: bộ chọn năm/tháng/định dạng khó tìm; "Full year" đặt month=0 gây lỗi; nhãn hiện key thô | `reports_page.dart:24-34,93-134` | TH |
| D6 | App không trỏ được sang server thật bằng `--dart-define` vì `.env` đóng gói (localhost) được ưu tiên | `app_config.dart:17-23` | DV |

## E. Nhỏ (gom nhóm)

- **Validate đầu vào:** `month=13`/`year=0` trả 500 thay vì 422 ở nhiều endpoint, 3 cái nhân viên gọi được. Ghi chú dài hơn cột DB gây 500 trên PostgreSQL. Tạo đơn đổi ca gần như không kiểm tra (counterpart không tồn tại → 500, ngày không có lịch vẫn nhận, swap khác role chỉ lỗi lúc duyệt).
- **Đồng thời:** bấm duyệt swap 2 lần có thể đổi ngược lại (thiếu `with_for_update`) — NG.
- **Riêng tư:** ghi chú "recently sick — forced A/D cover" lưu trên dòng chấm công thường của người thay (dữ liệu sức khoẻ). Seed chấm công từ bản nháp làm nhân viên thấy mã chưa publish.
- **i18n:** một số lỗi backend còn tiếng Anh cứng; Flutter thiếu key `year`, `month`, `format`, `requestLeave`; toast lỗi hiện "ApiException(409)…" hoặc danh sách 422 thô.
- **Giờ:** vài chỗ dùng ngày của máy thay vì `business_today()`; time clock ghi cứng `Europe/Berlin`.
- **Engine:** không tất định dù docs nói có; 1 người A nghỉ vào ngày 2 cặp → INFEASIBLE; không có người A thì engine không báo thiếu; checker bỏ sót vài vi phạm ở biên tháng/sau AL; chuỗi nghỉ không nhìn tháng trước; ngày nghỉ đẹp đếm khác nhau giữa engine và lịch sử; CD trước mốc 06/11 bị trừ vào nghỉ bù ngày lễ mới; force-regenerate tháng đã publish để lại chấm công seed cũ; người duyệt/disable sau khi tạo lịch không có hàng/vẫn bị tính; `build_boundary_states` tải toàn bộ lịch sử mỗi lần.
- **Flutter:** ngày kết thúc nghỉ có thể trước ngày bắt đầu; user bị disable giữa phiên không bị đăng xuất (chỉ xử lý 401, không xử lý 403); hộp chấm công cho chọn mã sai role; chọn người swap khác role; batch chuyến bay hiện sai tháng khi lỗi.
- **Vận hành:** migration dùng `now()` chỉ chạy trên PostgreSQL; production guard còn lỗ (chấp nhận SQLite, CORS `*`, retention < 24 tháng, TIMEZONE sai); Alembic lỗi khi mật khẩu có `%`; script guard bị vượt qua bằng `?host=`; script backup in mật khẩu và truyền trên dòng lệnh; không có file lock dependency; `.gitignore` thiếu `*.db`; 3 file `.DS_Store` bị track; action CI chỉ ghim tag lớn; `/docs` công khai ở prod.

## F. Tài liệu lệch code

- `README.md:79,99-100` và `docs/development-roadmap.md:19,25-27`: số test cũ (239/60), thực tế 291/65; README nói golden pass trên CI, thực tế đỏ.
- `docs/deployment-guide.md`: mô tả Docker + HTTPS + Postgres EU, thực tế backend dev-mode trên máy trạm qua Tailscale; "stamp 0001" sai; nói CI upload bản Windows nhưng bước đó đang bị bỏ qua.
- `docs/system-architecture.md:33,85`: nói vi phạm được lưu và engine tất định, cả hai sai.
- `backend/README.md`: số user demo sai (thực tế T×2, F×2, A×6), thiếu 4 nhóm endpoint.
- `docs/superpowers/test-guide-2026-11-07.md:3,52,65`: "chưa push" đã lỗi thời; log autorun không in ra; CI Ubuntu đã chạy và golden đỏ.

## Đã kiểm và ổn

RBAC/IDOR, che S với nhân viên, audit fail-loud, i18n backend en/vi khớp 100%, luật đăng ký nghỉ và quota,
đồng bộ chấm công seed, chặn tạo lại lịch, hợp đồng API Flutter↔backend (trừ A2), gate role trên Flutter,
khôi phục phiên, trọng số engine, khối tuần D2, nghỉ bù D1, schema migration khớp model trên PostgreSQL
(0 khác biệt), không có secret thật trong lịch sử git.
