import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/router/app_router.dart';
import '../../../../i18n/app_localizations.dart';
import '../../../auth/presentation/providers/auth_provider.dart';

/// Navigation shell for the authenticated area (left navigation rail + content).
class HomeShell extends ConsumerWidget {
  const HomeShell({super.key, required this.location, required this.child});

  final String location;
  final Widget child;

  /// Destination paths — index-aligned with the labels built in [build].
  static const List<String> _paths = [
    AppRoute.schedule,
    AppRoute.flights,
    AppRoute.leaves,
    AppRoute.attendance,
    AppRoute.reports,
    AppRoute.users,
  ];

  int get _selectedIndex {
    final index = _paths.indexWhere((p) => location.startsWith(p));
    return index < 0 ? 0 : index;
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final items = <({IconData icon, String label})>[
      (icon: Icons.calendar_month, label: l.navSchedule),
      (icon: Icons.flight_takeoff, label: l.navFlights),
      (icon: Icons.beach_access, label: l.navLeaves),
      (icon: Icons.fact_check, label: l.navAttendance),
      (icon: Icons.bar_chart, label: l.navReports),
      (icon: Icons.people, label: l.navUsers),
    ];

    return Scaffold(
      body: Row(
        children: [
          NavigationRail(
            extended: true,
            minExtendedWidth: 180,
            selectedIndex: _selectedIndex,
            onDestinationSelected: (i) => context.go(_paths[i]),
            leading: const Padding(
              padding: EdgeInsets.symmetric(vertical: 16),
              child: Icon(Icons.flight_class, size: 32),
            ),
            trailing: Expanded(
              child: Align(
                alignment: Alignment.bottomCenter,
                child: Padding(
                  padding: const EdgeInsets.only(bottom: 16),
                  child: IconButton(
                    tooltip: l.logout,
                    icon: const Icon(Icons.logout),
                    onPressed: () async {
                      await ref.read(authControllerProvider.notifier).logout();
                      if (context.mounted) context.go(AppRoute.login);
                    },
                  ),
                ),
              ),
            ),
            destinations: [
              for (final it in items)
                NavigationRailDestination(
                  icon: Icon(it.icon),
                  label: Text(it.label),
                ),
            ],
          ),
          const VerticalDivider(width: 1),
          Expanded(child: child),
        ],
      ),
    );
  }
}
