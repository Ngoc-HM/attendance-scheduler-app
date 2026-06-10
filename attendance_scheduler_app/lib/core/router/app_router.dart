import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/attendance/presentation/pages/attendance_page.dart';
import '../../features/auth/presentation/pages/login_page.dart';
import '../../features/flights/presentation/pages/flights_page.dart';
import '../../features/home/presentation/pages/home_shell.dart';
import '../../features/leaves/presentation/pages/leaves_page.dart';
import '../../features/reports/presentation/pages/reports_page.dart';
import '../../features/schedule/presentation/pages/schedule_page.dart';
import '../../features/users/presentation/pages/users_page.dart';

/// Application routes. The authenticated sections live inside a [HomeShell]
/// (navigation rail); `/login` sits outside it.
final appRouterProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: AppRoute.login,
    routes: [
      GoRoute(
        path: AppRoute.login,
        builder: (context, state) => const LoginPage(),
      ),
      ShellRoute(
        builder: (context, state, child) =>
            HomeShell(location: state.uri.path, child: child),
        routes: [
          GoRoute(
            path: AppRoute.schedule,
            builder: (context, state) => const SchedulePage(),
          ),
          GoRoute(
            path: AppRoute.flights,
            builder: (context, state) => const FlightsPage(),
          ),
          GoRoute(
            path: AppRoute.leaves,
            builder: (context, state) => const LeavesPage(),
          ),
          GoRoute(
            path: AppRoute.attendance,
            builder: (context, state) => const AttendancePage(),
          ),
          GoRoute(
            path: AppRoute.reports,
            builder: (context, state) => const ReportsPage(),
          ),
          GoRoute(
            path: AppRoute.users,
            builder: (context, state) => const UsersPage(),
          ),
        ],
      ),
    ],
  );
});

/// Centralized route paths.
class AppRoute {
  const AppRoute._();

  static const String login = '/login';
  static const String schedule = '/schedule';
  static const String flights = '/flights';
  static const String leaves = '/leaves';
  static const String attendance = '/attendance';
  static const String reports = '/reports';
  static const String users = '/users';
}
