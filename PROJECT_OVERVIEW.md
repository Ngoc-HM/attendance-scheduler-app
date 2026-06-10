> **Context cho AI/Dev — bản đầy đủ.** Đây là toàn bộ nội dung tài liệu yêu cầu (chuyển full từ Tai_lieu_yeu_cau_HOP_NHAT.docx), không cắt giảm. Phần Phụ lục A là tài liệu yêu cầu gốc của khách (nguyên văn).

---

**TÀI LIỆU YÊU CẦU TÍNH NĂNG**

**Phần mềm Tự động xếp lịch & Chấm công nhân sự**

*Tài liệu mô tả tính năng & thuật toán cho đội phát triển (Dev/AI)*

Phiên bản 1.2 — 06/2026 — Triển khai tại Frankfurt (Đức)

# 1\. Tổng quan

Phần mềm tự động phân lịch làm việc (xếp ca) và chấm công cho nhân sự,
thay cho cách phân ca thủ công bằng bảng in hiện tại (mẫu “WR JUN26”).

  - **Chức năng chính:** tự động xếp lịch — không chỉ là phần mềm chấm
    công thông thường.

  - Hàng tháng, căn cứ lịch bay để lập danh sách chuyến bay (cột FLT),
    sau đó phân bổ nhân lực cho từng chuyến.

  - Yêu cầu chung: đơn giản, dễ thao tác. Ngôn ngữ: Tiếng Anh (ưu tiên),
    có thêm Tiếng Việt càng tốt.

# 2\. Công nghệ sử dụng

| **Thành phần**     | **Công nghệ**                                   | **Ghi chú**                                              |
| ------------------ | ----------------------------------------------- | -------------------------------------------------------- |
| Mô hình triển khai | Cloud                                           | Toàn bộ dữ liệu & xử lý đặt trên Cloud, không lưu cục bộ |
| Backend / Server   | Python — FastAPI                                | REST API; chứa logic nghiệp vụ & engine xếp lịch         |
| Ứng dụng client    | Flutter (desktop Windows)                       | Cài trên máy Windows; số máy không giới hạn              |
| Cơ sở dữ liệu      | PostgreSQL trên Cloud (đề xuất)                 | DB dùng chung cho mọi client; có thể đổi tùy hạ tầng     |
| Engine xếp lịch    | Constraint solver, vd Google OR-Tools (đề xuất) | Chạy phía FastAPI; giải bài toán xếp ca (mục 5)          |
| Xác thực           | Tài khoản + đăng nhập (token/JWT, mức nhẹ)      | App nội bộ nên không cần bảo mật quá gắt                 |

**Lưu ý:** PostgreSQL và OR-Tools là đề xuất; dev có thể chọn phương án
tương đương. FastAPI, Cloud và client Flutter (Windows) là đã chốt.

# 3\. Vai trò người dùng & phân quyền

Tổng 09 nhân sự (số lượng linh hoạt, tùy việc tạo user trên hệ thống).

| **STT** | **Tên** | **Role** | **Tính chất / Quyền** |
| ------- | ------- | -------- | --------------------- |
| 1       | Toàn    | M        | Admin + Linh hoạt     |
| 2       | Chi     | M        | Admin + Linh hoạt     |
| 3       | Vũ      | T        | Linh hoạt             |
| 4       | Trường  | T        | Linh hoạt             |
| 9       | Tùng    | T        | Linh hoạt             |
| 5       | Agne    | A1       | Bắt buộc (cố định)    |
| 6       | Joachim | A2       | Bắt buộc (cố định)    |
| 7       | Long    | A3       | Bắt buộc (cố định)    |
| 8       | Thomas  | A4       | Bắt buộc (cố định)    |

  - **M (Admin + Linh hoạt):** quyền quản trị, phê duyệt phát sinh; lịch
    làm linh hoạt.

  - **T (Linh hoạt):** được gửi xin đổi lịch, admin phê duyệt, không bị
    bắt ép.

  - **A1–A4 (Bắt buộc/cố định):** phải theo lịch hệ thống xếp; xin đổi
    nhưng admin không duyệt thì không được đổi. Nhóm cần xếp chặt chẽ
    nhất.

# 4\. Danh sách tính năng cần làm

Mô tả theo từng module. Chi tiết thuật toán xếp lịch xem mục 5.

## 4.1. Module Tài khoản & Đăng nhập

