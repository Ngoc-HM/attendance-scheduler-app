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
        "schedule.override_date_out_of_month": "Override date must belong to the schedule month.",
        "schedule.cell_not_found": (
            "Schedule cell not found; a missing cell can only be added for an active user."
        ),
        "schedule.disabled_user_duty": (
            "Disabled account still has a working shift in the schedule; "
            "it does not count as cover."
        ),
        # --- Flights (F-04) ---
        "flight.day_not_found": "Flight day not found.",
        "flight.invalid_pairs": "flight_pairs must be 0, 1 or 2.",
        "flight.import_failed": "Excel import failed.",
        "flight.import_bad_file": "Unsupported or unreadable Excel file.",
        "flight.preset_not_found": "Flight preset not found.",
        "flight.import_row_invalid_date": "Row {row}: invalid date \"{value}\" (expected YYYY-MM-DD).",
        "flight.import_row_invalid_flt": "Row {row}: invalid FLT number \"{value}\".",
        "flight.import_row_invalid_time": "Row {row}: invalid time \"{value}\" (expected HH:MM).",
        "flight.import_row_route_too_long": "Row {row}: route is longer than {max} characters.",
        "flight.import_row_duplicate": "Row {row} repeats row {first_row} (same date and FLT {flt}); the later row is used.",
        # Monthly plan template (presets × days, F-04 owner 2026-11).
        "flight.template_no_presets": "Create a flight preset first.",
        "flight.template_month_label": "Month",
        "flight.template_instruction": (
            "Mark x on the days the flight operates. "
            "Do not edit columns A–C or the first 3 rows."
        ),
        "flight.template_col_preset": "Flight preset",
        "flight.template_col_arrival": "Arrival FLT",
        "flight.template_col_departure": "Departure FLT",
        "flight.template_weekdays": "Mon,Tue,Wed,Thu,Fri,Sat,Sun",
        "flight.plan_bad_month": (
            "Cell B1: invalid month \"{value}\" (expected YYYY-MM, year {min}–{max})."
        ),
        "flight.plan_layout_changed": (
            "The day columns of the template were changed; download the template again."
        ),
        "flight.plan_row_invalid_flt": "Row {row}: invalid FLT number \"{value}\" in column {col}.",
        "flight.plan_bad_mark": "Cell {cell}: \"{value}\" is not a valid mark (use x or leave it empty).",
        "flight.plan_duplicate_pair": "Row {row} repeats row {first_row} (FLT {arr}/{dep}).",
        "flight.plan_unknown_preset": "Row {row}: no flight preset {arr}/{dep} — create the preset first.",
        "flight.plan_too_many_presets": "{day}: more than {max} flight presets are marked.",
        "flight.plan_shared_flt": "{day}: two marked flight presets share FLT {flt}.",
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
        "swap.cell_locked": "Leave, comp, sick and admin-assigned days cannot be changed by request — only regular working or off days.",
        "swap.counterpart_self": "You cannot swap a shift with yourself.",
        "swap.counterpart_inactive": "That colleague's account is not active.",
        "swap.counterpart_other_role": "You can only swap with a colleague who works the same shift codes.",
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
            "Retention cutoff must be at least {months} months in the past "
            "(working-time records, ArbZG §16)."
        ),
        "user.delete_failed": "Deleting the user failed; nothing was changed.",
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
        "schedule.override_date_out_of_month": "Ngày chỉnh sửa phải thuộc tháng của lịch.",
        "schedule.cell_not_found": (
            "Không tìm thấy ô lịch; chỉ có thể thêm ô còn thiếu cho người dùng đang hoạt động."
        ),
        "schedule.disabled_user_duty": (
            "Tài khoản đã bị vô hiệu hoá vẫn còn ca làm việc trong lịch; "
            "ca này không được tính là người trực."
        ),
        # --- Flights (F-04) ---
        "flight.day_not_found": "Không tìm thấy ngày bay.",
        "flight.invalid_pairs": "Số cặp chuyến bay phải là 0, 1 hoặc 2.",
        "flight.import_failed": "Import Excel thất bại.",
        "flight.import_bad_file": "File Excel không hợp lệ hoặc không đọc được.",
        "flight.preset_not_found": "Không tìm thấy preset chuyến bay.",
        "flight.import_row_invalid_date": "Dòng {row}: ngày \"{value}\" không hợp lệ (định dạng YYYY-MM-DD).",
        "flight.import_row_invalid_flt": "Dòng {row}: số hiệu chuyến bay \"{value}\" không hợp lệ.",
        "flight.import_row_invalid_time": "Dòng {row}: giờ \"{value}\" không hợp lệ (định dạng HH:MM).",
        "flight.import_row_route_too_long": "Dòng {row}: tuyến bay dài quá {max} ký tự.",
        "flight.import_row_duplicate": "Dòng {row} trùng với dòng {first_row} (cùng ngày và chuyến {flt}); dùng dòng sau.",
        # Mẫu kế hoạch bay theo tháng (mẫu chuyến × ngày, F-04 owner 2026-11).
        "flight.template_no_presets": "Hãy tạo mẫu chuyến bay trước.",
        "flight.template_month_label": "Tháng",
        "flight.template_instruction": (
            "Đánh dấu x vào ngày có chuyến. Không sửa cột A–C và 3 hàng đầu."
        ),
        "flight.template_col_preset": "Mẫu chuyến bay",
        "flight.template_col_arrival": "Chuyến đến",
        "flight.template_col_departure": "Chuyến đi",
        "flight.template_weekdays": "T2,T3,T4,T5,T6,T7,CN",
        "flight.plan_bad_month": (
            "Ô B1: tháng \"{value}\" không hợp lệ (định dạng YYYY-MM, năm {min}–{max})."
        ),
        "flight.plan_layout_changed": (
            "Các cột ngày của file mẫu đã bị thay đổi; hãy tải lại file mẫu."
        ),
        "flight.plan_row_invalid_flt": "Dòng {row}: số hiệu chuyến bay \"{value}\" ở cột {col} không hợp lệ.",
        "flight.plan_bad_mark": "Ô {cell}: \"{value}\" không phải dấu hợp lệ (ghi x hoặc để trống).",
        "flight.plan_duplicate_pair": "Dòng {row} trùng với dòng {first_row} (chuyến {arr}/{dep}).",
        "flight.plan_unknown_preset": "Dòng {row}: chưa có mẫu chuyến bay {arr}/{dep} — hãy tạo mẫu trước.",
        "flight.plan_too_many_presets": "{day}: đánh dấu quá {max} mẫu chuyến bay.",
        "flight.plan_shared_flt": "{day}: hai mẫu chuyến bay được đánh dấu cùng có chuyến {flt}.",
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
        "swap.cell_locked": "Không thể yêu cầu đổi ngày nghỉ phép, nghỉ bù, ngày ốm hoặc ngày do admin gán — chỉ đổi được ngày làm hoặc ngày nghỉ thường.",
        "swap.counterpart_self": "Không thể hoán đổi ca với chính mình.",
        "swap.counterpart_inactive": "Tài khoản của đồng nghiệp này không còn hoạt động.",
        "swap.counterpart_other_role": "Chỉ được hoán đổi ca với đồng nghiệp làm cùng loại mã ca.",
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
            "Mốc xóa dữ liệu phải cách hiện tại ít nhất {months} tháng "
            "(hồ sơ giờ làm, ArbZG §16)."
        ),
        "user.delete_failed": "Xóa người dùng thất bại; chưa có thay đổi nào được lưu.",
    },
}


def t(key: str, lang: str | None = None) -> str:
    """Translate a message key; falls back to the key itself if missing.

    Language resolution: explicit arg > the request's Accept-Language
    (middleware) > DEFAULT_LANGUAGE.
    """
    language = lang or _request_language.get() or settings.DEFAULT_LANGUAGE
    return MESSAGES.get(language, MESSAGES["en"]).get(key, key)
