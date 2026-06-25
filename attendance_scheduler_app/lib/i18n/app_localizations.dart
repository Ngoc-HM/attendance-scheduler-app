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
      'leaveSubtitle': 'Monthly requests close on the 20th',
      'requestLeave': 'Request leave',
      'pending': 'Pending',
      'approved': 'Approved',
      'rejected': 'Rejected',
      'active': 'Active',
      'disabled': 'Disabled',
      'complete': 'Complete',
      'review': 'Review',
      'ready': 'Ready',
      'compDays': 'Comp days',
      'registrationOpen': 'Registration open',
      'shortLeaveMessage':
          'Short leave is under 5 consecutive days. Longer leave uses the annual request.',
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
      // --- Phase 09 wiring: flights / leaves / reports / schedule / attendance
      'addFlightDay': 'Add flight day',
      'addHoliday': 'Add holiday',
      'adminOnlyAction': 'This action requires admin privileges.',
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
      'pickDate': 'Pick a date',
      'reportSavedTo': 'Report saved to',
      'requestShiftChange': 'Request shift change',
      'save': 'Save',
      'scheduleEmptyTitle': 'No roster yet',
      'scheduleEmptyMessage':
          'No schedule for this month. Tap "Generate schedule" to build one.',
      'scheduleGenerated': 'Schedule generated.',
      'scheduleInfeasible': 'No valid schedule could be found.',
      'scheduleNotPublishedYet': 'The schedule for this month is not published yet.',
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
      'monthFlightsHint': 'Tick presets per day. Up to 2 per row. Only changed days are saved.',
      'monthFlightsLoading': 'Presets are loading — please try again.',
      'monthFlightsSaved': 'Month flights saved.',
      'selectAllColumn': 'Select all',
      'applyMonth': 'Apply whole month',
      'columnDay': 'Day',
      'columnWeekday': 'Wday',
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
      'leaveSubtitle': 'Đăng ký hàng tháng đóng vào ngày 20',
      'requestLeave': 'Đăng ký nghỉ',
      'pending': 'Chờ duyệt',
      'approved': 'Đã duyệt',
      'rejected': 'Đã từ chối',
      'active': 'Đang hoạt động',
      'disabled': 'Đã vô hiệu hóa',
      'complete': 'Hoàn tất',
      'review': 'Cần rà soát',
      'ready': 'Sẵn sàng',
      'compDays': 'Ngày nghỉ bù',
      'registrationOpen': 'Đang mở đăng ký',
      'shortLeaveMessage':
          'Nghỉ ngắn dưới 5 ngày liên tục. Nghỉ dài hơn dùng đăng ký phép năm.',
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
      // --- Phase 09 wiring: flights / leaves / reports / schedule / attendance
      'addFlightDay': 'Thêm ngày bay',
      'addHoliday': 'Thêm ngày lễ',
      'adminOnlyAction': 'Thao tác này cần quyền quản trị.',
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
      'pickDate': 'Chọn ngày',
      'reportSavedTo': 'Báo cáo đã lưu tại',
      'requestShiftChange': 'Yêu cầu đổi ca',
      'save': 'Lưu',
      'scheduleEmptyTitle': 'Chưa có lịch',
      'scheduleEmptyMessage':
          'Chưa có lịch cho tháng này. Nhấn "Tạo lịch" để bắt đầu.',
      'scheduleGenerated': 'Đã tạo lịch.',
      'scheduleInfeasible': 'Không tìm được lời giải hợp lệ cho lịch.',
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
      'monthFlightsHint': 'Tick mẫu cho từng ngày. Tối đa 2 mẫu mỗi hàng. Chỉ lưu ngày có thay đổi.',
      'monthFlightsLoading': 'Đang tải mẫu — vui lòng thử lại.',
      'monthFlightsSaved': 'Đã lưu chuyến bay cả tháng.',
      'selectAllColumn': 'Chọn tất cả',
      'applyMonth': 'Áp dụng cả tháng',
      'columnDay': 'Ngày',
      'columnWeekday': 'Thứ',
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
    'complete' => text('complete'),
    'review' => text('review'),
    'approved' => text('approved'),
    'rejected' => text('rejected'),
    'ready' => text('ready'),
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
    _ => role,
  };

  String authError(String? code) => switch (code) {
    'incorrect_credentials' => text('authIncorrectCredentials'),
    'server_unavailable' => text('authServerUnavailable'),
    'http_failure' => text('authHttpFailure'),
    'unknown_failure' => text('authUnknownFailure'),
    null => '',
    _ => code,
  };

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
