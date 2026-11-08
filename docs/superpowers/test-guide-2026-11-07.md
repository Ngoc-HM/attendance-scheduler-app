# Hướng dẫn test sau đợt sửa 2026-11

Đợt sửa 2026-11-07 đã được gộp vào `main` ngày 2026-11-08 (merge commit `4ded62e`, nhánh `fix/2026-11-remediation` đã xoá). Đợt sửa thứ hai theo bản rà soát 2026-11-08 nằm trên nhánh `fix/2026-11-review-2`; các thay đổi mới để bấm thử nằm ở **mục 6**.

## 1. Chạy

**Cảnh báo quan trọng về cơ sở dữ liệu**
- `backend/.env` đang trỏ tới PostgreSQL thật (qua Tailscale) và backend chạy `ENVIRONMENT=dev`. Có hai migration mới: **0008** (thêm cột `users.annual_leave_quota`, bỏ cột `annual_leave_balance` chưa dùng) và **0009** (xoá chuyến bay trùng cùng ngày + số FLT, giữ dòng có id nhỏ nhất, rồi thêm ràng buộc duy nhất). **Phải chạy migration trước khi bật backend:**

```bash
make install
```

```bash
cd backend && .venv/bin/alembic upgrade head
```

- `AUTO_CREATE_TABLES` **không** cứu được: nó chỉ tạo bảng cho một DB hoàn toàn mới, và bị bỏ qua (có dòng cảnh báo trong log) khi DB đã có bảng `alembic_version`. Nó cũng không bao giờ thêm cột hay ràng buộc vào bảng đã có.
- Nếu muốn test sạch trên máy, đổi `DATABASE_URL` trong `backend/.env` sang SQLite (`sqlite:///./dev.db`) rồi chạy bình thường; với file DB mới, bảng được tạo tự động.

**Khởi động cả backend và app**

```bash
make dev
```

Backend ở `http://localhost:8035`, docs API ở `/docs` (chỉ có ở `ENVIRONMENT=dev`). Log của backend (bootstrap, autorun) giờ được in ra terminal ở mức INFO.

## 2. Tài khoản

- **Admin (role M):** `FIRST_ADMIN_USERNAME` / `FIRST_ADMIN_PASSWORD` trong `backend/.env` (mặc định dev xem `backend/.env.example`). Ở `ENVIRONMENT=dev` mật khẩu admin được đặt lại về giá trị đó mỗi lần backend khởi động (giữ nguyên theo ý chủ dự án). Tài khoản admin seed chỉ được tạo khi chưa có admin nào đang hoạt động; nếu đã cố ý xoá nó thì nó không tự sinh lại.
- **Nhân viên demo:** tạo 10 tài khoản `nguyenvana` … `nguyenvanj` (a, b = T; c, d = F; e–j = A, xem `backend/app/services/demo_user_seed.py`) bằng:

```bash
cd backend && .venv/bin/python scripts/seed_demo_users.py
```

  Script **hỏi mật khẩu** (gõ ẩn, hỏi hai lần); không còn mật khẩu mặc định. Muốn chạy không hỏi thì thêm `--password <mật-khẩu>` (mật khẩu sẽ nằm trong lịch sử shell). Script **từ chối chạy** nếu DB không phải local (SQLite/localhost) — DB qua Tailscale cũng bị coi là không local — trừ khi thêm `--allow-non-dev` (xem mục 4).
- Hoặc tự tạo user trong màn Users của admin (có ô định mức phép năm), hoặc **tự đăng ký** ở màn Register rồi admin duyệt và **chọn role lúc duyệt**.

## 3. Các quy tắc đã sửa và cách kiểm tra

