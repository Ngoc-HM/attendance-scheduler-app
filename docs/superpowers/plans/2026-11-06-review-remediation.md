# Review Remediation 2026-11 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Đưa code lên trạng thái thoả mãn spec khách + quyết định owner 2026-11-06: sửa 10 lỗi backend, 2 thay đổi nghiệp vụ (lễ → nghỉ bù mọi role, phép năm còn lại), 11 điểm Flutter, và làm tài liệu đúng với code.

**Architecture:** Backend giữ kiến trúc endpoints → services → models, engine CP-SAT luôn-khả-thi với slack. Mọi quy tắc mới phải có mặt ở **4 chỗ**: engine (`scheduler/`), recheck sau chỉnh tay (`schedule_violation_checker`), self-arrange, và lịch sử carry (`schedule_history`). Flutter giữ feature-first, gọi API qua `core/constants/api_endpoints.dart`, chuỗi qua `AppLocalizations` en + vi.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2, Alembic, OR-Tools CP-SAT, pytest (SQLite); Flutter 3.44.9, Riverpod, go_router, Dio.

**Spec:** `docs/superpowers/specs/2026-11-06-review-remediation-spec.md`

## Global Constraints

- Backend chạy bằng venv tạm (máy Ngọc không có `backend/.venv`): `python3 -m venv /tmp/asa-venv && /tmp/asa-venv/bin/pip install -r backend/requirements-dev.txt`. Dưới đây `PY=/tmp/asa-venv/bin/python`.
- **Không bao giờ** chạy test/script với `backend/.env` (trỏ Postgres thật). pytest tự set `DATABASE_URL` SQLite trong `tests/conftest.py`.
- Flutter: `FLUTTER=~/develop/flutter/bin/flutter`, chạy từ `attendance_scheduler_app/`.
- Mọi key i18n mới có cả `en` và `vi` (backend `app/core/i18n.py`, Flutter `lib/i18n/app_localizations.dart`).
- Mọi mutation của admin được audit (`audit_service.record`). Mã `S` không bao giờ vào lịch kế hoạch.
- File code < 200 dòng khi có thể; commit theo `docs/code-standards.md` (conventional commit, **không** ghi tham chiếu AI).
- Trước khi sửa code, chạy test mục tiêu để thấy FAIL; sau khi sửa, chạy lại thấy PASS; cuối task chạy cả suite liên quan.

## Review Focus

1. Duyệt nghỉ trải 2 tháng mà chỉ 1 tháng đã có lịch → cập nhật tháng có lịch, cảnh báo cho tháng kia. Test ở Task 5.
2. Huỷ nghỉ trên tháng đã publish mà ô chấm công đã bị admin sửa tay (`recorded_by` khác null) → ô kế hoạch đổi, ô thực tế giữ nguyên. Test ở Task 4.
3. Self-arrange chuyển X lên ngày đang AL hoặc CD → bị từ chối (ô khoá, `selfarrange.cell_locked`). Test ở Task 7.
4. Ngày lễ mà người đó nghỉ X → không có CD; làm A/D đúng ngày lễ → +2. Test ở Task 7.
5. Tạo lại lịch có `force=true` trên tháng đã publish → về draft, nhân viên mất quyền xem tới khi publish lại; UI phải nói rõ. Test ở Task 1.

---

### Task 0: Chốt baseline

**Files:** không sửa code.

- [ ] **Step 1: Hỏi owner cho phép commit working tree hiện tại** (92 file). Nếu đồng ý:

```bash
git add -A && git commit -m "chore: checkpoint working tree before 2026-11 remediation"
```

- [ ] **Step 2: Dựng venv tạm, ghi baseline**

Run: `cd backend && $PY -m ruff check app tests && $PY -m mypy app && $PY -m pytest -q`
Expected: ruff 0 lỗi, mypy "no issues", pytest `188 passed`.

- [ ] **Step 3: Baseline Flutter**

Run: `cd attendance_scheduler_app && $FLUTTER analyze && $FLUTTER test`
Expected: analyze "No issues"; test `15 passed, 3 failed` (3 golden, sẽ cập nhật ở Task 15).

---

### Task 1: Chặn tạo lại lịch khi đã publish hoặc đã chỉnh tay (B1)

**Files:**
- Modify: `backend/app/services/schedule_service.py:71-118`
- Modify: `backend/app/core/i18n.py` (2 key đã có: `schedule.published_locked`, `schedule.has_overrides`)
- Test: `backend/tests/test_schedule_service.py`
- Modify (Flutter): `attendance_scheduler_app/lib/features/schedule/presentation/pages/schedule_page.dart:297` (`_onGenerate`), `lib/core/network/api_exception.dart`, `lib/i18n/app_localizations.dart`

**Interfaces:**
- Produces: `schedule_service.generate(db, year, month, force=False)` → raise `HTTPException(409, t("schedule.published_locked"))` khi `existing.status is ScheduleStatus.published and not force`; raise `HTTPException(409, t("schedule.has_overrides"))` khi có `assignment.is_manual_override` và `not force`. Với `force=True` xoá ô, về `draft` như hiện nay.
- Flutter `ApiException.statusCode: int?` (thêm nếu chưa có).

