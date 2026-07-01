import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/shift_codes.dart';
import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../../auth/domain/entities/user.dart';
import '../../../flights/data/datasources/flights_remote_datasource.dart';
import '../../../flights/data/models/flight_day_model.dart';
import '../../domain/entities/schedule_entities.dart';
import '../providers/schedule_provider.dart';
import '../providers/shift_change_provider.dart';
import '../widgets/shift_change_dialog.dart';

class SchedulePage extends ConsumerStatefulWidget {
  const SchedulePage({super.key});

  @override
  ConsumerState<SchedulePage> createState() => _SchedulePageState();
}

class _SchedulePageState extends ConsumerState<SchedulePage> {
  DateTime _month = DateTime(DateTime.now().year, DateTime.now().month);
  bool _showShiftChanges = false;
  Map<int, String> _flightLabels = const {}; // day-of-month → FLT codes

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _loadMonth());
  }

  void _loadMonth() {
    final isAdmin = ref.read(isAdminProvider);
    ref.read(scheduleControllerProvider.notifier).load(
          _month.year,
          _month.month,
          isAdmin: isAdmin,
        );
    if (isAdmin) {
      ref.read(shiftChangeControllerProvider.notifier).load(all: true);
    }
    _loadFlights();
  }

  /// Load the month's flight codes (FLT #) per day for the roster's flight column.
  Future<void> _loadFlights() async {
    try {
      final days = await ref
          .read(flightsDataSourceProvider)
          .listDays(_month.year, _month.month);
      if (!mounted) return;
      setState(() => _flightLabels = _buildFlightLabels(days));
    } catch (_) {
      if (mounted) setState(() => _flightLabels = const {});
    }
  }

  /// Map day-of-month → the flight-code label, IDENTICAL to the Flights page
  /// (e.g. "31/30 · 37/36"): pair each arrival leg (has STA) with the departure
  /// leg (has STD) at the same index, join with " · ".
  static Map<int, String> _buildFlightLabels(List<FlightDayModel> days) {
    final result = <int, String>{};
    for (final fd in days) {
      final arr = fd.flights.where((f) => f.sta != null).toList();
      final dep = fd.flights.where((f) => f.std != null).toList();
      final count = fd.flightPairs > 0
          ? fd.flightPairs
          : (arr.isNotEmpty || dep.isNotEmpty ? 1 : 0);
      final labels = <String>[
        for (var i = 0; i < count; i++)
          '${i < arr.length ? arr[i].fltNumber : '?'}'
              '/${i < dep.length ? dep[i].fltNumber : '?'}',
      ];
      if (labels.isNotEmpty) result[fd.day.day] = labels.join(' · ');
    }
    return result;
  }

  void _prevMonth() {
    setState(() => _month = DateTime(_month.year, _month.month - 1));
    _loadMonth();
  }

  void _nextMonth() {
    setState(() => _month = DateTime(_month.year, _month.month + 1));
    _loadMonth();
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final isAdmin = ref.watch(isAdminProvider);
    final scheduleState = ref.watch(scheduleControllerProvider);

    if (scheduleState.isLoading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    // Non-admin gets 404 for drafts — show graceful message.
    if (scheduleState.error != null && !isAdmin) {
      return _ScheduleNotPublished(
        month: _month,
        onPrevious: _prevMonth,
        onNext: _nextMonth,
        errorMessage: l.text('scheduleNotPublishedYet'),
      );
    }

    final rows = _buildRows(scheduleState);

    return Column(
      children: [
        Expanded(
          child: DsScheduleView(
            month: _month,
            rows: rows,
            flightLabels: _flightLabels,
            onPreviousMonth: _prevMonth,
            onNextMonth: _nextMonth,
            onGenerate: isAdmin ? () => _onGenerate(context, l) : () {},
            onPublish: isAdmin ? () => _onPublish(context, l) : () {},
          ),
        ),
        if (scheduleState.lastResult != null)
          _GenerateResultBanner(
            result: scheduleState.lastResult!,
            onDismiss: () => ref
                .read(scheduleControllerProvider.notifier)
                .clearResult(),
          ),
        if (isAdmin && _showShiftChanges) ...[
          const Divider(height: 1),
          Padding(
            padding: const EdgeInsets.all(DsSpacing.x4),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    l.text('pendingShiftChanges'),
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close),
                  onPressed: () =>
                      setState(() => _showShiftChanges = false),
                ),
              ],
            ),
          ),
          const ShiftChangePendingPanel(),
        ],
        if (isAdmin)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: DsSpacing.x4, vertical: DsSpacing.x2),
            child: TextButton.icon(
              icon: Icon(_showShiftChanges
                  ? Icons.expand_less
                  : Icons.swap_horiz_outlined),
              label: Text(l.text('shiftChangeRequests')),
              onPressed: () =>
                  setState(() => _showShiftChanges = !_showShiftChanges),
            ),
          ),
      ],
    );
  }

  // ── Helpers ──────────────────────────────────────────────────────────────────

  List<DsRosterRowData> _buildRows(ScheduleState state) {
    final schedule = state.schedule;
    if (schedule == null) return [];

    // Build user id→code map (employee code, e.g. "A3"). Admin has the users
    // list; non-admin falls back to the raw id.
    final userMap = <int, String>{
      for (final u in state.users) u.id: u.code,
    };

    // Group assignments by user_id.
    final byUser = <int, List<ShiftAssignment>>{};
    for (final a in schedule.assignments) {
      byUser.putIfAbsent(a.userId, () => []).add(a);
    }

    // Sort each user's assignments by work_date.
    for (final list in byUser.values) {
      list.sort((a, b) => a.workDate.compareTo(b.workDate));
    }

    final rows = byUser.entries.map((entry) {
      final userId = entry.key;
      final assignments = entry.value;
      final shifts =
          assignments.map((a) => _codeToShiftCode(a.code)).toList();
      final name = userMap[userId] ?? 'User $userId';
      final role = _roleLabel(userId, state);

      final arrivals =
          shifts.where((s) => s == ShiftCode.a || s == ShiftCode.aD).length;
      final departures =
          shifts.where((s) => s == ShiftCode.d || s == ShiftCode.aD).length;
      final offDays = shifts.where((s) => s == ShiftCode.x).length;

      return DsRosterRowData(
        name: name,
        role: role,
        shifts: shifts,
        arrivals: arrivals,
        departures: departures,
        offDays: offDays,
      );
    }).toList();

    // Sort by role letter (A, M, T…), then by the numeric part of the code
    // (A1, A2, … A10) so the roster reads in a stable, predictable order.
    rows.sort((a, b) {
      final byRole = a.role.compareTo(b.role);
      if (byRole != 0) return byRole;
      return _codeSeq(a.name).compareTo(_codeSeq(b.name));
    });
    return rows;
  }

  /// Numeric suffix of an employee code ("A3" → 3); 0 when none.
  int _codeSeq(String code) =>
      int.tryParse(code.replaceAll(RegExp(r'[^0-9]'), '')) ?? 0;

  String _roleLabel(int userId, ScheduleState state) {
    final user = state.users.where((u) => u.id == userId).firstOrNull;
    return user?.role.apiValue ?? '';
  }

  ShiftCode _codeToShiftCode(String code) => switch (code) {
        'A' => ShiftCode.a,
        'D' => ShiftCode.d,
        'A/D' => ShiftCode.aD,
        'AD' => ShiftCode.ad,
        'X' => ShiftCode.x,
        'CD' => ShiftCode.cd,
        'O/D' => ShiftCode.oD,
        'T' => ShiftCode.t,
        'B' => ShiftCode.b,
        'S' => ShiftCode.s,
        'AL' => ShiftCode.al,
        _ => ShiftCode.x,
      };

  // ── Admin actions ─────────────────────────────────────────────────────────────

  Future<void> _onGenerate(BuildContext context, AppLocalizations l) async {
    // Testing mode: admin regenerates freely — the backend no longer blocks a
    // published or manually-edited month, so no confirm dialog is needed.
    await ref
        .read(scheduleControllerProvider.notifier)
        .generate(_month.year, _month.month);
    final state = ref.read(scheduleControllerProvider);
    if (!context.mounted) return;
    if (state.error != null) {
      DsFeedback.show(context, state.error!, tone: DsTone.danger);
    } else {
      final result = state.lastResult;
      if (result != null && !result.feasible) {
        DsFeedback.show(
          context,
          l.text('scheduleInfeasible'),
          tone: DsTone.warning,
        );
      } else {
        DsFeedback.show(
          context,
          l.text('scheduleGenerated'),
          tone: DsTone.success,
        );
      }
    }
  }

  Future<void> _onPublish(BuildContext context, AppLocalizations l) async {
    await ref.read(scheduleControllerProvider.notifier).publish();
    final state = ref.read(scheduleControllerProvider);
    if (!context.mounted) return;
    if (state.error != null) {
      DsFeedback.show(context, state.error!, tone: DsTone.danger);
    } else {
      DsFeedback.show(context, l.text('schedulePublished'), tone: DsTone.success);
    }
  }
}

