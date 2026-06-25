/// Backend REST paths (relative to [AppConfig.apiBaseUrl]). Mirrors
/// `backend/app/api/v1`.
class ApiEndpoints {
  const ApiEndpoints._();

  // Auth & users (F-01..F-03)
  static const String login = '/auth/login';
  static const String register = '/auth/register';
  static const String me = '/users/me';
  static const String users = '/users';
  static String userById(int id) => '/users/$id';
  static String approveUser(int id) => '/auth/users/$id/approve';

  // Flights (F-04)
  static const String flightDays = '/flights/days';
  static const String flights = '/flights';
  static const String flightsImport = '/flights/import';
  static const String flightPresets = '/flights/presets';
  static String flightPresetById(int id) => '/flights/presets/$id';
  static const String flightsApply = '/flights/days/apply';
  static const String flightsApplyBatch = '/flights/days/apply-batch';

  // Leaves (F-05, F-06)
  static const String leaves = '/leaves';
  static const String leavesPending = '/leaves/pending';
  static String leaveDecide(int id) => '/leaves/$id/decide';
  static const String leaveConflicts = '/leaves/conflicts'; // ?date=YYYY-MM-DD

  // Shift-change requests (decision #8)
  static const String shiftChanges = '/shift-changes';
  static String shiftChangeDecide(int id) => '/shift-changes/$id/decide';

  // Schedules (F-07..F-09)
  static const String generateSchedule = '/schedules/generate';
  static String schedule(int year, int month) => '/schedules/$year/$month';
  static String scheduleOverride(int id) => '/schedules/$id/override';
  static String schedulePublish(int id) => '/schedules/$id/publish';

  // Attendance & holidays (F-10..F-13)
  static const String attendance = '/attendance';
  static const String myAttendance = '/attendance/me';
  static const String attendanceSeed = '/attendance/seed';
  static const String attendanceSickCover = '/attendance/sick-cover';
  static const String holidays = '/holidays';
  static String holidayById(int id) => '/holidays/$id';

  // Calculations (F-14)
  static String closeMonth(int year, int month) =>
      '/calculations/$year/$month/close';
  static const String carrySummary = '/calculations/summary';

  // Reports (F-15) — append `?format=csv|xlsx`.
  static String monthlyReport(int year, int month) =>
      '/reports/monthly/$year/$month';
  static String yearlyReport(int year) => '/reports/yearly/$year';
}