**F-01 Tạo tài khoản người dùng**

  - Admin tạo tài khoản cho user; HOẶC user tự đăng ký rồi admin phê
    duyệt mới dùng được.

**F-02 Đăng nhập**

  - User đăng nhập để xem lịch và đăng ký nghỉ. App nội bộ — bảo mật mức
    nhẹ.

**F-03 Gán role khi tạo user**

  - Admin gán role (M / T / A1–A4) để hệ thống áp đúng quy tắc xếp lịch
    cho từng người.

## 4.2. Module Nhập lịch bay

**F-04 Nhập danh sách chuyến bay hàng tháng**

**\[ĐÃ CHỐT\]** Hỗ trợ CẢ HAI cách: (1) nhập tay trên giao diện, và (2)
import từ file Excel.

  - Mỗi ngày trong tháng cần biết số cặp chuyến bay (0 / 1 / 2 cặp) để
    làm căn cứ định biên ca.

  - Ghi nhận giờ đến/đi STA/STD theo giờ địa phương Frankfurt (LT FRA).
    Quy ước số hiệu xem mục 8.

## 4.3. Module Đăng ký nghỉ

**F-05 Đăng ký nghỉ hàng tháng**

  - Ngày 5 đầu tháng: nhân sự đăng ký ngày nghỉ theo nhu cầu.

  - Ngày 20: hệ thống đóng đăng ký và chạy xếp lịch tự động (mục 5).

**F-06 Đăng ký nghỉ dài / nghỉ phép năm**

  - Nghỉ dưới 5 ngày liên tục: đăng ký hàng tháng.

  - Nghỉ liên tục từ 5 ngày trở lên: đăng ký vào phần nghỉ phép năm; mở
    đăng ký từ tháng 1 đến tháng 12 của năm trước.

## 4.4. Module Xếp lịch tự động (CHỨC NĂNG CHÍNH)

**F-07 Tự động sinh lịch tháng**

  - Xếp full tự động sau khi đóng đăng ký (ngày 20). Chi tiết input/ràng
    buộc/output xem mục 5.

**F-08 Cân bằng ca A / ca D**

**\[ĐÃ CHỐT\]** Cân bằng tính THEO TỪNG THÁNG (không lũy kế nhiều
tháng): trong tháng, số ca A và số ca D giữa các nhân sự phải ngang
nhau, hoặc ngang nhất có thể.

**F-09 Admin chỉnh tay sau khi xếp tự động**

**\[ĐÃ CHỐT\]** CÓ: sau khi hệ thống xếp tự động, admin được phép chỉnh
tay lịch. Hệ thống nên cảnh báo nếu chỉnh tay làm vi phạm ràng buộc cứng
(mục 5.3).

**F-10 Xử lý nghỉ ốm (S) phát sinh trong tháng**

  - Khi có người nghỉ ốm: bắt buộc có người làm A/D để bù ca trống.

  - Người vừa nghỉ ốm được ưu tiên (bắt buộc) làm A/D nếu sau đó có
    người khác nghỉ ốm.

## 4.5. Module Chấm công

**F-11 Chấm công thực tế**

  - Ghi nhận thực tế đi làm/nghỉ của từng nhân sự theo ngày (không chỉ
    lịch dự kiến).

  - Mỗi ngày của mỗi người gắn 1 ký hiệu chấm công (xem mục 7) làm căn
    cứ tính ngày công.

**F-12 Admin cập nhật trạng thái nghỉ**

  - Ai nghỉ thì admin là người cập nhật trạng thái (nghỉ ốm S, nghỉ
    phép, ngày lễ…) vào hệ thống.

**F-13 Admin cập nhật ngày lễ (PH)**

  - Admin tự cập nhật danh sách ngày lễ; ngày lễ được tính là ngày nghỉ
    (ký hiệu X).

## 4.6. Module Tính toán tự động

**F-14 Tính ngày làm thêm / nghỉ bù tích lũy**

  - Tự động tính số ngày làm thêm / nghỉ bù (nếu có) để phân bù vào
    tháng tiếp theo.

  - **Lưu ý:** chỉ tính theo logic nghỉ bù hiện tại; KHÔNG xử lý logic
    phép năm phức tạp (định mức/chuyển tiếp).

## 4.7. Module Báo cáo & Xuất dữ liệu

