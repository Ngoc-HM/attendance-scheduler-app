import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/api_error_message.dart';
import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../data/datasources/time_clock_remote_datasource.dart';
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

  static String _hm(DateTime? t) => t == null
      ? '—'
      : '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';

  Future<void> _act(bool isCheckIn, AppLocalizations l) async {
    final ctrl = ref.read(timeClockControllerProvider.notifier);
    final ok = await (isCheckIn ? ctrl.checkIn() : ctrl.checkOut());
    if (!mounted) return;
    DsFeedback.show(
      context,
      ok
          ? '${isCheckIn ? l.text('clockCheckedInAt') : l.text('clockCheckedOutAt')} ${_hm(DateTime.now())}'
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
            for (final e in state.monthEntries) _historyRow(l, e),
        ],
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
                ? '${l.text('clockCheckedInAt')} ${_hm(state.today?.checkInAt)}'
                    '${state.checkedOut ? ' · ${l.text('clockCheckedOutAt')} ${_hm(state.today?.checkOutAt)}' : ''}'
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
                onPressed:
                    !state.checkedIn || state.checkedOut || state.isMutating
                        ? null
                        : () => _act(false, l),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _historyRow(AppLocalizations l, TimeClockEntry e) {
    final weekend = e.workDate.weekday == DateTime.saturday ||
        e.workDate.weekday == DateTime.sunday;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: DsSpacing.x1),
      child: Row(
        children: [
          SizedBox(
            width: 96,
            child: Text(
              '${e.workDate.day.toString().padLeft(2, '0')} '
              '${l.shortWeekday(e.workDate)}',
              style: TextStyle(
                fontWeight: FontWeight.w600,
                color: weekend ? DsColors.primary : DsColors.textPrimary,
              ),
            ),
          ),
          Text('${_hm(e.checkInAt)} → ${_hm(e.checkOutAt)}',
              style: const TextStyle(color: DsColors.textSecondary)),
        ],
      ),
    );
  }
}