- [ ] **Step 1: Viết test fail**

```python
def test_regenerate_published_requires_force(client):
    # 4 user A, generate → publish → override 1 ô
    r = client.post(f"{V}/schedules/generate", json={"year": 2026, "month": 12}, headers=admin)
    assert r.status_code == 409 and "force" in r.json()["detail"]
    r = client.post(f"{V}/schedules/generate", json={"year": 2026, "month": 12, "force": True}, headers=admin)
    assert r.status_code == 200 and r.json()["schedule"]["status"] == "draft"

def test_regenerate_with_overrides_requires_force(client):
    # draft + override → 409 has_overrides; force → 200
```

- [ ] **Step 2:** Run `cd backend && $PY -m pytest tests/test_schedule_service.py -q` → 2 test mới FAIL (200 thay vì 409).
- [ ] **Step 3: Sửa `generate`**: thay khối "Testing mode" (dòng 78-81) bằng 2 guard trên, trước khi gọi engine.
- [ ] **Step 4:** Run lại → PASS, kể cả `test_regenerate_with_force_replaces_cells`.
- [ ] **Step 5: Flutter**: trong `_onGenerate`, bắt `ApiException` có `statusCode == 409` → hiện hộp xác nhận (tiêu đề `regenerateConfirmTitle`, nội dung `regenerateConfirmBody`: "Lịch đã publish hoặc đã chỉnh tay. Tạo lại sẽ xoá chỉnh tay và đưa lịch về nháp." en/vi) → nếu đồng ý gọi `generate(..., force: true)`.
- [ ] **Step 6:** Run `$FLUTTER analyze` → No issues.
- [ ] **Step 7: Commit** `fix(schedule): regenerate requires force when published or manually edited`

---

### Task 2: Tự đăng ký không được chọn role; admin gán role khi duyệt (B2, F-03)

**Files:**
- Modify: `backend/app/schemas/user.py`, `backend/app/services/user_service.py:99-115`, `backend/app/api/v1/endpoints/auth.py:25-38`
- Test: `backend/tests/test_auth_users.py`
- Modify (Flutter): `lib/features/auth/presentation/pages/register_page.dart:27-29`, `lib/features/auth/domain/repositories/auth_repository.dart`, `lib/features/auth/data/repositories/auth_repository_impl.dart`, `lib/features/auth/data/datasources/auth_remote_datasource.dart`, `lib/features/users/data/user_management_datasource.dart:61-65`, `lib/features/users/presentation/providers/users_provider.dart`, `lib/features/users/presentation/pages/users_page.dart:42`

**Interfaces:**
- `class RegisterRequest(BaseModel): username: str (3–64); full_name: str (≤128); password: str (6–128)` (không có `role`).
- `class ApproveRequest(BaseModel): role: Role`.
- `user_service.register(db, payload: RegisterRequest) -> User`: tạo `role=Role.T`, `status=pending`, `code=next_user_code(db, Role.T)`.
- `user_service.approve(db, user_id: int, role: Role) -> User`: nếu `role != user.role` → `user.role = role; user.code = next_user_code(db, role)`; `status = active`.
- Endpoint `POST /auth/users/{id}/approve` nhận body `ApproveRequest` (bắt buộc).
- Flutter `UserManagementDataSource.approve(int id, {required String role})`; `AuthRepository.register({username, fullName, password})`.

- [ ] **Step 1: Test fail**

```python
def test_register_ignores_role_and_approve_assigns_role(client):
    r = client.post(f"{V}/auth/register", json={"username": "x1", "full_name": "X", "password": "secret12", "role": "M"})
    assert r.status_code == 201 and r.json()["role"] == "T" and r.json()["status"] == "pending"
    r = client.post(f"{V}/auth/users/{r.json()['id']}/approve", headers=admin)
    assert r.status_code == 422          # body role bắt buộc
    r = client.post(f"{V}/auth/users/{uid}/approve", json={"role": "A"}, headers=admin)
    assert r.json()["role"] == "A" and r.json()["code"].startswith("A")
```

Sửa `test_self_register_then_approve_flow` cho khớp (approve gửi `{"role": ...}`).

- [ ] **Step 2:** Run `tests/test_auth_users.py` → FAIL.
- [ ] **Step 3:** Sửa schema, service, endpoint theo Interfaces.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5: Flutter**: bỏ dropdown role ở register page; `approve` gửi role; `users_page.onApprove` mở hộp chọn role (mặc định role hiện tại của tài khoản pending, danh sách M/T/A/F) rồi gọi `controller.approve(id, role)`.
- [ ] **Step 6:** `$FLUTTER analyze && $FLUTTER test test/features/users` → PASS.
- [ ] **Step 7: Commit** `fix(auth): self-registration cannot pick a role; admin assigns it at approval`

---

### Task 3: `leave_type` phải khớp độ dài kỳ nghỉ (B3)