**F-15 Xuất chấm công theo tháng và theo năm**

  - Cho phép chiết xuất dữ liệu chấm công theo tháng và theo năm.

**\[ĐÃ CHỐT\]** Định dạng/layout báo cáo: chưa cần làm ngay, sẽ quyết
định sau tùy tình hình. Thiết kế phần xuất dữ liệu ở mức linh hoạt,
dễ bổ sung định dạng về sau.

# 5\. Đặc tả thuật toán xếp lịch tự động (cho Dev/AI)

Mô tả bài toán xếp lịch dạng tối ưu có ràng buộc, đủ chi tiết để lập
trình (đề xuất dùng constraint solver như OR-Tools). Mỗi nhân sự, mỗi
ngày trong tháng được gán đúng MỘT trạng thái.

## 5.1. Dữ liệu đầu vào (Input)

  - **Tập nhân sự P:** mỗi người có role ∈ {M, T, A1, A2, A3, A4}.

  - **Tập ngày D:** các ngày của tháng đang xếp, mỗi ngày biết thứ trong
    tuần (T2…CN).

  - **Tuần:** tháng được chia thành các tuần (≈4 tuần). Định nghĩa tuần
    thống nhất một cách và dùng nhất quán để áp ràng buộc nghỉ.

  - **flightPairs\[d\]:** số cặp chuyến bay của ngày d (0, 1 hoặc 2) —
    từ module nhập lịch bay (F-04).

  - **Đăng ký nghỉ đã duyệt:** danh sách (người, ngày) đã duyệt nghỉ
    (AL, CD…) và ngày lễ X.

  - **carryComp\[p\]:** số ngày nghỉ bù tồn đọng từ tháng trước của
    người p (dùng cho ưu tiên).

  - **carryStreak\[p\]:** số ngày làm việc LIÊN TỤC tính đến hết ngày
    cuối tháng trước của người p — dùng để xử lý chuỗi vắt qua 2 tháng
    (mục 5.5).

## 5.2. Biến quyết định (Output)

  - shift\[p\]\[d\] ∈ {A, D, AD, A/D, X, CD, S, AL, B, T(training), O/D}
    — trạng thái của người p ngày d.

  - Quy ước: A, D, AD, A/D, B, T, O/D tính là đi làm; X, CD, S, AL là
    nghỉ. A/D tính bằng 2 ngày công (chi tiết ký hiệu xem mục 7).

## 5.3. Ràng buộc CỨNG (bắt buộc thỏa mãn)

1.  Mỗi người mỗi ngày đúng 1 trạng thái.

2.  Mỗi tuần, mỗi người có ĐÚNG 2 ngày nghỉ (X). T7 và CN không mặc định
    là nghỉ; 2 ngày nghỉ có thể rơi vào bất kỳ ngày nào trong tuần.

3.  Không ai làm quá 5 ngày LÀM VIỆC liên tục (chuỗi ≥ 6 ngày là không
    hợp lệ). Tính chuỗi phải cộng dồn carryStreak\[p\] từ tháng trước
    (mục 5.5).

4.  Định biên ca cho nhóm cố định A1–A4 theo flightPairs\[d\]:

| **flightPairs\[d\]** | **Yêu cầu định biên trong ngày (nhóm A1–A4)** |
| -------------------- | --------------------------------------------- |
| 2 cặp                | 1 người ca A và 2 người ca D                  |
| 1 cặp                | 1 người ca A và 1 người ca D                  |
| 0 cặp                | Không cần định biên ca bay trong ngày đó      |

5.  Tôn trọng nghỉ đã duyệt và ngày lễ: các ô (người, ngày) đã duyệt
    AL/CD hoặc ngày lễ X phải giữ nguyên, không xếp ca.

6.  Thiếu người (bất đắc dĩ): cho phép 1 người làm A/D (xuyên 2 ca) để
    phủ ca trống. Người đó được +1 ngày làm việc và sinh 1 ngày nghỉ bù
    (CD) cho tháng sau.

## 5.4. Mục tiêu MỀM (tối ưu — không bắt buộc 100%)

7.  Cân bằng ca A và ca D giữa các nhân sự TRONG THÁNG: tối thiểu hóa
    chênh lệch số ca A giữa người nhiều nhất và ít nhất; tương tự cho
    ca D (ưu tiên cao nhất, đặc biệt nhóm A1–A4).

