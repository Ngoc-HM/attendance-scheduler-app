import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';

class AppLocalizations {
  const AppLocalizations(this.locale);

  final Locale locale;

  static const supportedLocales = [Locale('en'), Locale('vi')];
  static const delegate = _AppLocalizationsDelegate();

  static AppLocalizations of(BuildContext context) =>
      Localizations.of<AppLocalizations>(context, AppLocalizations) ??
      const AppLocalizations(Locale('en'));

  bool get isVietnamese => locale.languageCode == 'vi';

  static const Map<String, Map<String, String>> _values = {
    'en': {
      'appTitle': 'Attendance & Scheduler',
      'productName': 'Roster FRA',
      'language': 'Language',
      'english': 'English',
      'vietnamese': 'Vietnamese',
      'login': 'Log in',
      'logout': 'Log out',
      'username': 'Username',
      'password': 'Password',
      'fieldRequired': 'Required',
      'navSchedule': 'Schedule',
      'navFlights': 'Flights',
      'navLeaves': 'Leaves',
      'navAttendance': 'Attendance',
      'navReports': 'Reports',
      'navUsers': 'Users',
      'register': 'Register',
      'createAccount': 'Create an account',
      'backToLogin': 'Back to login',
      'fullName': 'Full name',
      'role': 'Role',
      'minThreeChars': 'At least 3 characters',
      'minSixChars': 'At least 6 characters',
      'registerPending': 'Account created. Awaiting admin approval.',
      'registerFailed': 'Registration failed. The username may be taken.',
      'createUser': 'Create user',
      'createUserFailed': 'Could not create the user.',
      'cancel': 'Cancel',
      'create': 'Create',
      'refresh': 'Refresh',
      'loadFailed': 'Could not load users.',
      'noUsers': 'No users yet.',
      'status': 'Status',
      'actions': 'Actions',
      'approve': 'Approve',
      'approveRoleMessage':
          'Choose the role for this account before activating it. '
          'The account code follows the chosen role.',
      'disable': 'Disable',
      'enable': 'Enable',
      'changeRole': 'Change role',
      'changeRoleMessage':
          'The account code will be reassigned to match the new role '
          '(e.g. T2 → M3). The old code is never reused. Continue?',
      'confirm': 'Confirm',
      'reject': 'Reject',
      'retry': 'Retry',
      'download': 'Download',
      'signedIn': 'Signed in',
      'user': 'User',
      'previousMonth': 'Previous month',
      'nextMonth': 'Next month',
      'loginSubtitle': 'Use your approved account to continue.',
      'registerSubtitle': 'New accounts require administrator approval.',
      'loginFailedTitle': 'Login failed',
      'registrationFailedTitle': 'Registration failed',
      'authPanelSubtitle':
          'Monthly flight staffing and attendance for the Frankfurt team.',
      'authFeatureSchedule': 'Automatic monthly roster',
      'authFeatureBalance': 'Balanced ARR and DEP duties',
      'authFeatureAttendance': 'Attendance and leave control',
      'scheduleTitle': 'Schedule',
      'scheduleSubtitle': 'Monthly roster for the Frankfurt team',
      'publishSchedule': 'Publish schedule',
      'generateSchedule': 'Generate schedule',
      'employees': 'Employees',
      'arrDuties': 'ARR duties',
      'depDuties': 'DEP duties',
      'doubleDuties': 'A/D duties',
      'readyForReview': 'Ready for review',
      'scheduleReviewMessage':
          'Hard constraints pass. Review shift balance before publishing.',
      'monthlyRoster': 'Monthly roster',
      'employee': 'Employee',
      'off': 'Off',
      'doubleDuty': 'Double duty',
      'doubleDutyNoComp': 'Double duty (no comp)',
      'officeDuty': 'Office duty',
      'training': 'Training',
      'businessTrip': 'Business trip',
      'compensation': 'Compensation',
      'leave': 'Leave',
      'sick': 'Sick',
      'flightsTitle': 'Flights',
      'flightsSubtitle': 'STA and STD use Frankfurt local time',
      'importExcel': 'Import Excel',
      'addFlight': 'Add flight',
      'flightDays': 'Flight days',
      'flightPairs': 'Flight pairs',
      'twoPairDays': 'Two-pair days',
      'flightPlan': 'Flight plan',
      'date': 'Date',
      'pairs': 'Pairs',
      'flights': 'Flights',
      'importMonthlyFlights': 'Import monthly flights',
      'excelFileHint': 'Excel files up to 10 MB',
      'chooseFile': 'Choose file',
      'leaveRequests': 'Leave requests',
      'leaveSubtitle':
          'Monthly leave: register by day {day} of the previous month. '
          'Annual leave: register the year before.',
      'requestMonthlyLeave': 'Request monthly leave',
      'requestAnnualLeave': 'Request annual leave',
      'pending': 'Pending',
      'approved': 'Approved',
      'rejected': 'Rejected',
      'active': 'Active',
      'disabled': 'Disabled',
      'review': 'Review',
      'compDays': 'Comp days',
      'registrationOpen': 'Registration open',
      'shortLeaveMessage':
          'Monthly leave is 5 consecutive days or fewer. Longer leave uses the annual request.',
      'monthlyLeaveHint': 'Monthly leave is 5 consecutive days or fewer.',
      'annualLeaveHint': 'Annual leave is more than 5 consecutive days, limited to the next year (Y+1).',
      'leaveTypeSpanMismatch':
          'Leave of 5 days or less is monthly leave; more than 5 consecutive days must be registered as annual leave.',

      'leaveWindowHint':
          'Monthly leave: register during the previous month. '
          'Annual leave: register the year before.',
      'requests': 'Requests',
      'type': 'Type',
      'dates': 'Dates',
      'days': 'Days',
      'carry': 'Carry',
      'monthlyLeave': 'Monthly leave',
      'annualLeave': 'Annual leave',
      'leaveType': 'Leave type',
      'dateRange': 'Date range',
      'note': 'Note',
      'submitRequest': 'Submit request',
      'attendanceTitle': 'Attendance',
      'attendanceSubtitle': 'Actual daily status and public holidays',
      'publicHolidays': 'Public holidays',
      'updateAttendance': 'Update attendance',
      'workdays': 'Workdays',
      'absences': 'Absences',
      'sickDays': 'Sick days',
      'restrictedHealthData': 'Restricted health data',
      'healthDataMessage':
          'Sick status is visible to administrators only. Do not record medical details.',
      'attendanceBoard': 'Attendance board',
      'attendanceEmptyTitle': 'No attendance yet',
      'attendanceEmptyMessage':
          'No records for this month. Tap "Update attendance" to get started.',
      'work': 'Work',
      'absent': 'Absent',
      'reportsTitle': 'Reports',
      'reportsSubtitle': 'Attendance exports by month and year',
      'exportYear': 'Export year',
      'exportMonth': 'Export month',
      'reports': 'Reports',
      'formats': 'Formats',
      'retention': 'Retention',
      'flexibleExportFormat': 'Flexible export format',
      'exportFormatMessage':
          'The final customer report layout is not fixed yet. Exports remain modular.',
      'recentExports': 'Recent exports',
      'report': 'Report',
      'period': 'Period',
      'updated': 'Updated',
      'action': 'Action',
      'monthlyAttendance': 'Monthly attendance',
      'annualAttendance': 'Annual attendance',
      'usersTitle': 'Users',
      'usersSubtitle': 'Accounts, roles and approvals',
      'fixedTeam': 'Fixed team',
      'couldNotLoadUsers': 'Could not load users',
      'createFirstAccount': 'Create the first account and assign a role.',
      'couldNotCreateUser': 'Could not create user',
      'scheduleGenerationRequested':
          'Schedule generation will use the solver API.',
      'scheduleReadyPublish': 'Schedule marked ready to publish.',
      'excelImportRequested':
          'Excel import will be connected to the flight API.',
      'flightFormOpened': 'Flight entry form opened.',
      'requestApproved': 'Request approved.',
      'requestRejected': 'Request rejected.',
      'leaveSubmitted': 'Leave request submitted.',
      'attendanceEditRequested':
          'Attendance editing will be connected to the attendance API.',
      'holidaysOpened': 'Public holiday management opened.',
      'monthlyExportRequested': 'Monthly export requested.',
      'annualExportRequested': 'Annual export requested.',
      'reportDownloadRequested': 'Report download requested.',
      'authIncorrectCredentials': 'Incorrect username or password.',
      'authServerUnavailable':
          'Cannot reach the server. Check the configured backend URL.',
      'authHttpFailure': 'Login failed because the server returned an error.',
      'authUnknownFailure': 'Login failed because of an unexpected error.',
      'authSessionExpired': 'Your session has expired. Please log in again.',
      // --- Phase 09 wiring: flights / leaves / reports / schedule / attendance
      'addFlightDay': 'Add flight day',
      'addHoliday': 'Add holiday',
      'allYear': 'Full year',
      'attendanceUpdated': 'Attendance updated.',
      'autoAssignCover': 'Auto-assign A/D cover',
      'changeCode': 'Change code',
      'dayOfMonth': 'Day of month',
      'delete': 'Delete',
      'endDate': 'End date',
      'exportOptions': 'Export options',
      'flightDaySaved': 'Flight day saved.',
      'flightPairsCount': 'Flight pairs (0 / 1 / 2)',
      'flightsImportSuccess': 'Flights imported successfully.',
      'flightsLoadFailed': 'Could not load flight data.',
      'holidayAdded': 'Holiday saved.',
      'holidayName': 'Holiday name',
      'latestExport': 'Latest export',
      'leavesLoadFailed': 'Could not load leave requests.',
      'newShiftCode': 'New shift code',
      'noHolidaysYet': 'No holidays yet.',
      'noPendingShiftChanges': 'No pending shift-change requests.',
      'pendingShiftChanges': 'Pending shift-change requests',
      'myShiftChangeRequests': 'My shift-change requests',
      'noShiftChangeRequests':
          'No requests yet. Tap one of your own cells in the roster to request a change.',
      'shiftChangeSubmitted': 'Shift-change request submitted.',
      'shiftChangesLoadFailed': 'Could not load your shift-change requests.',
      'shiftCodeColumn': 'Code',
      'pickDate': 'Pick a date',
      'reportSavedTo': 'Report saved to',
      'requestShiftChange': 'Request shift change',
      'save': 'Save',
      'scheduleEmptyTitle': 'No roster yet',
      'scheduleEmptyMessage':
          'No schedule for this month. Tap "Generate schedule" to build one.',
      'scheduleGenerated': 'Schedule generated.',
      'ruleWarnings': 'rule warning(s).',
      'scheduleInfeasible': 'No valid schedule could be found.',
      'regenerate': 'Regenerate',
      'scheduleNotPublishedYet':
          'The schedule for this month is not published yet.',
      'schedulePublished': 'Schedule published.',
      'selectColleague': 'Select a colleague',
      'selectEmployee': 'Select an employee',
      'shiftChangeRequests': 'Shift-change requests',
      'sickCoverAssigned': 'Sick day recorded; A/D cover assigned.',
      'sickCoverNoneAvailable':
          'Sick day recorded; no eligible colleague for cover — resolve manually.',
      'startDate': 'Start date',
      'strictReviewRequired': 'Strict review (fixed role)',
      'swapWith': 'Swap with colleague',
      // --- Flight preset feature
      'flightPresets': 'Flight Presets',
      'addPreset': 'Add preset',
      'editPreset': 'Edit preset',
      'presetLabel': 'Label',
      'presetRoute': 'Route (optional)',
      'fltArr': 'FLT arrival',
      'fltDep': 'FLT departure',
      'sta': 'STA',
      'std': 'STD',
      'sortOrder': 'Sort order',
      'isActive': 'Active',
      'edit': 'Edit',
      'noPresetsYet': 'No presets yet',
      'noPresetsMessage':
          'Create reusable flight presets here. Then click a day on the flight calendar to apply them.',
      'presetSaved': 'Preset saved.',
      'presetDeleted': 'Preset deleted.',
      'deletePresetConfirm': 'Delete preset',
      'managePresets': 'Manage presets',
      'selectPresets': 'Select presets',
      'selectPresetsHint': 'Choose up to 2 presets for this day.',
      'applyFlights': 'Apply',
      // --- Month batch dialog
      'fillMonth': 'Fill whole month',
      'monthFlightsTitle': 'Fill whole month',
      'monthFlightsHint':
          'Tick presets per day. Up to 2 per row. Only changed days are saved.',
      'monthFlightsLoading': 'Presets are loading — please try again.',
      'monthFlightsSaved': 'Month flights saved.',
      'selectAllColumn': 'Select all',
      'applyMonth': 'Apply whole month',
      'columnDay': 'Day',
      'columnWeekday': 'Wday',
      // --- Employee shell (owner 2026-07-09) ---
      'navSelfArrange': 'Self-arrange',
      'navClock': 'Check-in/out',
      // --- Time clock ---
      'clockTitle': 'Check-in / Check-out',
      'clockCheckIn': 'Check-in',
      'clockCheckOut': 'Check-out',
      'clockCheckedInAt': 'Checked in at',
      'clockCheckedOutAt': 'Checked out at',
      'clockNotCheckedIn': 'Not checked in yet today.',
      'clockHistory': 'This month',
      'clockNoEntries': 'No entries this month yet.',
      'clockActionFailed': 'Action failed.',
      // --- Self-arrange ---
      'selfArrangeTitle': 'Self-arrange shifts',
      'selfArrangeHint':
          'Tap your own cells to swap work/off. Every 7-day block must keep '
          'exactly its required off days. Changes apply after admin approval.',
      'selfArrangeSubmit': 'Submit for approval',
      'selfArrangeNote': 'Note (optional)',
      'selfArrangeSubmitted': 'Request submitted — waiting for admin approval.',
      'selfArrangeQuotaBroken':
          'A 7-day block would not keep its required off days.',
      'selfArrangeNoDraft': 'No changes yet.',
      'selfArrangeDiscard': 'Discard draft',
      'selfArrangeHistory': 'My requests',
      'selfArrangePanelTitle': 'Pending self-arrange requests',
      'selfArrangeChanges': 'changes',
      'selfArrangeMonthCap': 'Only up to 2 months ahead can be viewed.',
      'selfArrangeSubmitFailed': 'Submitting the request failed.',
      'selfArrangeDecided': 'Request decided.',
      // --- Generate guard (owner 2026-07-17) ---
      'flightsMissingTitle': 'No flight data for this month',
      'flightsMissingBody':
          'No flights have been entered for this month yet, so the generated '
          'roster will contain no flight duties (A/D) and may be wrong. '
          'Enter flights first, or generate anyway?',
      'generateAnyway': 'Generate anyway',
      'regenerateConfirmTitle': 'Regenerate schedule?',
      'regenerateConfirmBody':
          'This schedule is published or has manual edits. Regenerating will '
          'discard the manual edits and return the schedule to draft. '
          'Employees lose access to this month until it is published again.',
      // --- Admin cell edit (F-09 UI, owner 2026-07-17) ---
      'editCell': 'Edit cell',
      'cellSaved': 'Cell saved.',
      // --- Busy overlays (owner 2026-07-18) ---
      'generatingSchedule': 'Generating schedule, please wait…',
      'publishingSchedule': 'Publishing schedule…',
      // --- Leave window banner (audit fix 2026-07-17) ---
      'registrationClosed': 'Monthly registration closed',
      'registrationClosedMessage':
          'Registration of monthly leave for next month has closed for this '
          'month. Annual leave (more than 5 days) is registered during the '
          'previous year.',
      // --- Revoke approval (owner 2026-07-17) ---
      'revokeApproval': 'Revoke approval',
      'revokeConfirmMessage':
          'This returns the leave days to the employee\'s balance and marks '
          'the request as rejected. If the month was already scheduled, '
          'regenerate it afterwards.',
      'requestRevoked': 'Approval revoked.',
      // --- User management guards (CSV TC-005/006/007/008) ---
      'usernameTaken': 'That username is already taken.',
      'lastAdminWarning':
          'You are about to act on the last remaining admin. This action cannot proceed.',
      'lastAdminDialogMessage':
          'This account is the last active admin. You cannot change its role '
          'or disable it, otherwise no admin would remain.',
      'selfActionWarning':
          'You are about to change your own account. Confirm to continue.',
      'confirmDeleteUser': 'Delete this user?',
      'deleteUserWarning':
          'All attendance, leave and shift history for this user will be '
          'permanently deleted. This cannot be undone.',
      'userDeleted': 'User deleted.',
      'fixedTeamWarning':
          'No active fixed-team members will remain after this change.',
      'fixedTeamDialogMessage':
          'No active fixed-team members will remain after this change. Continue?',
      // --- F-04 Excel import ---
      'importExcelSuccess': 'Imported {count} flights from Excel.',
      'importExcelFailed': 'Could not import the Excel file.',
      'importExcelHint': 'Choose an .xlsx file of at most 2 MB.',
      // --- F-14 month close / carry-over ---
      'close': 'Close',
      'closeMonth': 'Close month',
      'closeMonthConfirmTitle': 'Close {month}?',
      'closeMonthConfirmMessage':
          'Carry-over balances (comp days, working streak, premium off) are '
          'computed from this month\'s attendance and stored for the next '
          'schedule.',
      'closeMonthResultTitle': 'Month closed — carry-over balances',
      'closeMonthEmpty': 'The backend returned no carry-over balances.',
      'closeMonthFailed': 'Could not close the month.',
      'carryComp': 'Comp days',
      'carryStreak': 'Working streak',
      'carryPremiumOff': 'Premium off',
      // --- My attendance, leave window, i18n cleanup (review 2026-11-06) ---
      'navMyAttendance': 'My attendance',
      'myAttendanceEmptyMessage':
          'No records for this month yet. They appear once the roster is '
          'published.',
      'userFallback': 'ID {id}',
      'selectYearMonthFirst': 'Select a year and month first.',
      'selectYearFirst': 'Select a year first.',
      'statusReady': 'Ready',
      'statusComplete': 'Complete',
      // --- Annual leave quota (owner decision D4, 2026-11-06) ---
      'annualLeaveRemaining': 'Annual leave left',
      'annualLeaveQuota': 'Annual leave quota',
      'annualLeaveQuotaHint': 'Days per year — leave empty for the default',
      'annualLeaveQuotaInvalid': 'Enter a whole number from 0 to 365.',
      'editAnnualLeaveQuota': 'Edit leave quota',
      'annualLeaveQuotaUpdated': 'Annual leave quota updated.',
      // --- Schedule screen (review 2026-11-08: A3, C2, D3) ---
      'scheduleLoadFailed': 'Could not load the schedule:',
      'actionFailed': 'The action could not be completed.',
      'checkingRules': 'Checking the rules…',
      'ruleViolationsInMonth':
          'rule violation(s) in this month. Review them before publishing.',
      'publishWithViolationsTitle': 'Publish with rule violations?',
      'publishWithViolationsBody':
          'This month still breaks these rules. Publish anyway?',
      'rulesCheckFailed':
          'The rules could not be checked right now. Publish anyway?',
      'publishAnyway': 'Publish anyway',
      'approvedWithWarnings': 'Request approved, with rule warnings',
      'swapPartner': 'Swap partner',
    },
    'vi': {
      'appTitle': 'Xếp lịch & Chấm công',
      'productName': 'Lịch FRA',
      'language': 'Ngôn ngữ',
      'english': 'Tiếng Anh',
      'vietnamese': 'Tiếng Việt',
      'login': 'Đăng nhập',
      'logout': 'Đăng xuất',
      'username': 'Tên đăng nhập',
      'password': 'Mật khẩu',
      'fieldRequired': 'Bắt buộc',
      'navSchedule': 'Lịch làm',
      'navFlights': 'Chuyến bay',
      'navLeaves': 'Nghỉ phép',
      'navAttendance': 'Chấm công',
      'navReports': 'Báo cáo',
      'navUsers': 'Người dùng',
      'register': 'Đăng ký',
      'createAccount': 'Tạo tài khoản',
      'backToLogin': 'Quay lại đăng nhập',
      'fullName': 'Họ và tên',
      'role': 'Vai trò',
      'minThreeChars': 'Tối thiểu 3 ký tự',
      'minSixChars': 'Tối thiểu 6 ký tự',
      'registerPending': 'Đã tạo tài khoản. Đang chờ quản trị viên phê duyệt.',
      'registerFailed': 'Đăng ký thất bại. Tên đăng nhập có thể đã tồn tại.',
      'createUser': 'Tạo người dùng',
      'createUserFailed': 'Không thể tạo người dùng.',
      'cancel': 'Hủy',
      'create': 'Tạo',
      'refresh': 'Tải lại',
      'loadFailed': 'Không thể tải danh sách người dùng.',
      'noUsers': 'Chưa có người dùng.',
      'status': 'Trạng thái',
      'actions': 'Thao tác',
      'approve': 'Phê duyệt',
      'approveRoleMessage':
          'Chọn vai trò cho tài khoản trước khi kích hoạt. '
          'Mã tài khoản sẽ theo vai trò được chọn.',
      'disable': 'Vô hiệu hóa',
      'enable': 'Kích hoạt',
      'changeRole': 'Đổi vai trò',
      'changeRoleMessage':
          'Mã tài khoản sẽ được cấp lại theo vai trò mới '
          '(vd: T2 → M3). Mã cũ không dùng lại. Tiếp tục?',
      'confirm': 'Xác nhận',
      'reject': 'Từ chối',
      'retry': 'Thử lại',
      'download': 'Tải xuống',
      'signedIn': 'Đã đăng nhập',
      'user': 'Người dùng',
      'previousMonth': 'Tháng trước',
      'nextMonth': 'Tháng sau',
      'loginSubtitle': 'Sử dụng tài khoản đã được phê duyệt để tiếp tục.',
      'registerSubtitle': 'Tài khoản mới cần quản trị viên phê duyệt.',
      'loginFailedTitle': 'Đăng nhập thất bại',
      'registrationFailedTitle': 'Đăng ký thất bại',
      'authPanelSubtitle':
          'Phân lịch chuyến bay và chấm công hàng tháng cho đội Frankfurt.',
      'authFeatureSchedule': 'Tự động xếp lịch tháng',
      'authFeatureBalance': 'Cân bằng ca ARR và DEP',
      'authFeatureAttendance': 'Quản lý chấm công và nghỉ phép',
      'scheduleTitle': 'Lịch làm',
      'scheduleSubtitle': 'Lịch làm hàng tháng của đội Frankfurt',
      'publishSchedule': 'Công bố lịch',
      'generateSchedule': 'Tạo lịch tự động',
      'employees': 'Nhân sự',
      'arrDuties': 'Ca ARR',
      'depDuties': 'Ca DEP',
      'doubleDuties': 'Ca A/D',
      'readyForReview': 'Sẵn sàng rà soát',
      'scheduleReviewMessage':
          'Các ràng buộc cứng đã đạt. Hãy kiểm tra cân bằng ca trước khi công bố.',
      'monthlyRoster': 'Lịch làm tháng',
      'employee': 'Nhân sự',
      'off': 'Nghỉ',
      'doubleDuty': 'Ca kép',
      'doubleDutyNoComp': 'Ca kép (không bù)',
      'officeDuty': 'Văn phòng',
      'training': 'Đào tạo',
      'businessTrip': 'Công tác',
      'compensation': 'Nghỉ bù',
      'leave': 'Nghỉ phép',
      'sick': 'Nghỉ ốm',
      'flightsTitle': 'Chuyến bay',
      'flightsSubtitle': 'STA và STD theo giờ địa phương Frankfurt',
      'importExcel': 'Nhập Excel',
      'addFlight': 'Thêm chuyến bay',
      'flightDays': 'Ngày bay',
      'flightPairs': 'Cặp chuyến',
      'twoPairDays': 'Ngày 2 cặp',
      'flightPlan': 'Kế hoạch bay',
      'date': 'Ngày',
      'pairs': 'Số cặp',
      'flights': 'Chuyến bay',
      'importMonthlyFlights': 'Nhập lịch bay tháng',
      'excelFileHint': 'Tệp Excel tối đa 10 MB',
      'chooseFile': 'Chọn tệp',
      'leaveRequests': 'Đăng ký nghỉ',
      'leaveSubtitle':
          'Nghỉ tháng: đăng ký chậm nhất đến hết ngày {day} của tháng trước. '
          'Nghỉ phép năm: đăng ký từ năm trước.',
      'requestMonthlyLeave': 'Đăng ký nghỉ tháng',
      'requestAnnualLeave': 'Đăng ký nghỉ phép năm',
      'pending': 'Chờ duyệt',
      'approved': 'Đã duyệt',
      'rejected': 'Đã từ chối',
      'active': 'Đang hoạt động',
      'disabled': 'Đã vô hiệu hóa',
      'review': 'Cần rà soát',
      'compDays': 'Ngày nghỉ bù',
      'registrationOpen': 'Đang mở đăng ký',
      'shortLeaveMessage':
          'Nghỉ hàng tháng từ 5 ngày liên tục trở xuống. Nghỉ dài hơn dùng đăng ký phép năm.',
      'monthlyLeaveHint': 'Nghỉ hàng tháng từ 5 ngày liên tục trở xuống.',
      'annualLeaveHint': 'Nghỉ phép năm trên 5 ngày liên tục, chỉ được đăng ký năm sau (Y+1).',
      'leaveTypeSpanMismatch':
          'Nghỉ từ 5 ngày trở xuống là nghỉ tháng; trên 5 ngày liên tục phải đăng ký nghỉ phép năm.',

      'leaveWindowHint':
          'Nghỉ tháng: đăng ký trong tháng trước. '
          'Nghỉ phép năm: đăng ký từ năm trước.',
      'requests': 'Yêu cầu',
      'type': 'Loại',
      'dates': 'Thời gian',
      'days': 'Số ngày',
      'carry': 'Tồn bù',
      'monthlyLeave': 'Nghỉ hàng tháng',
      'annualLeave': 'Nghỉ phép năm',
      'leaveType': 'Loại nghỉ',
      'dateRange': 'Khoảng ngày',
      'note': 'Ghi chú',
      'submitRequest': 'Gửi yêu cầu',
      'attendanceTitle': 'Chấm công',
      'attendanceSubtitle': 'Trạng thái thực tế hàng ngày và ngày lễ',
      'publicHolidays': 'Ngày lễ',
      'updateAttendance': 'Cập nhật chấm công',
      'workdays': 'Ngày công',
      'absences': 'Ngày nghỉ',
      'sickDays': 'Ngày ốm',
      'restrictedHealthData': 'Dữ liệu sức khỏe hạn chế',
      'healthDataMessage':
          'Trạng thái nghỉ ốm chỉ hiển thị cho quản trị viên. Không ghi chi tiết y tế.',
      'attendanceBoard': 'Bảng chấm công',
      'attendanceEmptyTitle': 'Chưa có chấm công',
      'attendanceEmptyMessage':
          'Chưa có dữ liệu cho tháng này. Bấm "Cập nhật chấm công" để bắt đầu.',
      'work': 'Đi làm',
      'absent': 'Vắng',
      'reportsTitle': 'Báo cáo',
      'reportsSubtitle': 'Xuất chấm công theo tháng và năm',
      'exportYear': 'Xuất năm',
      'exportMonth': 'Xuất tháng',
      'reports': 'Báo cáo',
      'formats': 'Định dạng',
      'retention': 'Lưu trữ',
      'flexibleExportFormat': 'Định dạng xuất linh hoạt',
      'exportFormatMessage':
          'Bố cục báo cáo cuối cùng chưa chốt. Các định dạng xuất vẫn được tách mô-đun.',
      'recentExports': 'Bản xuất gần đây',
      'report': 'Báo cáo',
      'period': 'Kỳ',
      'updated': 'Cập nhật',
      'action': 'Thao tác',
      'monthlyAttendance': 'Chấm công tháng',
      'annualAttendance': 'Chấm công năm',
      'usersTitle': 'Người dùng',
      'usersSubtitle': 'Tài khoản, vai trò và phê duyệt',
      'fixedTeam': 'Nhóm cố định',
      'couldNotLoadUsers': 'Không thể tải người dùng',
      'createFirstAccount': 'Tạo tài khoản đầu tiên và gán vai trò.',
      'couldNotCreateUser': 'Không thể tạo người dùng',
      'scheduleGenerationRequested':
          'Việc tạo lịch sẽ sử dụng API của bộ giải.',
      'scheduleReadyPublish': 'Lịch đã sẵn sàng để công bố.',
      'excelImportRequested': 'Nhập Excel sẽ được kết nối với API chuyến bay.',
      'flightFormOpened': 'Đã mở biểu mẫu chuyến bay.',
      'requestApproved': 'Đã phê duyệt yêu cầu.',
      'requestRejected': 'Đã từ chối yêu cầu.',
      'leaveSubmitted': 'Đã gửi yêu cầu nghỉ.',
      'attendanceEditRequested':
          'Chỉnh sửa chấm công sẽ được kết nối với API chấm công.',
      'holidaysOpened': 'Đã mở quản lý ngày lễ.',
      'monthlyExportRequested': 'Đã yêu cầu xuất báo cáo tháng.',
      'annualExportRequested': 'Đã yêu cầu xuất báo cáo năm.',
      'reportDownloadRequested': 'Đã yêu cầu tải báo cáo.',
      'authIncorrectCredentials': 'Tên đăng nhập hoặc mật khẩu không đúng.',
      'authServerUnavailable':
          'Không thể kết nối máy chủ. Hãy kiểm tra URL backend.',
      'authHttpFailure': 'Đăng nhập thất bại do máy chủ trả về lỗi.',
      'authUnknownFailure': 'Đăng nhập thất bại do lỗi không xác định.',
      'authSessionExpired':
          'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.',
      // --- Phase 09 wiring: flights / leaves / reports / schedule / attendance
      'addFlightDay': 'Thêm ngày bay',
      'addHoliday': 'Thêm ngày lễ',
      'allYear': 'Cả năm',
      'attendanceUpdated': 'Đã cập nhật chấm công.',
      'autoAssignCover': 'Tự gán người bù ca A/D',
      'changeCode': 'Đổi mã ca',
      'dayOfMonth': 'Ngày trong tháng',
      'delete': 'Xóa',
      'endDate': 'Ngày kết thúc',
      'exportOptions': 'Tùy chọn xuất',
      'flightDaySaved': 'Đã lưu ngày bay.',
      'flightPairsCount': 'Số cặp chuyến (0 / 1 / 2)',
      'flightsImportSuccess': 'Đã nhập chuyến bay thành công.',
      'flightsLoadFailed': 'Không thể tải dữ liệu chuyến bay.',
      'holidayAdded': 'Đã lưu ngày lễ.',
      'holidayName': 'Tên ngày lễ',
      'latestExport': 'Bản xuất mới nhất',
      'leavesLoadFailed': 'Không thể tải danh sách nghỉ phép.',
      'newShiftCode': 'Mã ca mới',
      'noHolidaysYet': 'Chưa có ngày lễ nào.',
      'noPendingShiftChanges': 'Không có yêu cầu đổi ca chờ duyệt.',
      'pendingShiftChanges': 'Yêu cầu đổi ca chờ duyệt',
      'myShiftChangeRequests': 'Yêu cầu đổi ca của tôi',
      'noShiftChangeRequests':
          'Chưa có yêu cầu nào. Nhấn vào một ô của bạn trên lịch để yêu cầu đổi ca.',
      'shiftChangeSubmitted': 'Đã gửi yêu cầu đổi ca.',
      'shiftChangesLoadFailed': 'Không thể tải các yêu cầu đổi ca của bạn.',
      'shiftCodeColumn': 'Mã ca',
      'pickDate': 'Chọn ngày',
      'reportSavedTo': 'Báo cáo đã lưu tại',
      'requestShiftChange': 'Yêu cầu đổi ca',
      'save': 'Lưu',
      'scheduleEmptyTitle': 'Chưa có lịch',
      'scheduleEmptyMessage':
          'Chưa có lịch cho tháng này. Nhấn "Tạo lịch" để bắt đầu.',
      'scheduleGenerated': 'Đã tạo lịch.',
      'ruleWarnings': 'cảnh báo quy tắc.',
      'scheduleInfeasible': 'Không tìm được lời giải hợp lệ cho lịch.',
      'regenerate': 'Tạo lại',
      'scheduleNotPublishedYet': 'Lịch tháng này chưa được công bố.',
      'schedulePublished': 'Đã công bố lịch.',
      'selectColleague': 'Chọn đồng nghiệp',
      'selectEmployee': 'Chọn nhân sự',
      'shiftChangeRequests': 'Yêu cầu đổi ca',
      'sickCoverAssigned': 'Đã ghi nhận nghỉ ốm; đã gán người bù ca A/D.',
      'sickCoverNoneAvailable':
          'Đã ghi nhận nghỉ ốm; không có đồng nghiệp phù hợp để bù — xử lý tay.',
      'startDate': 'Ngày bắt đầu',
      'strictReviewRequired': 'Xét duyệt chặt (nhóm cố định)',
      'swapWith': 'Hoán đổi với đồng nghiệp',
      // --- Flight preset feature
      'flightPresets': 'Mẫu chuyến bay',
      'addPreset': 'Thêm mẫu',
      'editPreset': 'Sửa mẫu',
      'presetLabel': 'Tên mẫu',
      'presetRoute': 'Tuyến bay (tuỳ chọn)',
      'fltArr': 'Chuyến đến',
      'fltDep': 'Chuyến đi',
      'sta': 'STA',
      'std': 'STD',
      'sortOrder': 'Thứ tự',
      'isActive': 'Đang dùng',
      'edit': 'Sửa',
      'noPresetsYet': 'Chưa có mẫu nào',
      'noPresetsMessage':
          'Tạo mẫu chuyến bay dùng lại tại đây. Sau đó nhấn vào ngày trên lịch để áp dụng.',
      'presetSaved': 'Đã lưu mẫu chuyến bay.',
      'presetDeleted': 'Đã xóa mẫu chuyến bay.',
      'deletePresetConfirm': 'Xóa mẫu',
      'managePresets': 'Quản lý mẫu',
      'selectPresets': 'Chọn mẫu chuyến bay',
      'selectPresetsHint': 'Chọn tối đa 2 mẫu cho ngày này.',
      'applyFlights': 'Áp dụng',
      // --- Month batch dialog
      'fillMonth': 'Điền cả tháng',
      'monthFlightsTitle': 'Điền cả tháng',
      'monthFlightsHint':
          'Tick mẫu cho từng ngày. Tối đa 2 mẫu mỗi hàng. Chỉ lưu ngày có thay đổi.',
      'monthFlightsLoading': 'Đang tải mẫu — vui lòng thử lại.',
      'monthFlightsSaved': 'Đã lưu chuyến bay cả tháng.',
      'selectAllColumn': 'Chọn tất cả',
      'applyMonth': 'Áp dụng cả tháng',
      'columnDay': 'Ngày',
      'columnWeekday': 'Thứ',
      // --- Employee shell (owner 2026-07-09) ---
      'navSelfArrange': 'Tự sắp ca',
      'navClock': 'Chấm công vào/ra',
      // --- Time clock ---
      'clockTitle': 'Chấm công vào / ra',
      'clockCheckIn': 'Check-in',
      'clockCheckOut': 'Check-out',
      'clockCheckedInAt': 'Đã check-in lúc',
      'clockCheckedOutAt': 'Đã check-out lúc',
      'clockNotCheckedIn': 'Hôm nay chưa check-in.',
      'clockHistory': 'Trong tháng',
      'clockNoEntries': 'Chưa có dữ liệu trong tháng.',
      'clockActionFailed': 'Thao tác thất bại.',
      // --- Self-arrange ---
      'selfArrangeTitle': 'Tự sắp xếp ca',
      'selfArrangeHint':
          'Chạm vào ô của bạn để đổi làm/nghỉ. Mỗi block 7 ngày phải giữ đúng '
          'số ngày nghỉ quy định. Thay đổi có hiệu lực sau khi admin duyệt.',
      'selfArrangeSubmit': 'Gửi admin duyệt',
      'selfArrangeNote': 'Ghi chú (không bắt buộc)',
      'selfArrangeSubmitted': 'Đã gửi yêu cầu — chờ admin duyệt.',
      'selfArrangeQuotaBroken':
          'Có block 7 ngày không giữ đúng số ngày nghỉ quy định.',
      'selfArrangeNoDraft': 'Chưa có thay đổi.',
      'selfArrangeDiscard': 'Huỷ nháp',
      'selfArrangeHistory': 'Yêu cầu của tôi',
      'selfArrangePanelTitle': 'Yêu cầu tự sắp ca chờ duyệt',
      'selfArrangeChanges': 'thay đổi',
      'selfArrangeMonthCap': 'Chỉ xem được tối đa 2 tháng tương lai.',
      'selfArrangeSubmitFailed': 'Gửi yêu cầu thất bại.',
      'selfArrangeDecided': 'Đã quyết định yêu cầu.',
      // --- Generate guard (owner 2026-07-17) ---
      'flightsMissingTitle': 'Tháng này chưa nhập lịch bay',
      'flightsMissingBody':
          'Chưa có chuyến bay nào được nhập cho tháng này, nên lịch tạo ra sẽ '
          'không có ca bay (A/D) và có thể sai sót. Nên nhập lịch bay '
          'trước, hoặc vẫn tạo lịch?',
      'generateAnyway': 'Vẫn tạo lịch',
      'regenerateConfirmTitle': 'Tạo lại lịch?',
      'regenerateConfirmBody':
          'Lịch đã publish hoặc đã chỉnh tay. Tạo lại sẽ xoá chỉnh tay và '
          'đưa lịch về nháp. Nhân viên sẽ không xem được lịch tháng này '
          'cho đến khi lịch được công bố lại.',
      // --- Admin cell edit (F-09 UI, owner 2026-07-17) ---
      'editCell': 'Sửa ô lịch',
      'cellSaved': 'Đã lưu ô lịch.',
      // --- Busy overlays (owner 2026-07-18) ---
      'generatingSchedule': 'Đang tạo lịch, vui lòng đợi…',
      'publishingSchedule': 'Đang công bố lịch…',
      // --- Leave window banner (audit fix 2026-07-17) ---
      'registrationClosed': 'Đã đóng đăng ký nghỉ tháng',
      'registrationClosedMessage':
          'Tháng này đã hết hạn đăng ký nghỉ cho tháng kế tiếp. '
          'Nghỉ phép năm (trên 5 ngày) đăng ký trong năm trước.',
      // --- Revoke approval (owner 2026-07-17) ---
      'revokeApproval': 'Hủy duyệt',
      'revokeConfirmMessage':
          'Thao tác này hoàn lại ngày phép cho nhân viên và chuyển đơn về '
          'Từ chối. Nếu tháng liên quan đã tạo lịch, hãy tạo lại lịch '
          'sau khi hủy.',
      'requestRevoked': 'Đã hủy duyệt.',
      // --- User management guards (CSV TC-005/006/007/008) ---
      'usernameTaken': 'Tên đăng nhập đã tồn tại.',
      'lastAdminWarning':
          'Bạn sắp thao tác lên admin cuối cùng. Thao tác này không thể tiếp tục.',
      'lastAdminDialogMessage':
          'Tài khoản này là admin đang hoạt động cuối cùng. Bạn không thể đổi '
          'quyền hoặc vô hiệu hoá, nếu không sẽ không còn admin nào.',
      'selfActionWarning': 'Bạn sắp thay đổi chính tài khoản của mình. Xác nhận để tiếp tục.',
      'confirmDeleteUser': 'Xóa người dùng này?',
      'deleteUserWarning':
          'Toàn bộ lịch sử chấm công, nghỉ phép và ca làm của người dùng '
          'sẽ bị xoá vĩnh viễn. Không thể hoàn tác.',
      'userDeleted': 'Đã xóa người dùng.',
      'fixedTeamWarning':
          'Sẽ không còn thành viên fixed team nào đang hoạt động sau thay đổi này.',
      'fixedTeamDialogMessage':
          'Sẽ không còn thành viên fixed team nào đang hoạt động sau thay đổi này. Tiếp tục?',
      // --- F-04 Excel import ---
      'importExcelSuccess': 'Đã nhập {count} chuyến bay từ Excel.',
      'importExcelFailed': 'Không thể nhập tệp Excel.',
      'importExcelHint': 'Chọn tệp .xlsx có dung lượng tối đa 2 MB.',
      // --- F-14 month close / carry-over ---
      'close': 'Đóng',
      'closeMonth': 'Chốt tháng',
      'closeMonthConfirmTitle': 'Chốt {month}?',
      'closeMonthConfirmMessage':
          'Số dư chuyển tiếp (ngày bù, chuỗi ngày làm, nghỉ premium) được tính '
          'từ chấm công tháng này và lưu lại cho lịch tháng sau.',
      'closeMonthResultTitle': 'Đã chốt tháng — số dư chuyển tiếp',
      'closeMonthEmpty': 'Máy chủ không trả về số dư chuyển tiếp nào.',
      'closeMonthFailed': 'Không thể chốt tháng.',
      'carryComp': 'Ngày bù',
      'carryStreak': 'Chuỗi ngày làm',
      'carryPremiumOff': 'Nghỉ premium',
      // --- My attendance, leave window, i18n cleanup (review 2026-11-06) ---
      'navMyAttendance': 'Chấm công của tôi',
      'myAttendanceEmptyMessage':
          'Tháng này chưa có bản ghi. Chấm công sẽ hiện khi lịch được công bố.',
      'userFallback': 'ID {id}',
      'selectYearMonthFirst': 'Vui lòng chọn năm và tháng.',
      'selectYearFirst': 'Vui lòng chọn năm.',
      'statusReady': 'Sẵn sàng',
      'statusComplete': 'Hoàn tất',
      // --- Annual leave quota (owner decision D4, 2026-11-06) ---
      'annualLeaveRemaining': 'Phép năm còn lại',
      'annualLeaveQuota': 'Định mức phép năm',
      'annualLeaveQuotaHint': 'Số ngày mỗi năm — để trống để dùng mặc định',
      'annualLeaveQuotaInvalid': 'Nhập số nguyên từ 0 đến 365.',
      'editAnnualLeaveQuota': 'Sửa định mức phép',
      'annualLeaveQuotaUpdated': 'Đã cập nhật định mức phép năm.',
      // --- Schedule screen (review 2026-11-08: A3, C2, D3) ---
      'scheduleLoadFailed': 'Không thể tải lịch:',
      'actionFailed': 'Không thể thực hiện thao tác.',
      'checkingRules': 'Đang kiểm tra quy tắc…',
      'ruleViolationsInMonth':
          'vi phạm quy tắc trong tháng này. Hãy xem lại trước khi công bố.',
      'publishWithViolationsTitle': 'Công bố khi còn vi phạm quy tắc?',
      'publishWithViolationsBody':
          'Lịch tháng này vẫn vi phạm các quy tắc sau. Vẫn công bố?',
      'rulesCheckFailed':
          'Hiện không kiểm tra được quy tắc. Vẫn công bố?',
      'publishAnyway': 'Vẫn công bố',
      'approvedWithWarnings': 'Đã duyệt yêu cầu, có cảnh báo quy tắc',
      'swapPartner': 'Người hoán đổi',
    },
  };