**Files:**
- Modify: `backend/app/services/leave_service.py:93-95`, `backend/app/core/i18n.py`
- Test: `backend/tests/test_leave_service.py`
- Modify (Flutter): `lib/features/leaves/presentation/pages/leaves_page.dart:306-320`, `lib/i18n/app_localizations.dart`

**Interfaces:**
- i18n key `leave.type_span_mismatch`: en "Leave of 5 days or less is monthly leave; more than 5 consecutive days must be registered as annual leave." vi "Nghỉ từ 5 ngày trở xuống là nghỉ tháng; trên 5 ngày liên tục phải đăng ký nghỉ phép năm."
- `create_request`: nếu `payload.leave_type is not None and payload.leave_type is not classify(start, end)` → `HTTPException(422, t("leave.type_span_mismatch"))`.

- [ ] **Step 1: Test fail**

```python
def test_monthly_label_on_long_span_rejected(client):   # 10 ngày + monthly → 422
def test_annual_label_on_short_span_rejected(client):   # 3 ngày + annual → 422
def test_matching_label_accepted(client):               # 3 ngày + monthly → 201
```

(tạo user qua API, đăng nhập, POST `/leaves`; `ENVIRONMENT=dev` nên cửa sổ không chặn).

- [ ] **Step 2:** Run → FAIL. **Step 3:** sửa service + i18n. **Step 4:** Run → PASS.
- [ ] **Step 5: Flutter**: trước `submitRequest`, `final days = endDate!.difference(startDate!).inDays + 1`; nếu `(isAnnual && days <= 5) || (!isAnnual && days > 5)` → `DsFeedback.show(ctx, l.text('leaveTypeSpanMismatch'), tone: DsTone.warning); return;`. Key en/vi cùng nội dung trên.
- [ ] **Step 6:** `$FLUTTER analyze` → No issues. **Step 7: Commit** `fix(leave): leave type must match the span (>5 days is annual)`

---

### Task 4: Sửa ô kế hoạch đã publish phải cập nhật ô chấm công đã seed (B5)

**Files:**
- Modify: `backend/app/services/attendance_service.py`, `backend/app/services/schedule_service.py` (`manual_override`, `apply_shift_change`), `backend/app/services/self_arrange_service.py:200-204`
- Test: `backend/tests/test_attendance_sync.py` (mới)

**Interfaces:**
- `attendance_service.sync_planned_cell(db, user_id: int, work_date: date, code: AttendanceCode) -> bool`: tìm `AttendanceRecord(user_id, work_date)`; nếu có **và** `recorded_by is None` → `cell.code = code`, trả `True`; ngược lại `False`. Không commit.
- Gọi sau mỗi lần đổi `ShiftAssignment.code` khi `schedule.status is ScheduleStatus.published` (3 chỗ trên).

- [ ] **Step 1: Test fail**

```python
def test_override_on_published_month_updates_seeded_actual(client):
    # generate → publish → override user u ngày 15 = "T"
    actual = [r for r in client.get(f"{V}/attendance", params={"year": 2026, "month": 12}, headers=admin).json()
              if r["user_id"] == u and r["work_date"] == "2026-12-15"][0]
    assert actual["code"] == "T"

def test_override_does_not_touch_admin_recorded_actual(client):
    # PUT /attendance ngày 16 = "B" (recorded_by = admin) → override ngày 16 = "T" → actual vẫn "B"
```

- [ ] **Step 2:** Run → FAIL. **Step 3:** thêm hàm + 3 lời gọi. **Step 4:** Run cả `tests/test_schedule_service.py tests/test_shift_change_service.py tests/test_attendance_sync.py` → PASS.
- [ ] **Step 5: Commit** `fix(attendance): published-roster edits propagate to untouched seeded actuals`

---

### Task 5: Duyệt / huỷ nghỉ cập nhật thẳng vào lịch đã tạo (B4)

**Files:**
- Modify: `backend/app/services/schedule_service.py`, `backend/app/services/leave_service.py:157-213,278-300`, `backend/app/core/i18n.py`
- Test: `backend/tests/test_leave_service.py`

**Interfaces:**
- `schedule_service.apply_leave_span(db, user_id: int, start: date, end: date, code: AttendanceCode) -> list[str]`: với mỗi `(year, month)` trong span có `MonthlySchedule`: đặt `cell.code = code` cho các ngày thuộc span; nếu published → `attendance_service.sync_planned_cell`; trả về `[f"{year}-{month:02d}: {v.message}" for v in _recheck_violations(db, schedule)]`. Không commit.
- `leave_service.decide`: approve → `warnings += apply_leave_span(..., AttendanceCode.AL)`; `revoke` → `apply_leave_span(..., AttendanceCode.X)`. Thay `leave.schedule_stale` bằng key mới `leave.schedule_applied` (en "The already-generated schedule was updated with this decision; review the warnings." / vi "Lịch đã tạo được cập nhật theo quyết định này; hãy xem các cảnh báo.") khi có ít nhất 1 tháng có lịch. Xoá `_overlaps_generated_schedule` và key `leave.schedule_stale`.

- [ ] **Step 1: Test fail**