8.  Ghép 2 ngày nghỉ trong tuần thành cặp liền kề theo thứ tự: (1) T7+CN
    tốt nhất; (2) T6+T7; (3) CN+T2.

9.  Khi nhiều người cùng xin nghỉ một ngày (xung đột), ưu tiên: (a)
    người có carryComp\[p\] lớn hơn; (b) đảm bảo quyền nghỉ 2
    ngày/tuần; (c) ưu tiên ghép cặp cuối tuần.

Gợi ý cài đặt: gán trọng số cho từng mục tiêu mềm rồi cực tiểu hóa tổng
hàm phạt (weighted sum). Trọng số cân bằng A/D nên cao nhất.

## 5.5. Xử lý chuỗi ngày làm liên tục vắt qua 2 tháng

Để ràng buộc “không quá 5 ngày liên tục” vẫn đúng ở ranh giới giữa 2
tháng:

10. Khi kết thúc xếp một tháng, lưu carryStreak\[p\] = số ngày làm việc
    liên tục tính ngược từ ngày cuối tháng (nếu ngày cuối là nghỉ thì =
    0).

11. Khi xếp tháng mới, các ngày đầu tháng tính chuỗi liên tục CỘNG DỒN
    với carryStreak\[p\]. Ví dụ: đã làm 4 ngày liên tục cuối tháng
    trước thì sang tháng mới chỉ được làm tối đa 1 ngày nữa rồi phải
    nghỉ.

Ràng buộc 2 ngày nghỉ/tuần áp theo từng tuần của tháng (≈4 tuần) nên về
cơ bản đã đảm bảo nghỉ đều; quy tắc cộng dồn ở trên chỉ để chặn trường
hợp biên.

## 5.6. Khi không tìm được lời giải hợp lệ (infeasible)

12. Engine báo “không có lời giải” và chỉ rõ ngày/ràng buộc bị vi phạm
    (vd ngày X thiếu người ca D).

13. Gợi ý hướng xử lý (vd dùng A/D bất đắc dĩ theo 5.3) và CHO PHÉP
    admin chỉnh tay để hoàn thiện lịch (F-09).

14. Không tự ý phá ràng buộc cứng mà không thông báo; mọi vi phạm phải
    được admin xác nhận.

# 6\. Tổng hợp quy tắc nghiệp vụ đã chốt

  - Số lượng nhân sự: tùy việc tạo user (linh hoạt, không cố định).

  - 21 hay 22 ngày làm/tháng: không quan trọng vì tùy tháng; chỉ cần 2
    ngày nghỉ/tuần.

  - T7, CN không coi là ngày nghỉ mặc định, vẫn đi làm; mỗi tuần mỗi
    người nghỉ 2 ngày.

  - Xung đột nghỉ: xét (1) nghỉ bù tồn đọng → (2) nghỉ tuần 2 ngày → (3)
    ghép cặp cuối tuần; nhóm cố định do admin duyệt cuối.

  - Nhóm cố định (A1–A4) bắt buộc theo lịch; nhóm linh hoạt (M, T) xin
    đổi & admin duyệt, không bị bắt ép.

# 7\. Định nghĩa ký hiệu chấm công

| **Ký hiệu** | **Ý nghĩa**                                                              |
| ----------- | ------------------------------------------------------------------------ |
| A           | ARR duty (ca đến) — kết thúc trước STD 60 phút. Tính là ngày làm việc.   |
| D           | DEP duty (ca đi) — briefing trước 40 phút. Tính là ngày làm việc.        |
| A/D         | ARR và DEP duty (làm xuyên 2 ca trong ngày) — tính bằng 2 ngày làm việc. |
| AD          | Làm 2 ca trong ngày nhưng KHÔNG tính nghỉ bù (khác với A/D).             |
| X           | OFF DAY — ngày nghỉ (bao gồm ngày lễ PH).                                |
| CD          | Compensation days — ngày nghỉ bù.                                        |
| O/D         | Office duty — làm việc văn phòng.                                        |
| T           | Online / training course — đào tạo. Tính là ngày làm việc.               |
| B           | Business Trip — đi công tác. Tính là ngày làm việc; do quản lý chấm.     |
| S           | Reported SICK — báo ốm.                                                  |
| AL          | On leave — nghỉ phép.                                                    |