| # | Quy tắc | Cách test | Kết quả mong đợi |
|---|---|---|---|
| 1 | Tạo lại lịch bị chặn khi đã publish hoặc đã chỉnh tay | Admin: Generate → Publish → Generate lại | Hộp xác nhận "lịch đã publish/chỉnh tay, tạo lại sẽ xoá chỉnh tay và về nháp". Đồng ý mới tạo lại |
| 2 | Tự đăng ký không chọn được role | Màn Register: không còn ô role. Đăng ký xong → admin vào Users → Approve | Dialog duyệt bắt chọn role (M/T/A/F). Tài khoản đã active thì không duyệt lại được |
| 3 | Nhãn nghỉ phải khớp số ngày | Nhân viên đăng ký nghỉ tháng 10 ngày, hoặc nghỉ năm 3 ngày | Bị chặn ngay trên app, backend cũng trả 422 |
| 4 | Sửa lịch đã publish đồng bộ sang chấm công | Publish → admin sửa 1 ô lịch → mở Attendance | Ô chấm công seed đổi theo; ô admin đã ghi tay giữ nguyên |
| 5 | Duyệt / huỷ nghỉ cập nhật thẳng lịch | Generate tháng X → nhân viên xin nghỉ 3 ngày trong tháng X → admin duyệt / huỷ | Ô lịch thành AL (ngày X nghỉ tuần vẫn giữ X); huỷ thì ô đang AL về X, ô admin đã sửa giữ nguyên |
| 6 | Nghỉ bù đi làm ngày lễ, mọi role | Thêm ngày lễ ≥ 06/11/2026 → ghi chấm công A/AD/O/D đúng ngày đó → Generate tháng sau | Người đó được 1 ô CD tháng sau (lễ trước 06/11/2026 không tính; sửa mốc bằng `HOLIDAY_COMP_EFFECTIVE_FROM`) |
| 7 | Định mức phép năm | Users: tạo user có định mức, hoặc "Edit leave quota"; màn Leaves nhân viên | Thẻ "Phép năm còn lại" = định mức − ngày nghỉ đã duyệt trong năm; duyệt quá định mức chỉ cảnh báo |
| 8 | Cửa sổ đăng ký nghỉ | Màn Leaves hiển thị đúng trạng thái mở/đóng theo ngày 1–20 tháng trước (ở `ENVIRONMENT=dev` luôn mở) | Chuỗi hướng dẫn nêu đúng ngày đóng; không còn chữ "development" |
| 9 | Autorun | Xem log backend lúc 00:05 (giờ Berlin) ngày 21, hoặc khởi động lại backend vào ngày 21 trở đi khi tháng sau chưa có lịch | Log in "Autorun: generated draft …" và có nháp tháng sau; ngày 20 không chạy. Máy tắt lúc 00:05 thì lần khởi động sau (hoặc lần kiểm tra 00:05 hôm sau) sẽ chạy bù. Tháng sau chưa có chuyến bay thì log cảnh báo |
| 10 | Nhân viên xin đổi ca | Đăng nhập nhân viên → bấm vào ô của chính mình trên lịch đã publish | Dialog xin đổi ca; chỉ cho chọn mã thường (T/F: AD, X; A: A, D, X; M: O/D, X); danh sách đơn của mình hiện dưới lịch; admin duyệt ở màn Schedule |
| 11 | Nhân viên xem chấm công của mình | Đăng nhập nhân viên → mục "Chấm công của tôi" | Chỉ thấy của mình, không có nút admin |
| 12 | Tên trên lịch cho nhân viên | Đăng nhập nhân viên → Schedule | Hàng hiển thị mã (A1, T2...) thay vì "User 7" |
| 13 | Khôi phục phiên | Đăng nhập, tắt app, mở lại | Vào thẳng Schedule; nếu backend tắt thì giữ token và báo "không kết nối được" |
| 14 | Hộp sửa ô lịch của admin | Admin bấm ô lịch | Không còn mã S, danh sách mã theo đúng role |
| 15 | Nút Generate/Publish | Đăng nhập nhân viên | Không thấy 2 nút này |

## 4. Script và cảnh báo vận hành