```python
def test_approve_after_generate_writes_al_into_grid(client):
    # 4 user A, generate 2026-12, user u xin 20–22/12 monthly, approve
    grid = client.get(f"{V}/schedules/2026/12", headers=admin).json()["assignments"]
    assert {a["code"] for a in grid if a["user_id"] == u and a["work_date"] in days} == {"AL"}
    assert any("updated" in w for w in decision["warnings"])

def test_revoke_restores_x(client):   # revoke → 3 ô về "X"
def test_leave_spanning_two_months_updates_only_existing_schedule(client):  # Review Focus 1
```

- [ ] **Step 2:** Run → FAIL. **Step 3:** cài đặt. **Step 4:** Run `tests/test_leave_service.py tests/test_schedule_service.py` → PASS.
- [ ] **Step 5: Commit** `fix(leave): approving or revoking leave updates an already-generated schedule`

---

### Task 6: Một nguồn sự thật cho carry (B6)

**Files:**
- Modify: `backend/app/services/leave_conflict_resolver.py:71-100`, `backend/app/services/leave_service.py:376-421`, `backend/app/services/calculation_service.py:29-67`
- Test: `backend/tests/test_leave_service.py` (lớp rank), `backend/tests/test_calculation_service.py`

**Interfaces:**
- `rank(requests: list[LeaveRequest], carry_comp_by_user: dict[int, int], approved_off_by_user: dict[int, set[date]] | None = None) -> list[LeaveRequest]` (bỏ `users_by_id`).
- `conflicts_for_date`: `carry = {uid: s.carry_comp for uid, s in schedule_history.build_boundary_states(db, users, target_date.year, target_date.month).items()}`.
- `calculation_service.close_month(db, year, month)`: `ny, nm = schedule_autorun.next_month(date(year, month, 1))`; `states = schedule_history.build_boundary_states(db, users, ny, nm)`; ghi `carry_comp/carry_streak/carry_premium_off` từ `states` vào `User`. Bỏ import `carry_over_math` ở đây.

- [ ] **Step 1: Test fail**: sửa 5 test `rank(...)` truyền `{1: 3, 2: 0}`; thêm

```python
def test_close_month_equals_schedule_history(client):
    # actual A/D cho user A ngày 2026-11-03; POST /calculations/2026/11/close
    # → users.carry_comp == build_boundary_states(db, users, 2026, 12)[uid].carry_comp == 1
```

- [ ] **Step 2:** Run → FAIL. **Step 3:** cài đặt. **Step 4:** Run 2 file test → PASS.
- [ ] **Step 5: Commit** `refactor(carry): conflict ranking and month-close read carry from schedule_history`

---

### Task 7: Đi làm ngày lễ được +1 CD, mọi role (D1)

**Files:**
- Modify: `backend/app/services/carry_over_math.py:27-31`, `backend/app/scheduler/role_codes.py:26-45`, `backend/app/scheduler/constraints_comp_days.py:46-50`, `backend/app/services/schedule_history.py:98-103`, `backend/app/services/schedule_violation_checker.py:194-221`, `backend/app/services/self_arrange_service.py:74`
- Test: `backend/tests/test_calculation_service.py`, `backend/tests/test_engine_comp_days.py:84-94`, `backend/tests/test_engine_roles.py`, `backend/tests/test_role_code_validation.py`

**Interfaces:**
- `carry_over_math.comp_balance(records: list[tuple[date, AttendanceCode]], holidays: set[date]) -> int`: `earned = Σ[code is A_D] + Σ[code.is_working and day in holidays]`; `consumed = Σ[code is CD]`; `max(0, earned − consumed)`. (A/D đúng ngày lễ = 2.)
- `ROLE_CODES`: `T → (AD, X, CD)`, `M → (O_D, X, CD)`, `F → (AD, X, CD)`; `A` giữ nguyên.
- `constraints_comp_days.add`: áp cho **mọi** người (bỏ `if p.role is not Role.A`).
- `schedule_history.build_boundary_states`: `carry_comp = comp_balance(records, holidays) if records else user.carry_comp` cho mọi role.
- `check_comp_days`: bỏ nhánh "role never earns"; so `cd` với `owed` cho mọi role.
- `self_arrange_service._validate`: `allowed = set(codes_for(requester.role)) - {AttendanceCode.CD}`.

- [ ] **Step 1: Test fail**

```python
# test_calculation_service.py (pure)
def test_working_on_holiday_earns_comp_day():
    h = {date(2026, 12, 25)}
    assert comp_balance([(date(2026,12,25), AttendanceCode.A)], h) == 1
    assert comp_balance([(date(2026,12,25), AttendanceCode.A_D)], h) == 2
    assert comp_balance([(date(2026,12,25), AttendanceCode.X)], h) == 0       # Review Focus 4
    assert comp_balance([(date(2026,12,25), AttendanceCode.AD), (date(2027,1,4), AttendanceCode.CD)], h) == 0
# test_engine_comp_days.py: thay test_role_t_carry_comp_ignored_no_cd_assigned bằng
def test_role_t_owed_cd_is_scheduled():   # PersonInput(1, Role.T, carry_comp=1) → đúng 1 ô CD, còn lại AD/X
```