  @visibleForTesting
  static bool get translationsAreComplete {
    final englishKeys = _values['en']!.keys.toSet();
    final vietnameseKeys = _values['vi']!.keys.toSet();
    return englishKeys.length == vietnameseKeys.length &&
        englishKeys.containsAll(vietnameseKeys) &&
        vietnameseKeys.containsAll(englishKeys);
  }

  String text(String key) =>
      _values[locale.languageCode]?[key] ?? _values['en']![key] ?? key;

  String get appTitle => text('appTitle');
  String get productName => text('productName');
  String get language => text('language');
  String get english => text('english');
  String get vietnamese => text('vietnamese');
  String get login => text('login');
  String get logout => text('logout');
  String get username => text('username');
  String get password => text('password');
  String get fieldRequired => text('fieldRequired');
  String get navSchedule => text('navSchedule');
  String get navFlights => text('navFlights');
  String get navLeaves => text('navLeaves');
  String get navAttendance => text('navAttendance');
  String get navReports => text('navReports');
  String get navUsers => text('navUsers');
  String get register => text('register');
  String get createAccount => text('createAccount');
  String get backToLogin => text('backToLogin');
  String get fullName => text('fullName');
  String get role => text('role');
  String get minThreeChars => text('minThreeChars');
  String get minSixChars => text('minSixChars');
  String get registerPending => text('registerPending');
  String get registerFailed => text('registerFailed');
  String get createUser => text('createUser');
  String get createUserFailed => text('createUserFailed');
  String get cancel => text('cancel');
  String get create => text('create');
  String get refresh => text('refresh');
  String get loadFailed => text('loadFailed');
  String get noUsers => text('noUsers');
  String get status => text('status');
  String get actions => text('actions');
  String get approve => text('approve');
  String get disable => text('disable');
  String get enable => text('enable');

