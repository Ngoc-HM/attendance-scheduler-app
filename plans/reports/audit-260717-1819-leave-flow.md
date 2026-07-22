# Audit luồng nghỉ phép (F-05/F-06) — 2026-07-17

3 auditor độc lập (backend / solver / Flutter). Verdict: **luồng lõi ĐÚNG**
(đăng ký own-only, cửa sổ 1–20 tháng trước + phép năm đăng ký năm trước,
chặn trùng, duyệt idempotent, ghim vào lịch khi generate, role F đầy đủ).

## Đã vá cùng ngày (kèm test, 157/157 pass, analyze sạch)
1. Duyệt phép trùng tháng ĐÃ tạo lịch → giờ trả **cảnh báo "lịch tháng đó đã cũ,
   cần Generate lại"** hiển thị cho admin (backend warnings + toast).
2. Quota nghỉ 2 ngày/block: **cap theo độ dài block** — nghỉ phép trọn tuần
   không còn sinh vi phạm giả (solver + violation-checker nhất quán, test đổi).
3. Lệch trừ/hoàn phép: hoàn phép giờ áp cho CẢ hai loại nghỉ (khớp chiều trừ đã
   được test chốt); duyệt khi user biến mất → 404 thay vì lặng lẽ bỏ check.
4. Lỗi backend trả về **đúng ngôn ngữ app** (Accept-Language → contextvar t()).
5. Nhân viên: hàng của mình hết hiện "User 5" + bỏ request GET /users 403 thừa.
6. Nút Duyệt/Từ chối **ẩn hẳn** với nhân viên (trước là nút bấm không làm gì).
7. Banner "Đang mở đăng ký" giờ **đúng theo ngày** (đóng từ 21+, đổi màu cảnh báo).
8. Dialog đăng ký: thiếu ngày báo lỗi thay vì im lặng; lỗi 400 giữ nguyên dialog
   (không mất dữ liệu đã nhập).

## Chưa vá — cần owner quyết (backlog)
- **Hủy phép đã duyệt**: hiện không có cách rút lại (kể cả admin) — cần quyết
  flow un-approve (hoàn phép + gỡ ghim + cảnh báo lịch).
- Duyệt nhiều người nghỉ cùng ngày không bị chặn/cảnh báo staffing lúc duyệt
  (chỉ lộ khi generate) — resolver xếp hạng là "advisory" by design?
- Nghỉ tháng vắt qua đầu tháng sau lách cửa sổ đăng ký của tháng sau (check
  theo start date) — hiếm, cần chốt luật.
- Chuỗi nghỉ vắt tháng (4 ngày cuối tháng + 3 đầu tháng = 7 nghỉ liền) không bị
  luật max-5-off phát hiện (không có carry cho off-run).
- Nghỉ tháng 5 ngày gọn trong 1 block → block nghỉ 7 ngày liên tục → vi phạm
  max-5-off vẫn báo (đúng chính sách "nghỉ dài phải là phép năm"?).
- Không có unique constraint DB chống 2 đơn trùng submit song song (app-level ok).
- Client date-picker chưa mô phỏng hết cửa sổ (sau ngày 20 chọn tháng sau vẫn 400).

## Câu hỏi tồn đọng
1. Nghỉ tháng có trừ phép năm không? (hành vi hiện tại + test: CÓ — giữ nguyên.)
2. Chính sách un-approve phép đã duyệt?
3. Vi phạm max-5-off cho nghỉ tháng 5 ngày/block: chấp nhận như tín hiệu chính
   sách hay cần miễn trừ?