# 8\. Quy ước thông tin chuyến bay (FLT & STA/STD LT FRA)

  - 37 = Hà Nội – Frankfurt; 36 = chiều ngược lại.

  - 31 = Sài Gòn – Frankfurt; 30 = chiều ngược lại.

  - STA/STD LT FRA: giờ đến/đi theo giờ địa phương Frankfurt.

# 9\. Lưu ý bảo mật & tuân thủ pháp lý khi triển khai tại Đức

Triển khai tại Đức (EU) và xử lý dữ liệu nhân sự nên phải tuân thủ GDPR
(EU) và Luật bảo vệ dữ liệu liên bang Đức (BDSG).

## 9.1. Dữ liệu sức khỏe là loại đặc biệt

  - Ký hiệu S (báo ốm) là dữ liệu sức khỏe — thuộc “special category”
    theo Điều 9 GDPR. Hạn chế quyền xem (chỉ admin), không lưu lý do ốm
    chi tiết, tách quyền truy cập dữ liệu ốm khỏi dữ liệu lịch thông
    thường.

## 9.2. Quyền của hội đồng lao động (Betriebsrat)

  - Theo §87(1) No.6 BetrVG: hệ thống có khả năng giám sát hành vi/hiệu
    suất nhân viên cần có thỏa thuận với hội đồng lao động nếu doanh
    nghiệp có Betriebsrat. Đây là điểm Đức khắt khe hơn nhiều nước EU
    khác.

**\[CẦN LÀM RÕ VỚI KHÁCH\]** Doanh nghiệp khách hàng có Betriebsrat (hội
đồng lao động) không? Nếu có, cần thỏa thuận trước khi triển khai.

## 9.3. Cơ sở pháp lý & tối thiểu hóa dữ liệu

  - §26 BDSG: chỉ xử lý dữ liệu nhân viên ở mức “cần thiết” cho quan hệ
    lao động (data minimization). Có chính sách lưu trữ (retention) và
    xóa khi hết mục đích.

## 9.4. Lưu trữ dữ liệu trong EU/EEA

  - Chọn vùng (region) cloud đặt tại EU — ưu tiên Đức/Frankfurt. Tránh
    chuyển dữ liệu ra ngoài EU (đặc biệt sang Mỹ). Ký DPA (Điều 28 GDPR)
    với nhà cung cấp cloud.

## 9.5. Biện pháp kỹ thuật tối thiểu

  - Mã hóa khi truyền (HTTPS/TLS) và khi lưu (encryption at rest).

  - Phân quyền truy cập theo role; nhân viên thường chỉ xem dữ liệu của
    mình.

  - Nhật ký thao tác (audit log) cho hành động admin; sao lưu định kỳ &
    quy trình phục hồi.

  - Đáp ứng quyền của nhân viên: xem, chỉnh sửa, yêu cầu xóa dữ liệu cá
    nhân.

## 9.6. Lưu ý về AI

  - Engine xếp lịch dùng quy tắc/ràng buộc (rule-based / constraint
    solver), KHÔNG dùng AI đánh giá hiệu suất nhân viên. Từ 02/08/2026,
    EU AI Act xếp hệ thống AI giám sát/đánh giá nhân viên vào nhóm rủi
    ro cao (high-risk).

**Ghi chú:** việc tuân thủ pháp lý cuối cùng nên được khách hàng xác
nhận với pháp chế/DPO của họ.

# Phụ lục A — Tài liệu yêu cầu gốc của khách hàng (nguyên văn)

**TÀI LIỆU TỔNG HỢP YÊU CẦU**

*Phần mềm Tự động xếp lịch & Chấm công nhân sự*

Cập nhật sau buổi họp chốt yêu cầu — 06/2026

# 1\. Bối cảnh

Phần mềm phân lịch làm việc (xếp ca) và chấm công cho nhân sự, thay cho
cách phân ca thủ công bằng bảng in hiện tại (mẫu "WR JUN26").

  - Hàng tháng, căn cứ vào lịch bay để lập danh sách các chuyến bay (cột
    FLT), sau đó phân bổ nhân lực cho từng chuyến.

  - Bản chất phần mềm: **tự động xếp lịch** — đây là chức năng chính,
    không chỉ là một phần mềm chấm công thông thường.