Cập nhật `test_engine_roles.py` (domain T/M/F có CD) và `test_role_code_validation.py` (CD hợp lệ cho T trên lịch kế hoạch). Thêm vào `test_schedule_service.py` (hoặc file self-arrange hiện có): `test_self_arrange_cannot_touch_al_or_cd_cell` → batch của user T đặt `X` lên ngày đang `AL` hoặc `CD` → 422 `selfarrange.cell_locked` (Review Focus 3).

- [ ] **Step 2:** Run 4 file → FAIL. **Step 3:** cài đặt 6 file. **Step 4:** Run `pytest -q` toàn bộ → PASS (engine test có thể mất ~5 phút).
- [ ] **Step 5: Commit** `feat(comp): working on a public holiday earns a comp day for every role`

---

### Task 8: (BỎ) Phép AL tính là ngày nghỉ của tuần

Owner 2026-11-06: "giữ nguyên như code". Quyết định #4 giữ nguyên: phép AL không thay 2 ngày X của tuần. Không làm gì ở task này.

---

### Task 9: Phép năm còn lại (D4)

**Files:**
- Create: `backend/alembic/versions/0008_annual_leave_quota.py`
- Modify: `backend/app/core/config.py`, `backend/app/models/user.py:29-31`, `backend/app/core/bootstrap.py:90-97`, `backend/app/services/user_service.py:83-96,175-219`, `backend/app/schemas/user.py`, `backend/app/schemas/leave.py`, `backend/app/services/leave_service.py`, `backend/app/api/v1/endpoints/leaves.py`, `backend/app/services/compliance_service.py:147-149`, `backend/app/core/i18n.py`
- Test: `backend/tests/test_leave_service.py`, `backend/tests/test_auth_users.py`
- Modify (Flutter): `lib/features/leaves/data/datasources/leaves_remote_datasource.dart`, `lib/features/leaves/presentation/providers/leaves_provider.dart`, `lib/features/leaves/presentation/pages/leaves_page.dart`, `lib/design_system/business_views.dart` (DsLeavesView), `lib/features/users/presentation/widgets/create_user_dialog.dart`, `lib/features/auth/data/models/user_model.dart`, `lib/core/constants/api_endpoints.dart`, `lib/i18n/app_localizations.dart`

**Interfaces:**
- Migration 0008: `op.add_column("users", sa.Column("annual_leave_quota", sa.Integer(), nullable=False, server_default="30"))`; `with op.batch_alter_table("users") as b: b.drop_column("annual_leave_balance")`.
- `Settings.ANNUAL_LEAVE_DEFAULT_DAYS: int = 30` (placeholder, khách chốt).
- `User.annual_leave_quota: Mapped[int] = mapped_column(Integer, default=0)`; `_persist_new`, `ensure_first_admin` và `demo_user_seed.seed_demo_users` (`backend/app/services/demo_user_seed.py:53-62`) đặt `= settings.ANNUAL_LEAVE_DEFAULT_DAYS`.
- `UserUpdate.annual_leave_quota: int | None = Field(default=None, ge=0, le=365)`; `UserRead.annual_leave_quota: int`.
- `class AnnualLeaveSummary(BaseModel): year: int; quota: int; used: int; pending: int; remaining: int`.
- `leave_service.annual_leave_summary(db, user_id: int, year: int) -> AnnualLeaveSummary`: `used` = tổng ngày của đơn **approved** cắt trong `[1/1, 31/12]`; `pending` tương tự với đơn pending; `remaining = quota - used`.
- `decide`: approve mà `remaining - span_days < 0` → `warnings.append(t("leave.balance_exceeded"))` (en "Approving exceeds this person's annual leave quota." / vi "Duyệt đơn này vượt định mức phép năm của nhân sự.").
- `GET /leaves/balance?year=&user_id=` (ActiveUser; `ensure_self_or_admin`; mặc định `user_id = me`, `year = today.year`). Khai báo **trước** các route `/{leave_id}/...`.
- Flutter: `ApiEndpoints.leaveBalance = '/leaves/balance'`; `LeavesRemoteDataSource.fetchBalance({int? year}) -> AnnualLeaveBalance`; `LeavesState.balance`; `DsLeavesView` thêm `annualLeaveRemaining: int?` hiển thị metric `annualLeaveRemaining` (en "Annual leave left" / vi "Phép năm còn lại"); `create_user_dialog` thêm ô số `annualLeaveQuota` (en "Annual leave quota" / vi "Định mức phép năm") gửi `annual_leave_quota`.

- [ ] **Step 1: Test fail**

```python
def test_annual_leave_summary_counts_approved_days_in_year(client):
    # quota 30; approved 3 ngày 2026-12-20..22; pending 2 ngày → used 3, pending 2, remaining 27
def test_balance_endpoint_self_and_admin(client):
    # user xem của mình 200; user xem user khác 403; admin xem bất kỳ 200
def test_admin_can_set_quota(client):   # PATCH /users/{id} {"annual_leave_quota": 25} → UserRead 25
```

