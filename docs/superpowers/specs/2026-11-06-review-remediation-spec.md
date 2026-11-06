# Spec: Khắc phục sau review toàn dự án (2026-11-06)

Căn cứ: `PROJECT_OVERVIEW.md` (spec khách, bản 07/2026), `docs/design-decisions.md`
(quyết định owner), kết quả review working tree ngày 2026-11-06 (backend + Flutter,
chạy thật pytest/ruff/mypy/flutter test, tái hiện lỗi bằng API).

## 1. Quyết định của owner (Ngọc, 2026-11-06)

| # | Quyết định | Trạng thái |
|---|---|---|
| D1 | Ngày lễ là **ngày làm việc bình thường**; ai đi làm đúng ngày lễ được **+1 ngày nghỉ bù (CD)** tháng sau, áp dụng cho **mọi role** | Chốt (owner xác nhận lần 2, 2026-11-06) |
| D2 | Tuần = block 7 ngày tính từ ngày 1, đuôi tháng tính tỉ lệ | Chốt, giữ code |
| D3 | Nhóm M/T không có định biên theo ngày | Chốt, giữ code |
| D4 | Làm **"phép năm còn lại"**: định mức/người do admin đặt, còn lại = định mức − ngày AL đã duyệt trong năm | Chốt. Giả định: định mức mặc định 30 ngày (config), mọi AL đã duyệt đều trừ |
| D5 | Phép AL **không** thay thế 2 ngày X của tuần (giữ quyết định #4 như code hiện nay) | Chốt (owner 2026-11-06: "giữ nguyên như code") |
| D6 | Ưu tiên cặp nghỉ T7+CN > T6+T7 > CN+T2 | **Chưa chốt** (câu 4 nhắc có, câu 5 nói giữ code = không có). Task tuỳ chọn |
| D7 | Định biên nhóm A là tối thiểu; người thừa ngày 1 cặp làm gì | **Chưa chốt** → giữ code, không sửa |
| D8 | Time clock, self-arrange, role F | Chưa có chỉ thị bỏ → giữ nguyên |

## 2. Lỗi phải sửa (đã tái hiện bằng API thật, chế độ staging)

| # | Lỗi | Vị trí |
|---|---|---|
| B1 | Tạo lại lịch xoá sạch chỉnh tay và trạng thái publish; `force` bị bỏ qua; nhân viên nhận 404 | `backend/app/services/schedule_service.py:78-103` |
| B2 | Tự đăng ký chọn được role M; admin duyệt là thành admin | `backend/app/api/v1/endpoints/auth.py:25`, `schemas/user.py:14` |
| B3 | Gửi `leave_type=monthly` thì nghỉ 10 ngày lọt qua luật phép năm | `backend/app/services/leave_service.py:95` |
| B4 | Duyệt/huỷ nghỉ sau khi đã tạo lịch: lịch không đổi, chỉ cảnh báo | `leave_service.py:178-183` |
| B5 | Sửa lịch đã publish (override, đổi ca, self-arrange) không chạm bản chấm công đã seed | `schedule_service.py:163-174`, `attendance_service.py:68-92` |
| B6 | Xếp hạng xung đột nghỉ dùng cột `carry_comp` cũ; engine tính từ lịch sử; `close_month` tính từ actuals | `leave_conflict_resolver.py:92`, `calculation_service.py:55` |
| B7 | Engine đếm chuỗi nghỉ dài chỉ bằng X; recheck đếm X/CD/S/AL | `scheduler/constraints_off_chain.py:52` |
| B8 | Autorun 02:00 ngày 20 nhưng cửa sổ đăng ký mở hết ngày 20 | `schedule_autorun.py:36,77`, `leave_windows.py:46` |
| B9 | Script reset mật khẩu toàn bộ về `admin123`, không chốt môi trường | `backend/scripts/reset_all_passwords.py` |
| B10 | Luật "người vừa ốm bị ưu tiên A/D" chỉ nhớ trong tháng | `attendance_service.py:176-196` |

## 3. Flutter thiếu hoặc sai

| # | Vấn đề | Vị trí |
|---|---|---|
| C1 | Nhân viên không có cách xin đổi ca (dialog có nhưng không nơi nào gọi) | `schedule_page.dart:124-126`, `shift_change_dialog.dart:13` |
| C2 | Nhân viên không có màn xem chấm công của mình | `app_router.dart:21-27` |
| C3 | Hộp sửa ô lịch cho chọn mọi mã kể cả S | `schedule_page.dart:367` |
| C4 | Nhân viên xem lịch thấy "User 7" vì `/users` chỉ admin | `schedule_page.dart:199` |
| C5 | `registrationOpen: true` ghi cứng, chuỗi "unrestricted in development" đi vào release | `leaves_page.dart:54-55`, `app_localizations.dart:115` |
| C6 | Không khôi phục phiên: mở app là phải đăng nhập lại | `auth_provider.dart:36` |
| C7 | Nút Generate/Publish hiện cho mọi role | `schedule_page.dart:122-123`, `business_views.dart:252-253` |
| C8 | Hộp ngày lễ không gate theo isAdmin | `attendance_page.dart:83` |
| C9 | `carryComp: 0` ghi cứng | `leaves_provider.dart:135` |
| C10 | 3/18 golden test fail (ảnh mẫu cũ) | `test/visual_golden_test.dart` |
| C11 | Chuỗi tiếng Anh ghi cứng | `reports_provider.dart:74,84`, `reports_page.dart:186`, `flights_provider.dart:154`, `self_arrange_pending_panel.dart:55` |

## 4. Tài liệu và repo

- 92 file chưa commit từ 25/07 (gồm đợt sửa 03/09).
- README nói "flutter test clean" (sai), codebase-summary nói 99 test/Alembic 0002 (thực tế 188/0007),
  system-architecture ghi sai trọng số và domain, code-standards nói audit "best-effort" (đã fail-loud).
- `DESIGN/DESIGN_IMPLEMENTATION_GUIDE.md` và `DESIGN/UI_STYLE_GUIDE.md` viết cho dự án Next.js khác.

## 5. Thế nào là xong

- Mọi lỗi B1–B10 có test tái hiện và test đó pass.
- D1, D4 có trong engine + service + recheck + self-arrange + Flutter, có test.
- C1–C11 sửa xong; `flutter analyze` sạch; `flutter test` 100% pass (golden cập nhật).
- `ruff check app tests`, `mypy app`, `pytest` xanh; CI xanh.
- `docs/design-decisions.md`, README, codebase-summary, system-architecture, code-standards, changelog phản ánh đúng code.
- Những điểm chưa chốt (D6, D7) ghi rõ trong design-decisions "Open questions".
