# Nguyên lý tạo lịch tự động (báo cáo cho chủ dự án — không code)

## 1. Bản chất
Không phải AI/máy học. Là **bộ giải ràng buộc** (Google OR-Tools CP-SAT) — kiểu
"giải sudoku": liệt kê mọi cách điền lịch hợp lệ theo luật, rồi chọn phương án
có **tổng điểm phạt thấp nhất**. Cùng đầu vào → luôn ra cùng một lịch (seed cố
định). Giới hạn giải: 30 giây/tháng.

## 2. Đầu vào (lấy từ dữ liệu trong app)
- Nhân sự đang hoạt động + 3 số dư mang từ tháng trước: **nợ ngày bù CD**,
  **chuỗi ngày làm dở** cuối tháng trước, **số lần đã nghỉ trúng T7/CN/lễ**.
- Chuyến bay từng ngày (0/1/2 cặp — admin nhập bằng preset).
- Nghỉ phép đã duyệt (AL/CD) — bị **ghim cứng** thành ngày nghỉ.
- Ngày lễ (chỉ để tính "nghỉ trúng ngày đẹp", KHÔNG phải ngày nghỉ — lễ/T7/CN
  vẫn là ngày làm bình thường theo quyết định 18/06).

## 3. Cách máy "nghĩ"
Mỗi (người × ngày × mã) là một ô lựa chọn có/không. Bộ mã theo role:
- **A** (cố định): A · D · A/D · X · CD — chịu đủ luật + luật bay
- **T** (linh hoạt): AD · X
- **M** (quản trị): O/D · X
- **F**: AD · X — chỉ chịu duy nhất luật nghỉ 2 ngày/tuần
Mỗi người mỗi ngày đúng 1 mã.

## 4. Hệ thống luật (theo mức ưu tiên phạt)
**Cứng tuyệt đối (không bao giờ vỡ):** 1 mã/ngày; ngày nghỉ phép đã duyệt = nghỉ.

**Luật lớn — phạt 10.000/lần vỡ:**
1. Đủ người cho chuyến bay (chỉ nhóm A): 1 cặp bay → 1 người ca A + 1 ca D;
   2 cặp → 1 ca A + 2 ca D.
2. Nghỉ đúng **2 ngày X mỗi block 7 ngày** (block neo từ ngày 1: 1–7, 8–14…;
   block cuối lẻ tính tỷ lệ). Nghỉ phép/ốm KHÔNG tính vào 2 ngày này —
   người có phép vẫn được đủ 2 ngày nghỉ quy chế.
3. Không làm quá **5 ngày liên tục** (tính cả chuỗi mang từ tháng trước). F miễn.
4. Không nghỉ quá **5 ngày liên tục** (trừ nghỉ phép năm đã đăng ký). F miễn.

**Nợ ngày bù — phạt 2.000:** làm ca đúp A/D tháng này → tháng sau máy TỰ xếp
trả ngày CD (nhân viên không phải đăng ký). Nếu trả CD làm thiếu người bay thì
ưu tiên chuyến bay, báo nợ lại.

**Điểm "đẹp" (nhỏ — chỉ tinh chỉnh sau khi các luật trên thỏa):**
- Chia đều tổng ca A và tổng ca D **giữa những người nhóm A** (trọng số 100).
- Xoay vòng công bằng suất **nghỉ trúng T7/CN/lễ** — cộng dồn lịch sử nhiều
  tháng, ai hưởng nhiều rồi thì nhường (30).
- 2 ngày nghỉ trong tuần nên **liền nhau** (15).
- Ca đúp A/D là **phương án cuối cùng** (phạt 1.000/lần) — chỉ dùng khi không
  còn cách phủ chuyến bay.

## 5. Triết lý "không bao giờ bó tay"
Máy KHÔNG bao giờ trả lời "không xếp được". Mọi luật lớn đều có "van xả":
khi bắt buộc phải vỡ, máy vẫn ra lịch trọn tháng + **danh sách vi phạm có tên**
(ngày nào thiếu người, ai thiếu ngày nghỉ…) để admin quyết. Admin sửa tay ô nào
cũng được lưu ngay, máy kiểm lại và cảnh báo nếu vết sửa phá luật (chỉ cảnh
báo, không chặn).

## 6. Vận hành
- Admin bấm **Generate** bất kỳ lúc nào (tạo lại thoải mái, reset về nháp).
- **Tự động**: 02:00 mỗi ngày hệ thống kiểm; đúng **ngày 20** hằng tháng thì
  chốt đăng ký nghỉ tháng sau + tự tạo BẢN NHÁP tháng sau (không bao giờ đè
  bản đã có).
- Nhân viên chỉ thấy lịch sau khi admin **Publish**.
- Ốm (S) giữa chừng: nếu người ốm đang giữ ca bay, máy đề xuất người thay làm
  ca đúp — ưu tiên người vừa ốm xong đang làm ca đơn hôm đó, không có thì chọn
  người ít ca đúp nhất tháng.

## Câu hỏi tồn đọng
- Block 7 ngày neo từ ngày 1 (không phải tuần Thứ 2–CN) — code có cờ
  "confirm-with-customer"; anh/chị đã vận hành theo cách này, nếu muốn đổi sang
  tuần lịch thật thì là thay đổi lớn, cần chốt riêng.