  String monthYear(DateTime date) {
    const monthsEn = [
      'January',
      'February',
      'March',
      'April',
      'May',
      'June',
      'July',
      'August',
      'September',
      'October',
      'November',
      'December',
    ];
    return isVietnamese
        ? 'Tháng ${date.month} ${date.year}'
        : '${monthsEn[date.month - 1]} ${date.year}';
  }

  String shortWeekday(DateTime date) {
    const en = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const vi = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'];
    return (isVietnamese ? vi : en)[date.weekday - 1];
  }

  String flightDate(DateTime date) {
    if (isVietnamese) {
      return '${shortWeekday(date)}, ${_two(date.day)}/${_two(date.month)}';
    }
    const months = [
      'Jan',
      'Feb',
      'Mar',
      'Apr',
      'May',
      'Jun',
      'Jul',
      'Aug',
      'Sep',
      'Oct',
      'Nov',
      'Dec',
    ];
    return '${_two(date.day)} ${months[date.month - 1]}, '
        '${shortWeekday(date)}';
  }

  String dateTime(DateTime date) {
    if (isVietnamese) {
      return '${_two(date.day)}/${_two(date.month)}/${date.year}, '
          '${_two(date.hour)}:${_two(date.minute)}';
    }
    const months = [
      'Jan',
      'Feb',
      'Mar',
      'Apr',
      'May',
      'Jun',
      'Jul',
      'Aug',
      'Sep',
      'Oct',
      'Nov',
      'Dec',
    ];
    return '${_two(date.day)} ${months[date.month - 1]} ${date.year}, '
        '${_two(date.hour)}:${_two(date.minute)}';
  }

