"""Minimal message catalog for English (primary) and Vietnamese (spec §2).

Keep API-facing messages here so both languages stay in sync. The client
(Flutter) has its own ARB-based localization for UI labels; this catalog is
only for server-generated messages (errors, scheduler diagnostics, ...).
"""

from __future__ import annotations

from contextvars import ContextVar

from app.core.config import settings

# Per-request language (set by the Accept-Language middleware in main.py).
# ContextVars survive FastAPI's run_in_threadpool, so sync endpoints see it.
_request_language: ContextVar[str | None] = ContextVar(
    "request_language", default=None
)


def set_request_language(lang: str | None) -> None:
    _request_language.set(lang)

MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "auth.invalid_credentials": "Incorrect username or password.",
        "auth.inactive_user": "User account is not active.",
        "auth.admin_required": "Admin privileges are required.",
        "auth.forbidden_other_user": "You may only access your own data.",
        "user.not_found": "User not found.",
        "user.username_taken": "That username is already taken.",
        "user.not_pending": "Only a pending account can be approved.",
        "user.last_admin_lockout": "You cannot remove or disable the last remaining admin.",
        "user.fixed_team_empty": "No active fixed-team members will remain after this change.",
        "schedule.infeasible": "No valid schedule could be found.",
        "schedule.not_found": "Schedule not found.",
        "schedule.published_locked": "Schedule is published; regenerate requires force.",
        "schedule.has_overrides": "Schedule has manual edits; regenerate requires force.",
        # --- Flights (F-04) ---
        "flight.day_not_found": "Flight day not found.",
        "flight.invalid_pairs": "flight_pairs must be 0, 1 or 2.",
        "flight.import_failed": "Excel import failed.",
        "flight.import_bad_file": "Unsupported or unreadable Excel file.",
        "flight.preset_not_found": "Flight preset not found.",
        # --- Leaves (F-05/F-06) ---
        "leave.not_found": "Leave request not found.",
        "leave.window_closed_monthly": "Monthly leave registration is open from day 1 to day {day} of the previous month.",
        "leave.window_closed_annual": "Annual leave can only be registered for the next year (Y+1).",
        "leave.already_decided": "This leave request was already decided.",
        "leave.overlap": "An overlapping leave request already exists.",
        "leave.invalid_range": "End date must not be before start date.",
        "leave.type_span_mismatch": "Leave of 5 days or less is monthly leave; more than 5 consecutive days must be registered as annual leave.",
        "leave.schedule_applied": "The already-generated schedule was updated with this decision; review the warnings.",
        "leave.schedule_not_generated": "no schedule yet — this decision applies when the month is generated.",
        "leave.revoke_only_approved": "Only an approved leave can be revoked.",
        "leave.staffing_impossible": "flights CANNOT be covered — too few group-A staff remain that day.",
        "leave.staffing_short_ordinary": (
            "not enough role-A staff for ordinary A and D coverage that day."
        ),
        "leave.balance_exceeded": "Approving exceeds this person's annual leave quota.",
        # --- Shift changes (decision #8) ---
        "swap.not_found": "Shift-change request not found.",
        "swap.own_cell_only": "You can only request changes for your own scheduled day.",
        "swap.already_decided": "This shift-change request was already decided.",
        "swap.counterpart_required": "A colleague must be selected for a swap request.",
        "swap.code_required": "A requested code is required for a change request.",
        "swap.no_schedule": "There is no schedule for that date yet.",
        "swap.code_not_requestable": "Employees may only request their regular working or off codes.",
        # --- Attendance / holidays (F-10..F-13) ---
        "attendance.not_found": "Attendance record not found.",
        "holiday.not_found": "Holiday not found.",
        "attendance.sick_no_cover": "No eligible colleague to cover the sick shift; resolve manually (F-09).",
        "attendance.sick_only": "This endpoint only handles sick (S) days.",
        # --- Time clock (owner 2026-07-09) ---
        "clock.already_checked_in": "Already checked in today.",
        "clock.not_checked_in": "You have not checked in today.",
        "clock.already_checked_out": "Already checked out today.",
        # --- Self-arrange (owner 2026-07-09) ---
        "selfarrange.forbidden_role": "Your role cannot self-arrange shifts.",
        "selfarrange.empty_changes": "The request contains no changes.",
        "selfarrange.cell_not_found": "One of the selected days has no scheduled cell of yours.",
        "selfarrange.invalid_code": "A requested code is not allowed for your role.",
        "selfarrange.breaks_weekly_off": "The arrangement must keep exactly the required off days in every 7-day block.",
        "selfarrange.cell_locked": "Leave/sick days cannot be rearranged — only regular working (AD) and off (X) days.",
        "selfarrange.not_found": "Self-arrange request not found.",
        "selfarrange.already_decided": "This self-arrange request was already decided.",
        "schedule.month_out_of_range": "Future months beyond next-next month are not visible.",
        "schedule.sick_not_planned": (
            "Sick (S) is recorded in actual attendance only, never in the planned "
            "schedule."
        ),
        "audit.write_failed": "Audit log write failed; the action was not confirmed.",
        # --- Review 2026-11-08 (Task 4): attendance, validation, decisions ---
        "attendance.schedule_not_published": (
            "Attendance can only be seeded from a published schedule."
        ),
        "attendance.sick_cover_forced": (
            "Recently sick colleague assigned the A/D cover (§6)."
        ),
        "attendance.sick_cover_fewest_ad": (
            "Colleague with the fewest A/D doubles this month assigned the cover."
        ),
        "code.not_allowed_for_role": (
            "Code {code} is not valid for role {role}; allowed: {allowed}"
        ),
        "request.decision_status_invalid": (
            "Decision status must be 'approved' or 'rejected'."
        ),
        "compliance.retention_too_short": (
            "Retention cutoff must be at least 24 months in the past "
            "(working-time records, ArbZG §16)."
        ),
    },
    "vi": {
        "auth.invalid_credentials": "Sai tên đăng nhập hoặc mật khẩu.",
        "auth.inactive_user": "Tài khoản chưa được kích hoạt.",
        "auth.admin_required": "Yêu cầu quyền quản trị.",
        "auth.forbidden_other_user": "Bạn chỉ được truy cập dữ liệu của chính mình.",
        "user.not_found": "Không tìm thấy người dùng.",
        "user.username_taken": "Tên đăng nhập đã tồn tại.",
        "user.not_pending": "Chỉ duyệt được tài khoản đang chờ duyệt.",
        "user.last_admin_lockout": "Không thể hạ quyền hoặc vô hiệu hoá admin cuối cùng.",
        "user.fixed_team_empty": "Sẽ không còn thành viên fixed team nào đang hoạt động sau thay đổi này.",
        "schedule.infeasible": "Không tìm được lời giải hợp lệ cho lịch.",
        "schedule.not_found": "Không tìm thấy lịch.",
        "schedule.published_locked": "Lịch đã publish; tạo lại cần force.",
        "schedule.has_overrides": "Lịch có chỉnh tay; tạo lại cần force.",
        # --- Flights (F-04) ---
        "flight.day_not_found": "Không tìm thấy ngày bay.",
        "flight.invalid_pairs": "Số cặp chuyến bay phải là 0, 1 hoặc 2.",
        "flight.import_failed": "Import Excel thất bại.",
        "flight.import_bad_file": "File Excel không hợp lệ hoặc không đọc được.",
        "flight.preset_not_found": "Không tìm thấy preset chuyến bay.",
        # --- Leaves (F-05/F-06) ---
        "leave.not_found": "Không tìm thấy đơn nghỉ.",
        "leave.window_closed_monthly": "Đăng ký nghỉ tháng mở từ ngày 1 đến ngày {day} của tháng trước.",
        "leave.window_closed_annual": "Nghỉ phép năm chỉ được đăng ký cho năm sau (Y+1).",
        "leave.already_decided": "Đơn nghỉ này đã được quyết định.",
        "leave.overlap": "Đã tồn tại đơn nghỉ trùng thời gian.",
        "leave.invalid_range": "Ngày kết thúc không được trước ngày bắt đầu.",
        "leave.type_span_mismatch": "Nghỉ từ 5 ngày trở xuống là nghỉ tháng; trên 5 ngày liên tục phải đăng ký nghỉ phép năm.",
        "leave.schedule_applied": "Lịch đã tạo được cập nhật theo quyết định này; hãy xem các cảnh báo.",
        "leave.schedule_not_generated": "chưa có lịch — quyết định này sẽ được áp dụng khi tạo lịch tháng đó.",
        "leave.revoke_only_approved": "Chỉ hủy được đơn nghỉ đã duyệt.",
        "leave.staffing_impossible": "KHÔNG thể phủ chuyến bay — nhóm A còn lại quá ít người ngày này.",
        "leave.staffing_short_ordinary": (
            "không đủ nhân sự role A để phủ ca A và D thông thường trong ngày."
        ),
        "leave.balance_exceeded": "Duyệt đơn này vượt định mức phép năm của nhân sự.",
        # --- Shift changes (decision #8) ---
        "swap.not_found": "Không tìm thấy yêu cầu đổi ca.",
        "swap.own_cell_only": "Chỉ được yêu cầu đổi ca cho ngày làm của chính mình.",
        "swap.already_decided": "Yêu cầu đổi ca này đã được quyết định.",
        "swap.counterpart_required": "Cần chọn đồng nghiệp để hoán đổi ca.",
        "swap.code_required": "Cần chọn mã ca muốn đổi.",
        "swap.no_schedule": "Chưa có lịch cho ngày này.",
        "swap.code_not_requestable": "Nhân viên chỉ được yêu cầu mã ca làm hoặc nghỉ thông thường.",
        # --- Attendance / holidays (F-10..F-13) ---
        "attendance.not_found": "Không tìm thấy bản ghi chấm công.",
        "holiday.not_found": "Không tìm thấy ngày lễ.",
        "attendance.sick_no_cover": "Không có đồng nghiệp phù hợp để bù ca ốm; admin xử lý tay (F-09).",
        "attendance.sick_only": "Endpoint này chỉ xử lý ngày nghỉ ốm (S).",
        # --- Time clock (owner 2026-07-09) ---
        "clock.already_checked_in": "Hôm nay đã check-in rồi.",
        "clock.not_checked_in": "Bạn chưa check-in hôm nay.",
        "clock.already_checked_out": "Hôm nay đã check-out rồi.",
        # --- Self-arrange (owner 2026-07-09) ---
        "selfarrange.forbidden_role": "Vai trò của bạn không được tự sắp xếp ca.",
        "selfarrange.empty_changes": "Yêu cầu không có thay đổi nào.",
        "selfarrange.cell_not_found": "Có ngày được chọn không có ô lịch của bạn.",
        "selfarrange.invalid_code": "Có mã ca không hợp lệ với vai trò của bạn.",
        "selfarrange.breaks_weekly_off": "Sắp xếp phải giữ đúng số ngày nghỉ quy định trong mỗi block 7 ngày.",
        "selfarrange.cell_locked": "Không được sắp xếp lại ngày nghỉ phép/ốm — chỉ ngày làm (AD) và nghỉ (X) thường.",
        "selfarrange.not_found": "Không tìm thấy yêu cầu tự sắp ca.",
        "selfarrange.already_decided": "Yêu cầu tự sắp ca này đã được quyết định.",
        "schedule.month_out_of_range": "Chỉ xem được tối đa 2 tháng tương lai.",
        "schedule.sick_not_planned": (
            "Nghỉ ốm (S) chỉ được ghi ở chấm công thực tế, không đưa vào lịch kế hoạch."
        ),
        "audit.write_failed": "Ghi nhật ký kiểm toán thất bại; thao tác chưa được xác nhận.",
        # --- Review 2026-11-08 (Task 4): attendance, validation, decisions ---
        "attendance.schedule_not_published": (
            "Chỉ được khởi tạo chấm công từ lịch đã công bố."
        ),
        "attendance.sick_cover_forced": (
            "Đồng nghiệp vừa nghỉ ốm gần đây được phân ca bù A/D (§6)."
        ),
        "attendance.sick_cover_fewest_ad": (
            "Đồng nghiệp có ít ca đôi A/D nhất trong tháng được phân ca bù."
        ),
        "code.not_allowed_for_role": (
            "Mã {code} không hợp lệ với vai trò {role}; mã được phép: {allowed}"
        ),
        "request.decision_status_invalid": (
            "Trạng thái quyết định phải là 'approved' (duyệt) hoặc 'rejected' (từ chối)."
        ),
        "compliance.retention_too_short": (
            "Mốc xóa dữ liệu phải cách hiện tại ít nhất 24 tháng "
            "(hồ sơ giờ làm, ArbZG §16)."
        ),
    },
}


def t(key: str, lang: str | None = None) -> str:
    """Translate a message key; falls back to the key itself if missing.

    Language resolution: explicit arg > the request's Accept-Language
    (middleware) > DEFAULT_LANGUAGE.
    """
    language = lang or _request_language.get() or settings.DEFAULT_LANGUAGE
    return MESSAGES.get(language, MESSAGES["en"]).get(key, key)