- [ ] **Step 2:** Run → FAIL. **Step 3:** cài đặt backend + migration. **Step 4:** `pytest -q` → PASS; `alembic upgrade head` trên SQLite rỗng chạy được: `DATABASE_URL=sqlite:////tmp/mig.db $PY -m alembic upgrade head`.
- [ ] **Step 5: Flutter** theo Interfaces. **Step 6:** `$FLUTTER analyze` → No issues.
- [ ] **Step 7: Commit** `feat(leave): annual leave quota and remaining balance`

---

### Task 10: Dọn 4 lỗi nhỏ backend (B7, B8, B9, B10)

**Files:**
- Modify: `backend/app/scheduler/constraints_off_chain.py:50-54`, `backend/app/services/leave_windows.py:29-47`, `backend/app/services/schedule_autorun.py:30-37,72-80`, `backend/scripts/reset_all_passwords.py`, `backend/scripts/seed_demo_users.py`, `backend/app/services/attendance_service.py:176-196`, `backend/.env.example`
- Test: `backend/tests/test_engine_cross_month_rules.py`, `backend/tests/test_leave_service.py`, `backend/tests/test_schedule_service.py:137`, `backend/tests/test_attendance_sick.py`

**Interfaces:**
- `constraints_off_chain`: tổng ngày nghỉ trong cửa sổ = `Σ x[(uid, d, c)] for c in codes_for(role) if c in OFF_CODES` (X + CD).
- `leave_windows.registration_last_day() -> int = settings.AUTORUN_DAY`; `is_monthly_window_open` dùng nó thay số 20.
- `maybe_run_autorun`: chạy khi `today.day == settings.AUTORUN_DAY + 1`; cron `hour=0, minute=5`. `.env.example` ghi "AUTORUN_DAY=20: cửa sổ đóng hết ngày 20, lịch tự tạo 00:05 ngày 21".
- Scripts: thêm `--allow-non-dev`; nếu `settings.ENVIRONMENT != "dev"` và không có cờ → in host DB (`make_url(settings.DATABASE_URL).host`) và thoát mã 2.
- `_recently_sick`: `work_date >= before - timedelta(days=30)` thay vì đầu tháng.

- [ ] **Step 1: Test fail**

```python
def test_cd_counts_toward_consecutive_off_limit():      # A: carry_comp=1, 5 X cạnh 1 CD → violation max_consecutive_off
def test_monthly_window_closes_on_autorun_day(...)      # ngày 20 mở, ngày 21 đóng, theo settings.AUTORUN_DAY
def test_autorun_fires_day_after_close(client)          # day 21 → True, day 20 → False
def test_recently_sick_rule_spans_month_boundary(client) # S ngày 28/11 → bị ép A/D ngày 2/12
```

- [ ] **Step 2:** Run → FAIL. **Step 3:** cài đặt. **Step 4:** `pytest -q` → PASS.
- [ ] **Step 5: Commit** `fix: off-chain counts CD, autorun after window close, guarded scripts, 30-day sick lookback`

---

### Task 11: Hai endpoint phục vụ Flutter (danh bạ mã nhân sự, trạng thái cửa sổ nghỉ)

**Files:**
- Modify: `backend/app/schemas/user.py`, `backend/app/api/v1/endpoints/users.py`, `backend/app/schemas/leave.py`, `backend/app/services/leave_service.py`, `backend/app/api/v1/endpoints/leaves.py`
- Test: `backend/tests/test_auth_users.py`, `backend/tests/test_leave_service.py`

**Interfaces:**
- `class UserDirectoryEntry(ORMModel): id: int; code: str; role: Role` (không có tên: app hiển thị mã, xem `leaves_provider.dart:127`).
- `GET /users/directory` (ActiveUser) → `list[UserDirectoryEntry]` chỉ user `active`, sắp theo `code`. Khai báo trước `/{user_id}`.
- `class LeaveWindowRead(BaseModel): monthly_open: bool; monthly_target_year: int; monthly_target_month: int; annual_target_year: int; closes_on_day: int; enforced: bool`.
- `leave_service.window_status(today: date | None = None) -> LeaveWindowRead` (`enforced = settings.ENVIRONMENT != "dev"`; khi không enforce, `monthly_open = True`).
- `GET /leaves/window` (ActiveUser). Khai báo trước `/{leave_id}/...`.

- [ ] **Step 1: Test fail**

```python
def test_directory_lists_active_codes_only(client):   # pending/disabled bị loại; không có key full_name
def test_leave_window_status(client):                 # ngày 5 → monthly_open True, target = tháng sau; ngày 25 → False
```

- [ ] **Step 2:** FAIL → **Step 3:** cài đặt → **Step 4:** PASS → **Step 5: Commit** `feat(api): user directory and leave window status for the client`

---

### Task 12: Flutter màn lịch (C1, C3, C4, C7)