  String statusLabel(String status) => switch (status.toLowerCase()) {
    'active' => text('active'),
    'pending' => text('pending'),
    'disabled' => text('disabled'),
    'complete' => text('statusComplete'),
    'review' => text('review'),
    'approved' => text('approved'),
    'rejected' => text('rejected'),
    'ready' => text('statusReady'),
    _ => status,
  };

  String leaveTypeLabel(String type) => switch (type.toLowerCase()) {
    'monthly leave' => text('monthlyLeave'),
    'annual leave' => text('annualLeave'),
    'compensation' => text('compensation'),
    _ => type,
  };

  String roleLabel(String role) => switch (role) {
    'M' => isVietnamese ? 'M — Quản trị' : 'M — Admin',
    'T' => isVietnamese ? 'T — Linh hoạt' : 'T — Flexible',
    'A' => isVietnamese ? 'A — Cố định' : 'A — Fixed',
    'F' => isVietnamese ? 'F — Linh hoạt' : 'F — Flexible',
    _ => role,
  };

  String authError(String? code) => switch (code) {
    'incorrect_credentials' => text('authIncorrectCredentials'),
    'server_unavailable' => text('authServerUnavailable'),
    'http_failure' => text('authHttpFailure'),
    'unknown_failure' => text('authUnknownFailure'),
    'session_expired' => text('authSessionExpired'),
    null => '',
    _ => code,
  };

  /// "Imported N flights from Excel." (F-04).
  String importExcelSuccess(int count) =>
      text('importExcelSuccess').replaceAll('{count}', '$count');

  /// "Close March 2026?" (F-14).
  String closeMonthConfirmTitle(DateTime month) =>
      text('closeMonthConfirmTitle').replaceAll('{month}', monthYear(month));

  /// Leave page subtitle with the live window's last registration day.
  String leaveSubtitle(int closesOnDay) =>
      text('leaveSubtitle').replaceAll('{day}', '$closesOnDay');

  /// "ID 7" — a row whose user is not in the loaded directory.
  String userFallback(int userId) =>
      text('userFallback').replaceAll('{id}', '$userId');

  static String _two(int value) => value.toString().padLeft(2, '0');
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  bool isSupported(Locale locale) => AppLocalizations.supportedLocales.any(
    (supported) => supported.languageCode == locale.languageCode,
  );

  @override
  Future<AppLocalizations> load(Locale locale) =>
      SynchronousFuture(AppLocalizations(locale));

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}
