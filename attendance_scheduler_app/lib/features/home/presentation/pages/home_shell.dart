import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/router/app_router.dart';
import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../../auth/domain/entities/user.dart';
import '../../../auth/presentation/providers/auth_provider.dart';

class HomeShell extends ConsumerWidget {
  const HomeShell({super.key, required this.location, required this.child});

  final String location;
  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final auth = ref.watch(authControllerProvider);
    final destinations = [
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
      if (auth.user?.isAdmin ?? true)
        DsNavigationDestination(
          path: AppRoute.users,
          label: l.navUsers,
          icon: Icons.people_outline,
        ),
    ];
    final selected = destinations.indexWhere(
      (item) => location.startsWith(item.path),
    );

    return DsNavigationShell(
      appTitle: l.appTitle,
      productName: 'Roster FRA',
      destinations: destinations,
      selectedIndex: selected < 0 ? 0 : selected,
      userName: auth.user?.fullName,
      userRole: auth.user?.role.apiValue,
      logoutLabel: l.logout,
      onSelected: (index) => context.go(destinations[index].path),
      onLogout: () async {
        await ref.read(authControllerProvider.notifier).logout();
        if (context.mounted) context.go(AppRoute.login);
      },
      child: child,
    );
  }
}
