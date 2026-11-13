import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/api_error_message.dart';
import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../providers/time_clock_provider.dart';
import 'staff_clock_page.dart';

/// The clock tab: an employee checks in and out; the admin sees and
/// corrects everyone's punches ([StaffClockPage]).
class TimeClockPage extends ConsumerWidget {
  const TimeClockPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isAdmin = ref.watch(
      authControllerProvider.select((a) => a.user?.isAdmin ?? false),
    );
    return isAdmin ? const StaffClockPage() : const _OwnClockPage();
  }
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

    return SingleChildScrollView(
      padding: const EdgeInsets.all(DsSpacing.x4),
      child: Align(
        alignment: Alignment.topLeft,
        // A narrow column: two buttons and a short table do not need the
        // whole window, and the eye stays on one line.
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 640),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(l.text('clockTitle'),
                  style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: DsSpacing.x4),
              _todayCard(l, state),
              const SizedBox(height: DsSpacing.x6),
              Text(l.text('clockHistory'),
                  style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: DsSpacing.x2),
              if (state.isLoading)
                const Center(child: CircularProgressIndicator())
              else if (state.monthEntries.isEmpty)
                Text(l.text('clockNoEntries'),
                    style: const TextStyle(color: DsColors.textMuted))
              else
                DsOwnClockTable(
                  rows: [
                    for (final e in state.monthEntries)
                      (e.workDate, e.checkInLocal, e.checkOutLocal),
                  ],
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _todayCard(AppLocalizations l, TimeClockState state) {
    return DsSurface(
      padding: const EdgeInsets.all(DsSpacing.x4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            state.checkedIn
                ? '${l.text('clockCheckedInAt')} ${state.today?.checkInLocal ?? '—'}'
                    '${state.checkedOut ? ' · ${l.text('clockCheckedOutAt')} ${state.today?.checkOutLocal ?? '—'}' : ''}'
                : l.text('clockNotCheckedIn'),
            style: const TextStyle(fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: DsSpacing.x3),
          Row(
            children: [
              DsPrimaryButton(
                label: l.text('clockCheckIn'),
                icon: Icons.login_outlined,
                loading: state.isMutating,
                onPressed: state.checkedIn || state.isMutating
                    ? null
                    : () => _act(true, l),
              ),
              const SizedBox(width: DsSpacing.x3),
              DsSecondaryButton(
                label: l.text('clockCheckOut'),
                icon: Icons.logout_outlined,
                // Checking out again moves the check-out to now (the
                // latest one ends the day).
                onPressed: !state.checkedIn || state.isMutating
                    ? null
                    : () => _act(false, l),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