**Files:**
- Modify: `lib/core/constants/shift_codes.dart`, `lib/core/constants/api_endpoints.dart`, `lib/design_system/business_views.dart:236-283`, `lib/features/schedule/presentation/pages/schedule_page.dart:118-126,195-201,346-371`, `lib/features/schedule/presentation/providers/schedule_provider.dart`, `lib/features/schedule/data/datasources/schedule_remote_datasource.dart`, `lib/features/users/data/user_management_datasource.dart`, `lib/i18n/app_localizations.dart`
- Test: `test/features/schedule/schedule_role_gating_test.dart` (mới)

**Interfaces:**
- `ShiftCodeX.plannedCodesFor(UserRole role) -> List<ShiftCode>`: A → `[a, d, aD, x, cd, t, b, al]`; T/F → `[ad, x, cd, t, b, al]`; M → `[oD, x, cd, t, b, al]`. Không bao giờ có `s`.
- `DsScheduleView.onGenerate`, `onPublish` thành `VoidCallback?`; `actions` chỉ thêm nút khi khác null.
- `UserManagementDataSource.directory() -> List<UserDirectoryEntry>` (GET `/users/directory`), `ApiEndpoints.usersDirectory`.
- Controller trong `schedule_provider.dart` khi tải tháng: admin → `/users` như cũ; nhân viên → `directory()`; tên hàng = `code` (cùng quy ước ẩn danh như `leaves_provider.dart:127`), role từ directory.
- Nhân viên: `onCellTap` chỉ cho hàng của chính mình → mở `ShiftChangeRequestDialog` (đã có ở `shift_change_dialog.dart`) với ngày đã chọn → `createShiftChange`; dưới roster hiển thị danh sách đơn của mình (`fetchShiftChanges(all: false)`) bằng `DsDataTable` cột ngày, loại, mã, trạng thái.
- i18n mới: `myShiftChangeRequests`, `requestShiftChange`, `shiftChangeSubmitted` en/vi.

- [ ] **Step 1: Widget test fail**

```dart
testWidgets('employee sees no generate/publish and cannot pick S', ...)  // ProviderScope override auth = role T → không có text 'Generate schedule'; mở dialog sửa ô (admin) → items không chứa 'S'
```

- [ ] **Step 2:** `$FLUTTER test test/features/schedule` → FAIL. **Step 3:** cài đặt. **Step 4:** `$FLUTTER analyze && $FLUTTER test test/features/schedule` → PASS.
- [ ] **Step 5: Commit** `feat(flutter): employee shift-change requests, role-safe code picker, admin-only roster actions`

---

### Task 13: Flutter phiên, chấm công cá nhân, cửa sổ nghỉ, chuỗi i18n (C2, C5, C6, C8, C9, C11)

**Files:**
- Modify: `lib/features/auth/presentation/providers/auth_provider.dart`, `lib/features/auth/domain/entities/user.dart`, `lib/features/auth/data/models/user_model.dart`, `lib/app.dart`, `lib/core/router/app_router.dart:21-27,48-63`, `lib/features/home/presentation/pages/home_shell.dart:61-83`, `lib/features/attendance/presentation/pages/attendance_page.dart:76-83`, `lib/features/attendance/presentation/providers/attendance_provider.dart`, `lib/features/leaves/data/datasources/leaves_remote_datasource.dart`, `lib/features/leaves/presentation/providers/leaves_provider.dart:120-137`, `lib/features/leaves/presentation/pages/leaves_page.dart:54-55`, `lib/features/reports/presentation/providers/reports_provider.dart:74,84`, `lib/features/reports/presentation/pages/reports_page.dart:186`, `lib/features/flights/presentation/providers/flights_provider.dart:154`, `lib/features/schedule/presentation/widgets/self_arrange_pending_panel.dart:55`, `lib/i18n/app_localizations.dart`
- Test: `test/features/auth/session_restore_test.dart` (mới)

**Interfaces:**
- `AuthController.restoreSession() -> Future<void>`: `token = await tokenStorage.read()`; null → return; `user = await _repository.currentUser()` → `state = AuthState(user: user)` + `activateUser`; lỗi → `_repository.logout()`, state rỗng. Gọi một lần khi app khởi động (trong `app.dart`, trước khi router hiện). Router: `if (user != null && _publicPaths.contains(path)) return AppRoute.schedule;`.
- `User.carryComp: int` (từ `carry_comp` của `/users/me`); `leaves_provider._toRow` dùng `u.carryComp`.
- Bỏ `AppRoute.attendance` khỏi `_adminOnlyPaths`; nav nhân viên thêm `navMyAttendance` (en "My attendance" / vi "Chấm công của tôi"); `attendance_page`: `!isAdmin` → `load(isAdmin: false)` (đã có ở `attendance_provider.dart:60-66`), và mọi callback admin của `DsAttendanceView` (ngày lễ `onHolidays`, ghi chấm công, báo ốm, đóng tháng) truyền null; đổi các tham số đó trong `DsAttendanceView` thành nullable và ẩn nút khi null.
- `LeavesRemoteDataSource.fetchWindow() -> LeaveWindow` (GET `/leaves/window`); `registrationOpen: state.window?.monthlyOpen ?? true`; key `leavesSubtitle` en "Monthly leave: register by day {day} of the previous month. Annual leave: register the year before." / vi "Nghỉ tháng: đăng ký trước ngày {day} tháng trước. Nghỉ phép năm: đăng ký từ năm trước." Xoá chuỗi "unrestricted in development".
- Chuỗi cứng → key: `selectYearMonthFirst`, `selectYearFirst`, `statusReady`, `statusComplete`; `'User ${id}'` → mã từ directory (Task 12) hoặc `l.text('userFallback')` ("ID {id}").

