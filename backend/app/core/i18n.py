"""Minimal message catalog for English (primary) and Vietnamese (spec §2).

Keep API-facing messages here so both languages stay in sync. The client
(Flutter) has its own ARB-based localization for UI labels; this catalog is
only for server-generated messages (errors, scheduler diagnostics, ...).
"""

from __future__ import annotations

from app.core.config import settings

MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "auth.invalid_credentials": "Incorrect username or password.",
        "auth.inactive_user": "User account is not active.",
        "auth.admin_required": "Admin privileges are required.",
        "auth.forbidden_other_user": "You may only access your own data.",
        "user.not_found": "User not found.",
        "user.username_taken": "That username is already taken.",
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
        "leave.window_closed_monthly": "Monthly leave registration is open from day 1 to day 20 of the previous month.",
        "leave.window_closed_annual": "Annual leave (>= 5 consecutive days) must be registered during the previous calendar year.",
        "leave.already_decided": "This leave request was already decided.",
        "leave.overlap": "An overlapping leave request already exists.",
        "leave.balance_insufficient": "Insufficient annual leave balance.",
        "leave.invalid_range": "End date must not be before start date.",
        # --- Shift changes (decision #8) ---
        "swap.not_found": "Shift-change request not found.",
        "swap.own_cell_only": "You can only request changes for your own scheduled day.",
        "swap.already_decided": "This shift-change request was already decided.",
        "swap.counterpart_required": "A colleague must be selected for a swap request.",
        "swap.code_required": "A requested code is required for a change request.",
        "swap.no_schedule": "There is no schedule for that date yet.",
        # --- Attendance / holidays (F-10..F-13) ---
        "attendance.not_found": "Attendance record not found.",
        "holiday.not_found": "Holiday not found.",
        "attendance.sick_no_cover": "No eligible colleague to cover the sick shift; resolve manually (F-09).",
        "attendance.sick_only": "This endpoint only handles sick (S) days.",
    },
    "vi": {
        "auth.invalid_credentials": "Sai tên đăng nhập hoặc mật khẩu.",
        "auth.inactive_user": "Tài khoản chưa được kích hoạt.",
        "auth.admin_required": "Yêu cầu quyền quản trị.",
        "auth.forbidden_other_user": "Bạn chỉ được truy cập dữ liệu của chính mình.",
        "user.not_found": "Không tìm thấy người dùng.",
        "user.username_taken": "Tên đăng nhập đã tồn tại.",
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
        "leave.window_closed_monthly": "Đăng ký nghỉ tháng mở từ ngày 1 đến ngày 20 của tháng trước.",
        "leave.window_closed_annual": "Nghỉ phép năm (>= 5 ngày liên tục) phải đăng ký trong năm trước.",
        "leave.already_decided": "Đơn nghỉ này đã được quyết định.",
        "leave.overlap": "Đã tồn tại đơn nghỉ trùng thời gian.",
        "leave.balance_insufficient": "Số ngày phép năm còn lại không đủ.",
        "leave.invalid_range": "Ngày kết thúc không được trước ngày bắt đầu.",
        # --- Shift changes (decision #8) ---
        "swap.not_found": "Không tìm thấy yêu cầu đổi ca.",
        "swap.own_cell_only": "Chỉ được yêu cầu đổi ca cho ngày làm của chính mình.",
        "swap.already_decided": "Yêu cầu đổi ca này đã được quyết định.",
        "swap.counterpart_required": "Cần chọn đồng nghiệp để hoán đổi ca.",
        "swap.code_required": "Cần chọn mã ca muốn đổi.",
        "swap.no_schedule": "Chưa có lịch cho ngày này.",
        # --- Attendance / holidays (F-10..F-13) ---
        "attendance.not_found": "Không tìm thấy bản ghi chấm công.",
        "holiday.not_found": "Không tìm thấy ngày lễ.",
        "attendance.sick_no_cover": "Không có đồng nghiệp phù hợp để bù ca ốm; admin xử lý tay (F-09).",
        "attendance.sick_only": "Endpoint này chỉ xử lý ngày nghỉ ốm (S).",
    },
}


def t(key: str, lang: str | None = None) -> str:
    """Translate a message key; falls back to the key itself if missing."""
    language = lang or settings.DEFAULT_LANGUAGE
    return MESSAGES.get(language, MESSAGES["en"]).get(key, key)