- `backend/scripts/reset_all_passwords.py` và `seed_demo_users.py` hỏi mật khẩu (gõ ẩn) khi không truyền `--password`, và từ chối chạy nếu DB không local trừ khi `--allow-non-dev`.
- Trước khi deploy lên DB thật: kiểm tra có tài khoản `status='pending' AND role='M'` (đăng ký từ trước) không; nên đổi về T.
- Giá trị định mức phép năm mặc định 30 ngày (`ANNUAL_LEAVE_DEFAULT_DAYS`) là tạm, chờ khách chốt. Mọi user có sẵn sẽ nhận 30 sau migration; sửa từng người bằng "Edit leave quota".
- **Autorun trên DB dùng chung:** từ ngày 21 đến hết tháng, **mỗi lần bật backend** (và lần kiểm tra 00:05 mỗi ngày) sẽ tạo nháp tháng sau nếu tháng đó chưa có lịch. Nó không bao giờ ghi đè nháp hay lịch đã publish. Nên nhập chuyến bay tháng sau trước ngày 21; nếu nhiều máy cùng chạy backend vào DB này thì chỉ để `AUTORUN_ENABLED=true` trên một máy.
- Golden test Flutter chỉ khớp trên macOS. CI chạy golden ở job riêng trên macOS 15; job Ubuntu chạy `flutter test --exclude-tags golden`; bản build Windows không còn chờ golden. Trên máy: `flutter test --tags golden` (macOS) và `flutter test --exclude-tags golden`.
- Thư viện đã được khoá phiên bản: `backend/requirements.lock` (CI và Docker cài với `-c requirements.lock`) và `attendance_scheduler_app/pubspec.lock`.
- Chế độ `ENVIRONMENT=staging` bị chặn khởi động giống hệt `prod` (mật khẩu/secret mặc định, DB SQLite hoặc URL mặc định, CORS `*`, `AUTO_CREATE_TABLES=true`, thời hạn lưu trữ dưới 24 tháng).

## 5. Những điều vẫn chờ khách chốt

