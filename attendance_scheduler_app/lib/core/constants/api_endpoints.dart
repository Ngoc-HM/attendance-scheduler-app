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

  // Leaves (F-05, F-06)
  static const String leaves = '/leaves';

  // Schedules (F-07..F-09)
  static const String generateSchedule = '/schedules/generate';
  static String schedule(int year, int month) => '/schedules/$year/$month';

  // Attendance & holidays (F-10..F-13)
  static const String attendance = '/attendance';
  static const String holidays = '/holidays';

  // Reports (F-15)
  static String monthlyReport(int year, int month) =>
      '/reports/monthly/$year/$month';
  static String yearlyReport(int year) => '/reports/yearly/$year';
}