- [ ] **Step 1: Test fail**

```dart
test('restoreSession signs in from a stored token', ...)   // TokenStorage giả có token, AuthRepository giả trả User → state.user != null
test('restoreSession clears a rejected token', ...)        // currentUser ném 401 → state.user == null, token bị xoá
```

- [ ] **Step 2:** FAIL → **Step 3:** cài đặt → **Step 4:** `$FLUTTER analyze && $FLUTTER test` (trừ golden) → PASS.
- [ ] **Step 5: Commit** `feat(flutter): session restore, employee attendance view, live leave window, i18n cleanup`

---

### Task 14 (tuỳ chọn, chỉ khi owner chọn D6 = "đưa lại ưu tiên cuối tuần"): Thưởng cặp T7+CN > T6+T7 > CN+T2

**Files:**
- Modify: `backend/app/scheduler/objective_off_pairing.py`, `backend/app/scheduler/objectives.py:44-50`
- Test: `backend/tests/test_engine_objectives.py`

**Interfaces:**
- `WEEKEND_PAIR_SCORE: dict[tuple[int, int], int] = {(5, 6): 3, (4, 5): 2, (6, 0): 1}` (weekday của 2 ngày liền nhau).
- `WEIGHTS["weekend_pairing"] = 10`; thêm penalty mỗi block: `10 * Σ both_i * (3 - WEEKEND_PAIR_SCORE.get((d_i.weekday(), d_{i+1}.weekday()), 0))`.

- [ ] **Step 1: Test fail** `test_free_month_pairs_offs_on_saturday_sunday`: 1 người T, không chuyến bay → mọi block chứa đủ T7 và CN có cặp X đúng T7+CN.
- [ ] **Step 2:** FAIL → **Step 3:** cài đặt → **Step 4:** `pytest tests/test_engine_objectives.py tests/test_engine_off_days.py` → PASS.
- [ ] **Step 5: Commit** `feat(engine): prefer Sat+Sun > Fri+Sat > Sun+Mon for the weekly off pair`

---

### Task 15: Tài liệu, golden, cổng kiểm tra cuối

**Files:**
- Modify: `docs/design-decisions.md`, `README.md`, `docs/codebase-summary.md`, `docs/system-architecture.md`, `docs/code-standards.md`, `docs/project-changelog.md`, `DESIGN/README.md` (mới, 5 dòng), `attendance_scheduler_app/test/goldens/*.png`

- [ ] **Step 1: design-decisions**: #4 giữ nguyên (owner tái xác nhận 2026-11-06); sửa #5 (lễ đi làm → +1 CD), #13 (mọi role); thêm #24 regenerate guard, #25 role gán khi duyệt, #26 leave_type khớp span, #27 sửa lịch publish đồng bộ chấm công seed, #28 duyệt/huỷ nghỉ cập nhật lịch, #29 carry một nguồn, #30 định mức phép năm (mặc định 30, khách chốt), #31 autorun 00:05 ngày 21, #32 danh bạ chỉ mã. "Open questions": D6, D7, số ngày định mức phép năm, Betriebsrat.
- [ ] **Step 2: README** mục Status: số test thật, bỏ câu "flutter test clean" nếu chưa đúng. **codebase-summary**: 0008, số test. **system-architecture**: domain `{A,D,X,CD}` / `{AD,X,CD}` / `{O/D,X,CD}`, trọng số thật. **code-standards**: audit fail-loud. **changelog**: mục 2026-11. `DESIGN/README.md`: "DESIGN_IMPLEMENTATION_GUIDE.md và UI_STYLE_GUIDE.md viết cho dự án Next.js khác; chỉ DESIGN_GUI*.md áp dụng cho app này."
- [ ] **Step 3: Golden**: `cd attendance_scheduler_app && $FLUTTER test --update-goldens test/visual_golden_test.dart` rồi `$FLUTTER test` → tất cả PASS. Xem lại 3 ảnh mới bằng mắt.
- [ ] **Step 4: Cổng cuối**

Run: `cd backend && $PY -m ruff check app tests && $PY -m mypy app && $PY -m pytest -q`
Expected: 0 lỗi, no issues, `N passed` với N ≥ 188 + số test mới, 0 failed.
Run: `cd attendance_scheduler_app && $FLUTTER analyze && $FLUTTER test`
Expected: No issues; 0 failed.

- [ ] **Step 5: Commit** `docs: record 2026-11 decisions and remediation; refresh goldens`
