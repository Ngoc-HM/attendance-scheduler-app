# Hướng dẫn test sau đợt sửa 2026-11

Đợt sửa đã được gộp vào `main` ngày 2026-11-08 (merge commit `4ded62e`, nhánh `fix/2026-11-remediation` đã xoá). `main` cục bộ đi trước `origin/main`; chưa push.

## 1. Chạy

**Cảnh báo quan trọng về cơ sở dữ liệu**
- `backend/.env` đang trỏ tới PostgreSQL thật (qua Tailscale). Đợt sửa này có **migration 0008** (thêm cột `users.annual_leave_quota`, bỏ cột `annual_leave_balance` chưa dùng). `AUTO_CREATE_TABLES` **không** thêm cột vào bảng đã có, nên **phải chạy migration trước khi bật backend**, nếu không API user/leave sẽ lỗi:

```bash
make install
```

```bash
cd backend && .venv/bin/alembic upgrade head
```

- Nếu muốn test sạch trên máy, đổi `DATABASE_URL` trong `backend/.env` sang SQLite (`sqlite:///./dev.db`) rồi chạy bình thường; bảng được tạo tự động.

**Khởi động cả backend và app**

```bash
make dev
```

Backend ở `http://localhost:8035`, docs API ở `/docs`.

## 2. Tài khoản

- **Admin (role M):** `FIRST_ADMIN_USERNAME` / `FIRST_ADMIN_PASSWORD` trong `backend/.env` (mặc định dev xem `backend/.env.example`). Ở `ENVIRONMENT=dev` mật khẩu admin được đặt lại về giá trị đó mỗi lần backend khởi động.
- **Nhân viên demo:** tạo 10 tài khoản `nguyenvana` … `nguyenvanj` (a, b = T; c, d = F; e–j = A, xem `backend/app/services/demo_user_seed.py`) bằng:

```bash
cd backend && .venv/bin/python scripts/seed_demo_users.py --password <mật-khẩu-bạn-chọn>
```

  Không truyền `--password` thì dùng mặc định ghi trong script. Script **từ chối chạy** nếu DB không phải local (SQLite/localhost) trừ khi thêm `--allow-non-dev` (xem mục 4).
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
| 9 | Autorun | Xem log backend lúc 00:05 (giờ Berlin) ngày 21 | Sinh nháp tháng sau; ngày 20 không chạy |
| 10 | Nhân viên xin đổi ca | Đăng nhập nhân viên → bấm vào ô của chính mình trên lịch đã publish | Dialog xin đổi ca; chỉ cho chọn mã thường (T/F: AD, X; A: A, D, X; M: O/D, X); danh sách đơn của mình hiện dưới lịch; admin duyệt ở màn Schedule |
| 11 | Nhân viên xem chấm công của mình | Đăng nhập nhân viên → mục "Chấm công của tôi" | Chỉ thấy của mình, không có nút admin |
| 12 | Tên trên lịch cho nhân viên | Đăng nhập nhân viên → Schedule | Hàng hiển thị mã (A1, T2...) thay vì "User 7" |
| 13 | Khôi phục phiên | Đăng nhập, tắt app, mở lại | Vào thẳng Schedule; nếu backend tắt thì giữ token và báo "không kết nối được" |
| 14 | Hộp sửa ô lịch của admin | Admin bấm ô lịch | Không còn mã S, danh sách mã theo đúng role |
| 15 | Nút Generate/Publish | Đăng nhập nhân viên | Không thấy 2 nút này |

## 4. Script và cảnh báo vận hành

- `backend/scripts/reset_all_passwords.py` giờ **bắt buộc** `--password`, và từ chối chạy nếu DB không local trừ khi `--allow-non-dev`. Tương tự `seed_demo_users.py`.
- Trước khi deploy lên DB thật: kiểm tra có tài khoản `status='pending' AND role='M'` (đăng ký từ trước) không; nên đổi về T.
- Giá trị định mức phép năm mặc định 30 ngày (`ANNUAL_LEAVE_DEFAULT_DAYS`) là tạm, chờ khách chốt. Mọi user có sẵn sẽ nhận 30 sau migration; sửa từng người bằng "Edit leave quota".
- Golden test Flutter được render trên macOS; CI Ubuntu chưa chạy với bộ ảnh mới. Nếu push lên GitHub và job Flutter đỏ ở golden thì cập nhật ảnh trên Ubuntu.

## 5. Những điều vẫn chờ khách chốt

Xem mục "Open questions" trong `docs/design-decisions.md`: ưu tiên cặp nghỉ cuối tuần, định biên "đúng số" hay "tối thiểu" và người nhóm A thừa làm gì, số ngày phép năm thật, hội đồng lao động, và các ghi chú nghiệp vụ nhỏ (ví dụ: CD bị AL đè khi duyệt nghỉ, T/B đúng ngày lễ cũng được nghỉ bù, đơn đổi ca đang chờ với mã AL/CD cũ sẽ bị từ chối khi duyệt).
