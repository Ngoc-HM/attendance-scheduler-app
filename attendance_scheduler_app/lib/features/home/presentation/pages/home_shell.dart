import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/router/app_router.dart';
import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../../../i18n/locale_provider.dart';
import '../../../auth/domain/entities/user.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../data/pending_counts_datasource.dart';
import '../providers/pending_counts_provider.dart';

class HomeShell extends ConsumerStatefulWidget {
  const HomeShell({super.key, required this.location, required this.child});

  final String location;
  final Widget child;

  /// How often the admin's badge numbers are reloaded while the shell shows.
  static const pendingCountsInterval = Duration(seconds: 60);

  @override
  ConsumerState<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends ConsumerState<HomeShell> {
  Timer? _timer;

  /// Badge numbers reload when the shell first shows, on every tab switch,
  /// when the signed-in user changes, and on a quiet timer. Decisions
  /// refresh them from their controllers (`refreshPendingCounts`). The
  /// controller itself skips the call for anyone but an admin.
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _refreshCounts());
    _timer = Timer.periodic(
      HomeShell.pendingCountsInterval,
      (_) => _refreshCounts(),
    );
  }

  @override
  void didUpdateWidget(HomeShell oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.location != widget.location) _refreshCounts();
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  void _refreshCounts() {
    if (!mounted) return;
    ref.read(pendingCountsProvider.notifier).refresh();
  }

  /// Role-gated navigation (owner 2026-07-09): admin keeps the full shell;
  /// other roles get View schedule / Register leave / My attendance /
  /// Check-in-out.
  static List<DsNavigationDestination> _destinationsFor(
    User? user,
    AppLocalizations l,
    PendingCounts? counts,
  ) {
    // While the user is still loading, show the admin set (matches the old
    // `?? true` behavior; the router guard protects admin-only pages anyway).
    if (user == null || user.isAdmin) {
      return [
        DsNavigationDestination(
          path: AppRoute.schedule,
          label: l.navSchedule,
          icon: Icons.calendar_today_outlined,
          // Shift-change requests are decided on the schedule page.
          badgeCount: counts?.shiftChanges,
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
          badgeCount: counts?.leaves,
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
          badgeCount: counts?.users,
        ),
      ];
    }
    return [
      DsNavigationDestination(
        path: AppRoute.schedule,
        label: l.navSchedule,
        icon: Icons.calendar_today_outlined,
      ),
      DsNavigationDestination(
        path: AppRoute.leaves,
        label: l.navLeaves,
        icon: Icons.event_available_outlined,
      ),
      DsNavigationDestination(
        path: AppRoute.attendance,
        label: l.text('navMyAttendance'),
        icon: Icons.fact_check_outlined,
      ),
      DsNavigationDestination(
        path: AppRoute.clock,
        label: l.text('navClock'),
        icon: Icons.timer_outlined,
      ),
    ];
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final locale = ref.watch(localeControllerProvider);
    final auth = ref.watch(authControllerProvider);
    ref.listen(
      authControllerProvider.select((s) => (s.user?.id, s.user?.isAdmin)),
      (_, _) => _refreshCounts(),
    );
    // Employees never load counts, so they never see a badge.
    final counts = auth.user?.isAdmin == true
        ? ref.watch(pendingCountsProvider)
        : null;
    final destinations = _destinationsFor(auth.user, l, counts);
    final selected = destinations.indexWhere(
      (item) => widget.location.startsWith(item.path),
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
      child: widget.child,
    );
  }
}