// ── Supplementary widgets ──────────────────────────────────────────────────────

class _ScheduleNotPublished extends StatelessWidget {
  const _ScheduleNotPublished({
    required this.month,
    required this.onPrevious,
    required this.onNext,
    required this.errorMessage,
  });

  final DateTime month;
  final VoidCallback onPrevious;
  final VoidCallback onNext;
  final String errorMessage;

  @override
  Widget build(BuildContext context) {
    return DsScheduleView(
      month: month,
      rows: const [],
      onPreviousMonth: onPrevious,
      onNextMonth: onNext,
      onGenerate: () {},
      onPublish: () {},
    );
  }
}

/// Banner shown after a generate call, listing violations.
class _GenerateResultBanner extends ConsumerWidget {
  const _GenerateResultBanner({
    required this.result,
    required this.onDismiss,
  });

  final ScheduleResult result;
  final VoidCallback onDismiss;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final tone = result.feasible ? DsTone.success : DsTone.warning;
    final title = result.feasible
        ? l.text('scheduleGenerated')
        : l.text('scheduleInfeasible');

    final violationText = result.violations
        .map((v) => '• ${v.message}')
        .join('\n');

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: DsSpacing.x4, vertical: DsSpacing.x2),
      child: Stack(
        children: [
          DsInlineAlert(
            title: title,
            message: result.violations.isEmpty
                ? l.text('scheduleReviewMessage')
                : violationText,
            tone: tone,
          ),
          Positioned(
            top: 0,
            right: 0,
            child: IconButton(
              icon: const Icon(Icons.close, size: 16),
              onPressed: onDismiss,
            ),
          ),
        ],
      ),
    );
  }
}
