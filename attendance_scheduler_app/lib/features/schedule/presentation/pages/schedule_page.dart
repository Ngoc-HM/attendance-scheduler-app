import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/shift_codes.dart';
import '../../../../core/network/api_exception.dart';
import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../../auth/domain/entities/user.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../../flights/data/datasources/flights_remote_datasource.dart';
import '../../../flights/data/models/flight_day_model.dart';
import '../../domain/entities/schedule_entities.dart';
import '../providers/schedule_provider.dart';
import '../providers/self_arrange_provider.dart';
import '../providers/shift_change_provider.dart';
import '../widgets/self_arrange_pending_panel.dart';
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
    ref
        .read(scheduleControllerProvider.notifier)
        .load(_month.year, _month.month, isAdmin: isAdmin);
    if (isAdmin) {
      ref.read(shiftChangeControllerProvider.notifier).load(all: true);
      ref.read(selfArrangeAdminControllerProvider.notifier).load();
    } else {
      ref.read(shiftChangeControllerProvider.notifier).load();
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
    final me = ref.watch(authControllerProvider).user;
    final scheduleState = ref.watch(scheduleControllerProvider);

    if (scheduleState.isLoading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    // Non-admin gets 404 for drafts: show an empty roster with a neutral
    // message (no "generate" hint) and keep the own-requests panel below.
    // The state may still hold the previous month's schedule, so no rows.
    final notPublished = scheduleState.error != null && !isAdmin;
    final rows = notPublished
        ? const <DsRosterRowData>[]
        : _buildRows(scheduleState);

    return Column(
      children: [
        Expanded(
          child: DsScheduleView(
            month: _month,
            rows: rows,
            flightLabels: _flightLabels,
            onPreviousMonth: _prevMonth,
            onNextMonth: _nextMonth,
            onGenerate: isAdmin ? () => _onGenerate(context, l) : null,
            onPublish: isAdmin ? () => _onPublish(context, l) : null,
            emptyMessage: isAdmin ? null : l.text('scheduleNotPublishedYet'),
            onCellTap: isAdmin
                ? (row, dayIndex) => _onEditCell(context, l, row, dayIndex)
                : me == null
                ? null
                : (row, dayIndex) => _onRequestChange(context, l, me, dayIndex),
            // Employees may only ask to change their own cells.
            isRowTappable: isAdmin || me == null
                ? null
                : (row) => row.id == me.id,
          ),
        ),
        if (!isAdmin && me != null) ...[
          const Divider(height: 1),
          MyShiftChangeRequestsPanel(
            codeById: {for (final p in scheduleState.people) p.id: p.code},
          ),
        ],
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
                  onPressed: () => setState(() => _showShiftChanges = false),
                ),
              ],
            ),
          ),
          const ShiftChangePendingPanel(),
          // Batch self-arrange approvals (owner 2026-07-09) — approving
          // rewrites schedule cells, so reload the grid afterwards.
          SelfArrangePendingPanel(onDecided: _loadMonth),
        ],
        if (isAdmin)
          Padding(
            padding: const EdgeInsets.symmetric(
              horizontal: DsSpacing.x4,
              vertical: DsSpacing.x2,
            ),
            child: TextButton.icon(
              icon: Icon(
                _showShiftChanges
                    ? Icons.expand_less
                    : Icons.swap_horiz_outlined,
              ),
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

    // Build user id→code map (employee code, e.g. "A3") — admin from /users,
    // employees from the name-free /users/directory.
    final userMap = <int, String>{for (final p in state.people) p.id: p.code};

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
      final shifts = assignments.map((a) => _codeToShiftCode(a.code)).toList();
      // Same anonymous fallback as the leaves list when the code is unknown.
      final name = userMap[userId] ?? 'ID $userId';
      final role = _roleLabel(userId, state);

      final arrivals = shifts
          .where((s) => s == ShiftCode.a || s == ShiftCode.aD)
          .length;
      final departures = shifts
          .where((s) => s == ShiftCode.d || s == ShiftCode.aD)
          .length;
      final offDays = shifts.where((s) => s == ShiftCode.x).length;

      return DsRosterRowData(
        id: userId,
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
    final person = state.people.where((p) => p.id == userId).firstOrNull;
    return person?.role.apiValue ?? '';
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

  /// True when the month has at least one day with flight data entered.
  Future<bool> _monthHasFlights() async {
    try {
      final days = await ref
          .read(flightsDataSourceProvider)
          .listDays(_month.year, _month.month);
      return days.any((d) => d.flightPairs > 0 || d.flights.isNotEmpty);
    } catch (_) {
      return true; // can't tell → don't block the admin with a false warning
    }
  }

  /// Confirm dialog when generating a month with NO flight data (owner
  /// 2026-07-17): without flights the roster gets zero A/D duties, which
  /// looks broken — warn first instead of silently producing it.
  Future<bool> _confirmGenerateWithoutFlights(
    BuildContext context,
    AppLocalizations l,
  ) async {
    final proceed = await showDialog<bool>(
      context: context,
      builder: (context) => DsFormDialog(
        title: l.text('flightsMissingTitle'),
        width: 400,
        content: Text(l.text('flightsMissingBody')),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text(l.text('cancel')),
          ),
          DsPrimaryButton(
            label: l.text('generateAnyway'),
            onPressed: () => Navigator.of(context).pop(true),
          ),
        ],
      ),
    );
    return proceed == true;
  }

  /// The backend refuses (409) to regenerate a published or manually edited
  /// month without force: regenerating drops the manual edits and resets the
  /// month to draft, so the admin must confirm that first.
  Future<bool> _confirmRegenerate(
    BuildContext context,
    AppLocalizations l,
  ) async {
    final proceed = await showDialog<bool>(
      context: context,
      builder: (context) => DsFormDialog(
        title: l.text('regenerateConfirmTitle'),
        width: 400,
        content: Text(l.text('regenerateConfirmBody')),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text(l.text('cancel')),
          ),
          DsPrimaryButton(
            label: l.text('regenerate'),
            onPressed: () => Navigator.of(context).pop(true),
          ),
        ],
      ),
    );
    return proceed == true;
  }

  /// The solve can take ~30s, so block with a spinner overlay meanwhile.
  Future<void> _runGenerate(
    BuildContext context,
    AppLocalizations l, {
    bool force = false,
  }) =>
      DsBusy.run(
        context,
        l.text('generatingSchedule'),
        () => ref
            .read(scheduleControllerProvider.notifier)
            .generate(_month.year, _month.month, force: force),
      );

  Future<void> _onGenerate(BuildContext context, AppLocalizations l) async {
    // Months without flight data still solve, but yield zero flight duties —
    // surface that BEFORE generating so the admin isn't surprised.
    if (!await _monthHasFlights()) {
      if (!context.mounted) return;
      if (!await _confirmGenerateWithoutFlights(context, l)) return;
    }
    if (!context.mounted) return;
    try {
      await _runGenerate(context, l);
    } on ApiException catch (e) {
      if (e.statusCode != 409) rethrow;
      if (!context.mounted) return;
      if (!await _confirmRegenerate(context, l)) return;
      if (!context.mounted) return;
      await _runGenerate(context, l, force: true);
    }
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
      } else if (result != null && result.violations.isNotEmpty) {
        DsFeedback.show(
          context,
          '${l.text('scheduleGenerated')} ${result.violations.length} '
          '${l.text('ruleWarnings')}',
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

  /// F-09 admin cell edit: tap a roster cell → pick a code → save. The edit
  /// is ALWAYS saved server-side; recheck warnings come back for display.
  /// Only the row role's planned codes are offered (never S — the backend
  /// rejects it on the planned grid).
  Future<void> _onEditCell(
    BuildContext context,
    AppLocalizations l,
    DsRosterRowData row,
    int dayIndex,
  ) async {
    final userId = row.id;
    if (userId == null) return;
    final workDate = DateTime(_month.year, _month.month, dayIndex + 1);
    final current = row.shifts[dayIndex];
    final allowed = ShiftCodeX.plannedCodesFor(UserRoleX.fromApi(row.role));
    // A current code outside the role's set (legacy data) shows as the hint
    // until the admin picks an allowed one.
    ShiftCode? selected = allowed.contains(current) ? current : null;

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => DsFormDialog(
          title:
              '${l.text('editCell')} — ${row.name} · ${workDate.day}/${workDate.month}',
          width: 320,
          content: DropdownButton<ShiftCode>(
            value: selected,
            isExpanded: true,
            hint: Text(current.code),
            items: allowed
                .map((c) => DropdownMenuItem(value: c, child: Text(c.code)))
                .toList(),
            onChanged: (v) {
              if (v != null) setState(() => selected = v);
            },
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: Text(l.text('cancel')),
            ),
            DsPrimaryButton(
              label: l.text('save'),
              onPressed: selected == null
                  ? null
                  : () => Navigator.of(context).pop(true),
            ),
          ],
        ),
      ),
    );
    final code = selected;
    if (confirmed != true || code == null || !mounted) return;

    final warnings = await ref
        .read(scheduleControllerProvider.notifier)
        .overrideCell(userId: userId, workDate: workDate, code: code.code);
    if (!context.mounted) return;
    if (warnings == null) {
      DsFeedback.show(
        context,
        ref.read(scheduleControllerProvider).error ?? l.text('loadFailed'),
        tone: DsTone.danger,
      );
    } else if (warnings.isEmpty) {
      DsFeedback.show(context, l.text('cellSaved'), tone: DsTone.success);
    } else {
      // Keep the top-right toast concise; detailed diagnostics must never
      // expand into a screen-sized notification.
      DsFeedback.show(
        context,
        '${l.text('cellSaved')} ${warnings.length} ${l.text('ruleWarnings')}',
        tone: DsTone.warning,
      );
    }
  }

  /// Employee taps one of their own cells → shift-change request (decision
  /// #8). The admin decides it later; the own-requests list reloads here.
  Future<void> _onRequestChange(
    BuildContext context,
    AppLocalizations l,
    User me,
    int dayIndex,
  ) async {
    final submitted = await showDialog<bool>(
      context: context,
      builder: (_) => ShiftChangeRequestDialog(
        workDate: DateTime(_month.year, _month.month, dayIndex + 1),
        role: me.role,
        people: ref.read(scheduleControllerProvider).people,
        currentUserId: me.id,
      ),
    );
    if (submitted == null || !context.mounted) return; // cancelled
    if (submitted) {
      DsFeedback.show(
        context,
        l.text('shiftChangeSubmitted'),
        tone: DsTone.success,
      );
      ref.read(shiftChangeControllerProvider.notifier).load();
    } else {
      DsFeedback.show(
        context,
        ref.read(shiftChangeControllerProvider).error ?? l.text('loadFailed'),
        tone: DsTone.danger,
      );
    }
  }

  Future<void> _onPublish(BuildContext context, AppLocalizations l) async {
    await DsBusy.run(
      context,
      l.text('publishingSchedule'),
      () => ref.read(scheduleControllerProvider.notifier).publish(),
    );
    final state = ref.read(scheduleControllerProvider);
    if (!context.mounted) return;
    if (state.error != null) {
      DsFeedback.show(context, state.error!, tone: DsTone.danger);
    } else {
      DsFeedback.show(
        context,
        l.text('schedulePublished'),
        tone: DsTone.success,
      );
    }
  }
}
