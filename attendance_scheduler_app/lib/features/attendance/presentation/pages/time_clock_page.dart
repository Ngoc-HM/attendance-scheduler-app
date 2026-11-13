import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/api_error_message.dart';
import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../providers/time_clock_provider.dart';

/// The employee's check-in/out tab (owner 2026-07-09). The admin reads and
/// edits everyone's punches from the attendance grid instead.
class TimeClockPage extends StatelessWidget {
  const TimeClockPage({super.key});

  @override
  Widget build(BuildContext context) => const _OwnClockPage();
}

/// Check-in / check-out for all employee roles (owner 2026-07-09).
/// Timestamps only — the admin attendance code grid is untouched.
class _OwnClockPage extends ConsumerStatefulWidget {
  const _OwnClockPage();

  @override
  ConsumerState<_OwnClockPage> createState() => _OwnClockPageState();
}

class _OwnClockPageState extends ConsumerState<_OwnClockPage> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback(
      (_) => ref.read(timeClockControllerProvider.notifier).load(),
    );
  }

  Future<void> _act(bool isCheckIn, AppLocalizations l) async {
    final ctrl = ref.read(timeClockControllerProvider.notifier);
    final ok = await (isCheckIn ? ctrl.checkIn() : ctrl.checkOut());
    if (!mounted) return;
    // The time the server stamped (Frankfurt), not the device clock.
    final today = ref.read(timeClockControllerProvider).today;
    final stamped = isCheckIn ? today?.checkInLocal : today?.checkOutLocal;
    DsFeedback.show(
      context,
      ok
          ? '${isCheckIn ? l.text('clockCheckedInAt') : l.text('clockCheckedOutAt')} ${stamped ?? ''}'
          : apiErrorMessage(
              l,
              ref.read(timeClockControllerProvider).error,
              fallbackKey: 'clockActionFailed',
            ),
      tone: ok ? DsTone.success : DsTone.danger,
    );
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final state = ref.watch(timeClockControllerProvider);
    final today = state.today;

    // Same frame as the other screens: title, the one action that applies
    // now at the top right, today's numbers, then the month's table.
    return DsPage(
      title: l.text('clockTitle'),
      actions: [
        DsPrimaryButton(
          label: l.text(state.checkedIn ? 'clockCheckOut' : 'clockCheckIn'),
          icon: state.checkedIn ? Icons.logout_outlined : Icons.login_outlined,
          loading: state.isMutating,
          onPressed: state.isMutating || state.isLoading
              ? null
              : () => _act(!state.checkedIn, l),
        ),
      ],
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          DsResponsiveGrid(
            children: [
              DsMetricCard(
                label: l.text('clockTodayIn'),
                value: today?.checkInLocal ?? '—',
                icon: Icons.login_outlined,
                tone: DsTone.primary,
              ),
              DsMetricCard(
                label: l.text('clockTodayOut'),
                value: today?.checkOutLocal ?? '—',
                icon: Icons.logout_outlined,
                tone: DsTone.warning,
              ),
              DsMetricCard(
                label: l.text('clockTodayWorked'),
                value:
                    workedTime(today?.checkInLocal, today?.checkOutLocal) ??
                    '—',
                icon: Icons.timer_outlined,
                tone: DsTone.success,
              ),
            ],
          ),
          const SizedBox(height: DsSpacing.x6),
          if (state.isLoading)
            const Center(child: CircularProgressIndicator())
          else
            DsOwnClockTable(
              title: l.text('clockHistory'),
              emptyText: l.text('clockNoEntries'),
              rows: [
                for (final e in state.monthEntries)
                  (e.workDate, e.checkInLocal, e.checkOutLocal),
              ],
            ),
        ],
      ),
    );
  }
}