# 2\. Yêu cầu chung

  - Đơn giản, dễ thao tác.

  - Cài đặt trên 10 máy tính để mỗi nhân sự tự đăng ký trên máy của
    mình.

  - **Hệ điều hành:** Windows.

  - **Ngôn ngữ:** Tiếng Anh (ưu tiên); có thêm Tiếng Việt thì càng tốt.

  - **Nơi triển khai:** tại Đức (Frankfurt).

  - Cho phép chiết xuất dữ liệu chấm công theo tháng và theo năm.

# 3\. Nhân sự, phân role & phân quyền

Tổng cộng 09 nhân sự (số lượng user có thể thay đổi tùy theo việc tạo
user trên hệ thống). Phân role như sau:

| **STT** | **Tên** | **Role** | **Tính chất**      |
| ------- | ------- | -------- | ------------------ |
| 1       | Toàn    | M        | Admin + Linh hoạt  |
| 2       | Chi     | M        | Admin + Linh hoạt  |
| 3       | Vũ      | T        | Linh hoạt          |
| 4       | Trường  | T        | Linh hoạt          |
| 9       | Tùng    | T        | Linh hoạt          |
| 5       | Agne    | A1       | Bắt buộc (cố định) |
| 6       | Joachim | A2       | Bắt buộc (cố định) |
| 7       | Long    | A3       | Bắt buộc (cố định) |
| 8       | Thomas  | A4       | Bắt buộc (cố định) |

  - **M (Admin + Linh hoạt):** có quyền quản trị, phê duyệt các vấn đề
    phát sinh; lịch làm linh hoạt.

  - **T (Linh hoạt):** được gửi xin đổi lịch, admin phê duyệt, không bị
    bắt ép.

  - **A1–A4 (Bắt buộc / cố định):** phải tuân theo lịch hệ thống xếp; có
    thể xin đổi nhưng nếu admin không duyệt thì không được đổi. Đây là
    nhóm cần phân lịch chặt chẽ nhất.

# 4\. Nguyên tắc phân lịch & chấm công

  - Đảm bảo mỗi tuần mỗi người có 2 ngày nghỉ (nghỉ phép tuần). Số ngày
    làm việc trong tháng (\~21–22) không cố định, tùy theo tháng.

  - **Đặc thù cuối tuần:** Thứ 7 và Chủ nhật KHÔNG được coi là ngày nghỉ
    mặc định — nhân sự vẫn đi làm bình thường. Mỗi người được nghỉ 2
    ngày/tuần và có thể rơi vào bất kỳ ngày nào.

  - Đảm bảo cân bằng số ca A, ca D giữa các nhân sự (đặc biệt nhóm cố
    định A1–A4).

  - **Giới hạn ngày làm liên tục:** không nhân sự nào được làm việc quá
    5 ngày liên tục (từ 6 ngày liên tục trở lên là không hợp lệ).

**Quy tắc riêng cho nhóm cố định (A1–A4):**

Ngày có 2 cặp chuyến bay: bắt buộc 1 người ca A và 2 người ca D.

Ngày chỉ có 1 cặp chuyến bay: 1 người ca A và 1 người ca D.

Trường hợp bất đắc dĩ: có thể phân 1 người làm A/D (làm xuyên 2 ca),
nhưng người đó được tính thêm 1 ngày làm việc để nghỉ bù vào tháng tiếp
theo.

# 5\. Quy tắc ưu tiên khi đăng ký & xếp lịch nghỉ

**Thứ tự ưu tiên khi xét duyệt / xử lý xung đột đăng ký nghỉ:**

  - **Quyền nghỉ bù:** ưu tiên người có tổng số ngày nghỉ bù tồn đọng từ
    tháng trước (tích lũy nhiều hơn được ưu tiên trước).

  - **Quyền nghỉ tuần:** đảm bảo mỗi người đủ 2 ngày nghỉ/tuần.

**Ưu tiên xếp 2 ngày nghỉ thành cặp ngày liền kề, theo thứ tự ưu tiên:**

  - T7 + CN — tốt nhất (ưu tiên tuyệt đối).

  - T6 + T7.

  - CN + T2.

# 6\. Quy tắc nghỉ ốm (S)

  - Khi có người nghỉ ốm, bắt buộc phải có người làm A/D để bù vào ca
    trống.

  - Người vừa nghỉ ốm sẽ được ưu tiên (bắt buộc) làm A/D nếu sau đó có
    người khác nghỉ ốm.

