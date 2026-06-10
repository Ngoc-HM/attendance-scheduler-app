import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/router/app_router.dart';
import '../../../auth/presentation/providers/auth_provider.dart';

/// Navigation shell for the authenticated area (left navigation rail + content).
class HomeShell extends ConsumerWidget {
  const HomeShell({super.key, required this.location, required this.child});

  final String location;
  final Widget child;

  static const List<({String path, IconData icon, String label})> _destinations = [
    (path: AppRoute.schedule, icon: Icons.calendar_month, label: 'Schedule'),
    (path: AppRoute.flights, icon: Icons.flight_takeoff, label: 'Flights'),
    (path: AppRoute.leaves, icon: Icons.beach_access, label: 'Leaves'),
    (path: AppRoute.attendance, icon: Icons.fact_check, label: 'Attendance'),
    (path: AppRoute.reports, icon: Icons.bar_chart, label: 'Reports'),
    (path: AppRoute.users, icon: Icons.people, label: 'Users'),
  ];

  int get _selectedIndex {
    final index = _destinations.indexWhere((d) => location.startsWith(d.path));
    return index < 0 ? 0 : index;
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      body: Row(
        children: [
          NavigationRail(
            extended: true,
            minExtendedWidth: 180,
            selectedIndex: _selectedIndex,
            onDestinationSelected: (i) => context.go(_destinations[i].path),
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
                    tooltip: 'Log out',
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
              for (final d in _destinations)
                NavigationRailDestination(
                  icon: Icon(d.icon),
                  label: Text(d.label),
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
