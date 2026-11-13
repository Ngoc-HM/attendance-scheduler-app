import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/attendance/presentation/pages/attendance_page.dart';
import '../../features/attendance/presentation/pages/holidays_page.dart';
import '../../features/attendance/presentation/pages/time_clock_page.dart';
import '../../features/auth/presentation/pages/login_page.dart';
import '../../features/auth/presentation/pages/register_page.dart';
import '../../features/auth/presentation/providers/auth_provider.dart';
import '../../features/flights/presentation/pages/flight_presets_page.dart';
import '../../features/flights/presentation/pages/flights_page.dart';
import '../../features/home/presentation/pages/home_shell.dart';
import '../../features/leaves/presentation/pages/leaves_page.dart';
import '../../features/reports/presentation/pages/reports_page.dart';
import '../../features/schedule/presentation/pages/schedule_page.dart';
import '../../features/users/presentation/pages/users_page.dart';

/// Routes only role M may open (client-side UX guard; the API re-checks).
const _adminOnlyPaths = {
  AppRoute.flights,
  AppRoute.flightPresets,
  AppRoute.reports,
  AppRoute.users,
  AppRoute.holidays,
};

/// Routes reachable without a session.
const _publicPaths = {AppRoute.login, AppRoute.register};

/// Bridges Riverpod → go_router: pinged whenever the signed-in user changes
/// (login, logout, session expiry) so `redirect` is re-evaluated for the
/// current location.
class _AuthChangeNotifier extends ChangeNotifier {
  void ping() => notifyListeners();
}

/// Application routes. The authenticated sections live inside a [HomeShell]
/// (navigation rail); `/login` and `/register` sit outside it.
final appRouterProvider = Provider<GoRouter>((ref) {
  final authChanges = _AuthChangeNotifier();
  ref.onDispose(authChanges.dispose);
  ref.listen<AuthState>(authControllerProvider, (previous, next) {
    if (previous?.user != next.user) authChanges.ping();
  });

  return GoRouter(
    initialLocation: AppRoute.login,
    refreshListenable: authChanges,
    redirect: (context, state) {
      final user = ref.read(authControllerProvider).user;
      final path = state.uri.path;
      // No session (never logged in, logged out, or the token expired): only
      // the public pages are reachable.
      if (user == null) {
        return _publicPaths.contains(path) ? null : AppRoute.login;
      }
      // Signed in (login or a restored session): login/register are done.
      if (_publicPaths.contains(path)) return AppRoute.schedule;
      if (user.isAdmin) return null;
      if (_adminOnlyPaths.contains(path)) return AppRoute.schedule;
      return null;
    },
    routes: [
      GoRoute(
        path: AppRoute.login,
        builder: (context, state) => const LoginPage(),
      ),
      GoRoute(
        path: AppRoute.register,
        builder: (context, state) => const RegisterPage(),
      ),
      ShellRoute(
        builder: (context, state, child) =>
            HomeShell(location: state.uri.path, child: child),
        // `NoTransitionPage` on every tab route: switching tabs is instantaneous
        // with zero slide/fade. go_router would otherwise apply the default
        // platform page transition (a slide on macOS) between these sub-routes.
        routes: [
          GoRoute(
            path: AppRoute.schedule,
            pageBuilder: (context, state) =>
                const NoTransitionPage(child: SchedulePage()),
          ),
          GoRoute(
            path: AppRoute.flights,
            pageBuilder: (context, state) =>
                const NoTransitionPage(child: FlightsPage()),
          ),
          GoRoute(
            path: AppRoute.flightPresets,
            pageBuilder: (context, state) =>
                const NoTransitionPage(child: FlightPresetsPage()),
          ),
          GoRoute(
            path: AppRoute.leaves,
            pageBuilder: (context, state) =>
                const NoTransitionPage(child: LeavesPage()),
          ),
          GoRoute(
            path: AppRoute.attendance,
            pageBuilder: (context, state) =>
                const NoTransitionPage(child: AttendancePage()),
          ),
          GoRoute(
            path: AppRoute.reports,
            pageBuilder: (context, state) =>
                const NoTransitionPage(child: ReportsPage()),
          ),
          GoRoute(
            path: AppRoute.users,
            pageBuilder: (context, state) =>
                const NoTransitionPage(child: UsersPage()),
          ),
          GoRoute(
            path: AppRoute.holidays,
            pageBuilder: (context, state) =>
                const NoTransitionPage(child: HolidaysPage()),
          ),
          GoRoute(
            path: AppRoute.clock,
            pageBuilder: (context, state) =>
                const NoTransitionPage(child: TimeClockPage()),
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
  static const String register = '/register';
  static const String schedule = '/schedule';
  static const String flights = '/flights';
  static const String flightPresets = '/flights/presets';
  static const String leaves = '/leaves';
  static const String attendance = '/attendance';
  static const String reports = '/reports';
  static const String users = '/users';
  static const String clock = '/clock';
  static const String holidays = '/holidays';
}