# 7\. Quy trình đăng ký nghỉ hàng tháng

  - Ngày 5 đầu tháng: nhân sự được đăng ký ngày nghỉ theo nhu cầu.

  - Ngày 20: hệ thống đóng đăng ký và phân lịch trên cơ sở cân đối nhu
    cầu, đồng thời đảm bảo tuân thủ các nguyên tắc & quy tắc ưu tiên
    nêu trên.

**Đăng ký nghỉ gồm 2 phần:**

Nghỉ dưới 5 ngày liên tục: đăng ký hàng tháng.

Nghỉ liên tục từ 5 ngày trở lên: đăng ký vào phần nghỉ phép năm; thời
gian đăng ký mở từ tháng 1 đến tháng 12 của năm trước.

# 8\. Tính toán tự động

  - Tự động tính số ngày phép còn lại của từng nhân sự.

  - Tự động tính số ngày làm thêm / ngày nghỉ bù tích lũy (nếu có) để
    phân bù vào tháng tiếp theo.

# 9\. Định nghĩa ký hiệu chấm công

| **Ký hiệu** | **Ý nghĩa**                                                              |
| ----------- | ------------------------------------------------------------------------ |
| A           | ARR duty (ca đến) — kết thúc trước STD 60 phút. Tính là ngày làm việc.   |
| D           | DEP duty (ca đi) — briefing trước 40 phút. Tính là ngày làm việc.        |
| A/D         | ARR và DEP duty (làm xuyên 2 ca trong ngày) — tính bằng 2 ngày làm việc. |
| AD          | Làm 2 ca trong ngày nhưng KHÔNG tính nghỉ bù (khác với A/D).             |
| X           | OFF DAY — ngày nghỉ (bao gồm ngày lễ PH).                                |
| CD          | Compensation days — ngày nghỉ bù.                                        |
| O/D         | Office duty — làm việc văn phòng.                                        |
| T           | Online / training course — đào tạo. Tính là ngày làm việc.               |
| B           | Business Trip — đi công tác. Tính là ngày làm việc; do quản lý chấm.     |
| S           | Reported SICK — báo ốm.                                                  |
| AL          | On leave — nghỉ phép.                                                    |

# 10\. Thông tin chuyến bay (cột FLT & STA/STD LT FRA)

Hàng tháng nhập danh sách chuyến bay làm căn cứ phân ca. Quy ước số
hiệu:

  - 37 = Hà Nội – Frankfurt; 36 = chiều ngược lại.

  - 31 = Sài Gòn – Frankfurt; 30 = chiều ngược lại.

  - **STA/STD LT FRA:** giờ đến/đi theo giờ địa phương Frankfurt.

# 11\. Các nội dung đã chốt trong buổi họp

  - Số lượng nhân sự cuối cùng: 9 hay 10 người.

> **→ Đã chốt:** tùy theo việc tạo user trên hệ thống (số lượng user
> linh hoạt, không cố định).

  - Mâu thuẫn định mức: "22 ngày làm việc/tháng" so với "TTL 21 WORKING
    DAYS" trên bảng mẫu.

> **→ Đã chốt:** con số 21 hay 22 không quan trọng vì tùy theo tháng;
> chỉ cần đảm bảo mỗi tuần có 2 ngày nghỉ.

  - Định nghĩa "số ca A, ca D và ngày nghỉ cuối tuần giống nhau".

> **→ Đã chốt:** Thứ 7, Chủ nhật KHÔNG được coi là ngày nghỉ mà vẫn đi
> làm bình thường; nhưng mỗi tuần mỗi người được nghỉ 2 ngày (nghỉ phép
> tuần). Cần cân bằng số ca A, ca D giữa các nhân sự.

  - Cách xử lý khi đăng ký nghỉ của nhiều người bị xung đột.

> **→ Đã chốt:** xét theo thứ tự ưu tiên: (1) quyền nghỉ bù tồn đọng
> tháng trước, (2) quyền nghỉ tuần 2 ngày/tuần, (3) ưu tiên ghép cặp
> cuối tuần (T7+CN tốt nhất). Với nhóm cố định, admin là người phê
> duyệt cuối cùng.

  - Phạm vi khác biệt giữa nhóm linh hoạt và nhóm cố định.

> **→ Đã chốt:** nhóm cố định (A1–A4) bắt buộc theo lịch; có thể xin
> duyệt đổi nhưng admin không cho thì không được đổi. Nhóm linh hoạt
> (M, T) gửi xin đổi và admin phê duyệt, không bị bắt ép.