Xem mục "Open questions" trong `docs/design-decisions.md`: ưu tiên cặp nghỉ cuối tuần, định biên "đúng số" hay "tối thiểu" và người nhóm A thừa làm gì, số ngày phép năm thật, hội đồng lao động, và các ghi chú nghiệp vụ nhỏ (ví dụ: CD bị AL đè khi duyệt nghỉ, T/B đúng ngày lễ cũng được nghỉ bù, đơn đổi ca đang chờ với mã AL/CD cũ sẽ bị từ chối khi duyệt). Từ 2026-11-08 có thêm: nghỉ phép nằm cạnh ngày nghỉ tuần không còn bị tính là "nghỉ liền quá dài" (tạm quyết, #41), cách tính CD trước mốc 06/11/2026 (tạm quyết, #43), không phạt làm ngày lễ (R5), và ca đêm với chấm giờ (check-out sau nửa đêm hiện trả 409).

## 6. Bổ sung 2026-11-08 (đợt sửa theo rà soát 2026-11-08)

Chạy `alembic upgrade head` trước (mục 1). Số liệu: backend 463 test, Flutter 119 test (gồm 3 golden).

| # | Thay đổi | Cách test | Kết quả mong đợi |
|---|---|---|---|
| 16 | Bảng vi phạm trước khi Publish | Admin: tạo một tháng nháp có vi phạm (ví dụ sửa tay để một người làm 6 ngày liền, hoặc tháng có 2 cặp chuyến/ngày mà ít người role A) → xem màn Schedule → bấm Publish | Dưới lưới có khung "N vi phạm quy tắc trong tháng này. Hãy xem lại trước khi công bố."; bấm Publish hiện hộp "Công bố khi còn vi phạm quy tắc?" liệt kê từng vi phạm (ngày hiện một lần), nút "Vẫn công bố". Nếu không kiểm tra được thì hộp ghi "Chưa kiểm tra được quy tắc". Tháng sạch thì publish thẳng |
| 17 | Chuyển sang tháng chưa có lịch | Admin đang xem tháng có lịch → chuyển sang tháng chưa tạo | Lưới trống, không còn lưới tháng trước; không có nút Publish (nút bị ẩn chứ không mờ); Publish/sửa ô chỉ tác động tháng đang hiện |
| 18 | Báo ốm tự gán người thay | Admin → Attendance → ghi S cho một người role A có ô A hoặc D hôm đó | Lưu được (trước đây luôn lỗi 422); một đồng nghiệp **đang hoạt động** được gán A/D thay; ô chấm công của người thay không có ghi chú; lý do chọn người thay chỉ nằm trong thông báo trả về cho admin, không lưu vào ô |
| 19 | Hộp ghi chấm công | Admin mở hộp ghi chấm công | Danh sách người chỉ gồm người đang hoạt động; mã theo đúng role của người đó cộng thêm S |
| 20 | Đăng xuất xoá dữ liệu | Nhân viên 1 đăng nhập, mở Leaves, Attendance, Schedule → đăng xuất → nhân viên 2 đăng nhập trên cùng app | Nhân viên 2 chỉ thấy dữ liệu của mình, không thấy đơn nghỉ hay chấm công của nhân viên 1 |
| 21 | Tài khoản bị khoá giữa phiên | Nhân viên đăng nhập → admin (máy khác) đổi trạng thái người đó sang disabled → nhân viên bấm một thao tác | App báo "Tài khoản của bạn không còn hoạt động…" và về màn đăng nhập |
| 22 | Lỗi quản lý user hiện đúng | Admin: tạo user trùng username; hạ role admin cuối cùng; nhập định mức sai | Thông báo nêu đúng lý do từ backend, không còn "Could not load users." chung chung |
| 23 | Bộ chọn trên màn Reports | Admin → Reports | Có ô Năm (năm hiện tại và 4 năm trước, theo đồng hồ máy), Tháng hoặc "Cả năm" ("Full year"), Định dạng (CSV/XLSX) ngay trên trang; "Cả năm" xuất file cả năm (không còn lỗi month=0); nhãn không còn hiện key thô |
| 24 | Chống công thức trong báo cáo | Tự đăng ký một tài khoản tên `=HYPERLINK("http://example.com","bam")` → admin duyệt → ghi chấm công cho người đó trong tháng → xuất CSV và XLSX, mở bằng Excel/LibreOffice | Ô tên hiện nguyên văn `'=HYPERLINK(...)`, không thành liên kết; số âm như `-1` vẫn là số. Tài khoản pending không có trong báo cáo; tài khoản disabled chỉ có khi có chấm công trong kỳ |
| 25 | Chuyến bay trùng dòng | Tạo file Excel có 2 dòng cùng ngày + cùng số FLT (khác giờ) → Import → sau đó sửa tay chuyến đó → Import lại file | Import thành công, chỉ lưu 1 chặng (lấy **dòng cuối**); log backend có cảnh báo dòng trùng (app không báo); sửa tay và import lại đều được (trước đây 500 rồi 422 mãi) |
| 26 | Ô bị khoá khi xin đổi ca | Nhân viên bấm ô AL hoặc CD của mình → xin đổi mã | Bị từ chối: "Không thể yêu cầu đổi ngày nghỉ phép, nghỉ bù, ngày ốm hoặc ngày do admin gán…". Đơn đổi ca đang chờ mà ô sau đó thành AL/CD: admin duyệt thì bị từ chối (nên bấm Reject) |
| 27 | Duyệt đổi ca | Nhân viên xin hoán đổi với đồng nghiệp → admin mở bảng duyệt | Bảng hiện mã người xin và người được hoán đổi; chỉ chọn được đồng nghiệp cùng role đang hoạt động; duyệt xong có cảnh báo quy tắc (nếu có) và lưới tự tải lại. (Ở backend, duyệt cùng một đơn hai lần trả 409, ô chỉ bị đổi một lần) |
| 28 | Giới hạn tháng/năm (422) | Mở `http://localhost:8035/docs` → Authorize bằng tài khoản nhân viên → `GET /api/v1/attendance/me` với `month=13` (hoặc `year=0`) | Trả **422**, không còn 500. Tương tự với các endpoint báo cáo, lịch, chuyến bay… (năm hợp lệ 2000–2100, tháng 1–12) |
| 29 | Màn Leaves tải lại | Mở Leaves → sang màn khác → quay lại; hoặc bấm nút làm mới | Danh sách tải lại mỗi lần mở và khi bấm làm mới; chọn ngày bắt đầu sau ngày kết thúc thì ngày kết thúc tự đặt lại |
| 30 | Nghỉ phép cạnh ngày nghỉ tuần | Duyệt nghỉ tháng 5 ngày (ví dụ thứ Ba–thứ Bảy) **trước** khi Generate → Generate | Không có vi phạm "nghỉ liền quá 5 ngày" cho người đó, kể cả khi hai ngày X của tuần nằm sát kỳ nghỉ (tạm quyết #41, chờ khách xác nhận). Một chuỗi chỉ gồm X/CD dài hơn 5 ngày vẫn bị báo |
| 31 | Tạo lại tháng đã publish | Publish tháng → Generate lại (đồng ý tạo lại) → nhân viên mở "Chấm công của tôi" tháng đó | Nhân viên không thấy các ô chấm công seed của tháng đó cho tới khi admin publish lại; ô admin ghi tay và ngày ốm của chính mình vẫn thấy |
| 32 | Trỏ app sang server khác | Build/chạy app với `--dart-define=API_BASE_URL=http://<máy-chủ>:8035/api/v1` | App dùng địa chỉ này dù file `.env` đóng gói vẫn là localhost |
