import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/router/app_router.dart';
import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../../../i18n/locale_provider.dart';
import '../../../auth/domain/entities/user.dart';
import '../../../auth/presentation/providers/auth_provider.dart';

class HomeShell extends ConsumerWidget {
  const HomeShell({super.key, required this.location, required this.child});

  final String location;
  final Widget child;

  /// Role-gated navigation (owner 2026-07-09): admin keeps the full shell;
  /// other roles get View schedule / Register leave / Check-in-out, and the
  /// self-arrange tab only for T & F.
  static List<DsNavigationDestination> _destinationsFor(
    User? user,
    AppLocalizations l,
  ) {
    // While the user is still loading, show the admin set (matches the old
    // `?? true` behavior; the router guard protects admin-only pages anyway).
    if (user == null || user.isAdmin) {
      return [
        DsNavigationDestination(
          path: AppRoute.schedule,
          label: l.navSchedule,
          icon: Icons.calendar_today_outlined,
        ),
        DsNavigationDestination(
          path: AppRoute.flights,
          label: l.navFlights,
          icon: Icons.flight_takeoff_outlined,
        ),
        DsNavigationDestination(
          path: AppRoute.leaves,
          label: l.navLeaves,
          icon: Icons.event_available_outlined,
        ),
        DsNavigationDestination(
          path: AppRoute.attendance,
          label: l.navAttendance,
          icon: Icons.fact_check_outlined,
        ),
        DsNavigationDestination(
          path: AppRoute.reports,
          label: l.navReports,
          icon: Icons.bar_chart_outlined,
        ),
        DsNavigationDestination(
          path: AppRoute.users,
          label: l.navUsers,
          icon: Icons.people_outline,
        ),
      ];
    }
    return [
      DsNavigationDestination(
        path: AppRoute.schedule,
        label: l.navSchedule,
        icon: Icons.calendar_today_outlined,
      ),
      if (user.role.canSelfArrange)
        DsNavigationDestination(
          path: AppRoute.selfArrange,
          label: l.text('navSelfArrange'),
          icon: Icons.edit_calendar_outlined,
        ),
      DsNavigationDestination(
        path: AppRoute.leaves,
        label: l.navLeaves,
        icon: Icons.event_available_outlined,
      ),
      DsNavigationDestination(
        path: AppRoute.clock,
        label: l.text('navClock'),
        icon: Icons.timer_outlined,
      ),
    ];
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final locale = ref.watch(localeControllerProvider);
    final auth = ref.watch(authControllerProvider);
    final destinations = _destinationsFor(auth.user, l);
    final selected = destinations.indexWhere(
      (item) => location.startsWith(item.path),
    );

    return DsNavigationShell(
      appTitle: l.appTitle,
      productName: l.productName,
      destinations: destinations,
      selectedIndex: selected < 0 ? 0 : selected,
      userName: auth.user?.fullName,
      userRole: auth.user == null
          ? null
          : l.roleLabel(auth.user!.role.apiValue),
      logoutLabel: l.logout,
      languageCode: locale.languageCode,
      onLanguageChanged: ref
          .read(localeControllerProvider.notifier)
          .setLanguage,
      onSelected: (index) => context.go(destinations[index].path),
      onLogout: () async {
        await ref.read(authControllerProvider.notifier).logout();
        if (context.mounted) context.go(AppRoute.login);
      },
      child: child,
    );
  }
}
