import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../attendance/data/datasources/time_clock_remote_datasource.dart';
import '../../../attendance/presentation/clock_board_marks.dart';
import '../../../../core/constants/shift_codes.dart';
import '../../../../core/network/api_error_message.dart';
import '../../../../core/network/api_exception.dart';
import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../../auth/domain/entities/user.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../../flights/data/datasources/flights_remote_datasource.dart';
import '../../../flights/data/models/flight_day_model.dart';
import '../../domain/entities/schedule_entities.dart';
import '../providers/schedule_provider.dart';
import '../providers/shift_change_provider.dart';
import '../widgets/shift_change_dialog.dart';
import '../widgets/violation_line.dart';

class SchedulePage extends ConsumerStatefulWidget {
  const SchedulePage({super.key, this.initialMonth});

  /// Month shown first (only its year and month count). Defaults to the
  /// current month; tests and goldens pin it so they do not depend on the
  /// clock.
  final DateTime? initialMonth;

  @override
  ConsumerState<SchedulePage> createState() => _SchedulePageState();
}

class _SchedulePageState extends ConsumerState<SchedulePage> {
  late DateTime _month;
  bool _showShiftChanges = false;
  Map<int, String> _flightLabels = const {}; // day-of-month → FLT codes

  @override
  void initState() {
    super.initState();
    final start = widget.initialMonth ?? DateTime.now();
    _month = DateTime(start.year, start.month);
    WidgetsBinding.instance.addPostFrameCallback((_) => _loadMonth());
  }

  void _loadMonth() {
    final isAdmin = ref.read(isAdminProvider);
    ref
        .read(scheduleControllerProvider.notifier)
        .load(_month.year, _month.month, isAdmin: isAdmin);
    if (isAdmin) {
      ref.read(shiftChangeControllerProvider.notifier).load(all: true);
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

    // Only the month on screen is ever drawn or published (A3): a month
    // without a schedule (404) shows the empty state and no Publish button.
    final onScreen = scheduleState.holds(_month.year, _month.month);
    // Admin: each day of the published roster read against the punches —
    // light red when missed, light yellow when adjusted (owner 2026-11-13).
    final board = isAdmin && onScreen
        ? ref.watch(clockBoardProvider((_month.year, _month.month))).value ??
            const <ClockBoardCell>[]
        : const <ClockBoardCell>[];
    final rows = onScreen
        ? _buildRows(scheduleState, board, l)
        : const <DsRosterRowData>[];
    final violations = isAdmin && onScreen
        ? (scheduleState.violations ?? const <ConstraintViolation>[])
        : const <ConstraintViolation>[];

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
            onPublish: isAdmin && onScreen
                ? () => _onPublish(context, l)
                : null,
            emptyMessage: _emptyMessage(l, scheduleState, isAdmin),
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
        if (violations.isNotEmpty) ...[
          const Divider(height: 1),
          _ViolationsPanel(
            lines: [
              for (final v in violations) _violationLine(l, v, scheduleState),
            ],
          ),
        ],
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
          // The page, not the panel row, shows the decision and reloads the
          // grid: the row leaves the tree once its request is decided.
          ShiftChangePendingPanel(
            codeById: {for (final p in scheduleState.people) p.id: p.code},
            onDecided: _onShiftChangeDecided,
          ),
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

  /// Empty-roster text: a failed load names the backend detail; a month
  /// with no schedule (404) gets the admin "generate" hint (null = the
  /// view's default) or the employee "not published" note. Only a failed
  /// load counts here: a failed generate is a toast, not "could not load".
  String? _emptyMessage(
    AppLocalizations l,
    ScheduleState state,
    bool isAdmin,
  ) {
    final error = state.loadError;
    if (error != null && state.loadErrorStatus != 404) {
      return '${l.text('scheduleLoadFailed')} ${apiErrorMessage(l, error)}';
    }
    return isAdmin ? null : l.text('scheduleNotPublishedYet');
  }

  /// "2026-06-03 · A1 — message"; the date and code parts are left out when
  /// the violation is not tied to a day or a person, and the date part when
  /// the message already starts with it ([violationLine]).
  String _violationLine(
    AppLocalizations l,
    ConstraintViolation v,
    ScheduleState state,
  ) {
    final userId = v.userId;
    return violationLine(
      v,
      userLabel: userId == null
          ? null
          : state.people.where((p) => p.id == userId).firstOrNull?.code ??
              l.userFallback(userId),
    );
  }

  List<DsRosterRowData> _buildRows(
    ScheduleState state,
    List<ClockBoardCell> board,
    AppLocalizations l,
  ) {
    final clock = clockBoardByDay(board, _month);
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

      final cells = [
        for (final a in assignments) clock[(userId, a.workDate.day)],
      ];

      return DsRosterRowData(
        id: userId,
        name: name,
        role: role,
        shifts: shifts,
        arrivals: arrivals,
        departures: departures,
        offDays: offDays,
        dayNotes: [for (final c in cells) c == null ? null : clockNote(c, l)],
        dayMarks: [for (final c in cells) c == null ? null : clockMark(c)],
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
      DsFeedback.show(
        context,
        apiErrorMessage(l, state.error),
        tone: DsTone.danger,
      );
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
      final nextMonth = result?.nextMonthWarnings ?? const <String>[];
      if (nextMonth.isNotEmpty) {
        await _showNextMonthWarnings(context, l, nextMonth);
      }
    }
  }

  /// Regenerating a month can break the first week of the following month
  /// when that one is already generated (owner 2026-11-13): list what broke.
  Future<void> _showNextMonthWarnings(
    BuildContext context,
    AppLocalizations l,
    List<String> lines,
  ) =>
      showDialog<void>(
        context: context,
        builder: (context) => DsFormDialog(
          title: l.text('nextMonthBrokenTitle'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(l.text('nextMonthBrokenBody')),
              const SizedBox(height: DsSpacing.x2),
              RuleWarningsList(lines: lines),
            ],
          ),
          actions: [
            DsPrimaryButton(
              label: l.text('close'),
              onPressed: () => Navigator.of(context).pop(),
            ),
          ],
        ),
      );

  /// A shift-change request was decided (admin panel). Approving rewrites
  /// schedule cells, so the grid reloads at once; the backend's rule
  /// warnings are listed in full instead of a one-line toast.
  Future<void> _onShiftChangeDecided(ShiftChangeRequest decided) async {
    if (!mounted) return;
    final l = AppLocalizations.of(context);
    if (decided.status != 'approved') {
      DsFeedback.show(context, l.text('requestRejected'), tone: DsTone.success);
      return;
    }
    _loadMonth();
    ref.invalidate(clockBoardProvider);
    if (decided.warnings.isEmpty) {
      DsFeedback.show(context, l.text('requestApproved'), tone: DsTone.success);
      return;
    }
    await showDialog<void>(
      context: context,
      builder: (context) => DsFormDialog(
        title: l.text('approvedWithWarnings'),
        content: RuleWarningsList(lines: decided.warnings),
        actions: [
          DsPrimaryButton(
            label: l.text('close'),
            onPressed: () => Navigator.of(context).pop(),
          ),
        ],
      ),
    );
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
    // An edited cell turns light yellow: re-read the day tints.
    ref.invalidate(clockBoardProvider);
    if (!context.mounted) return;
    if (warnings == null) {
      DsFeedback.show(
        context,
        apiErrorMessage(
          l,
          ref.read(scheduleControllerProvider).error,
          fallbackKey: 'actionFailed',
        ),
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
        apiErrorMessage(
          l,
          ref.read(shiftChangeControllerProvider).error,
          fallbackKey: 'actionFailed',
        ),
        tone: DsTone.danger,
      );
    }
  }

  /// Publishes the month on screen (A3). The rules are re-checked first
  /// (C2): any violation, or a failed check, needs the admin's confirmation.
  Future<void> _onPublish(BuildContext context, AppLocalizations l) async {
    final year = _month.year;
    final month = _month.month;
    final controller = ref.read(scheduleControllerProvider.notifier);
    final violations = await DsBusy.run(
      context,
      l.text('checkingRules'),
      controller.refreshViolations,
    );
    if (!context.mounted) return;
    if (violations == null || violations.isNotEmpty) {
      final state = ref.read(scheduleControllerProvider);
      final proceed = await _confirmPublish(
        context,
        l,
        violations == null
            ? null
            : [for (final v in violations) _violationLine(l, v, state)],
      );
      if (!proceed || !context.mounted) return;
    }
    final ok = await DsBusy.run(
      context,
      l.text('publishingSchedule'),
      () => controller.publish(year: year, month: month),
    );
    if (!context.mounted) return;
    if (!ok) {
      DsFeedback.show(
        context,
        apiErrorMessage(
          l,
          ref.read(scheduleControllerProvider).error,
          fallbackKey: 'actionFailed',
        ),
        tone: DsTone.danger,
      );
    } else {
      DsFeedback.show(
        context,
        l.text('schedulePublished'),
        tone: DsTone.success,
      );
    }
  }

  /// Lists the month's rule violations ([lines]) — or says the check could
  /// not run (null) — and lets the admin publish anyway or cancel.
  Future<bool> _confirmPublish(
    BuildContext context,
    AppLocalizations l,
    List<String>? lines,
  ) async {
    final proceed = await showDialog<bool>(
      context: context,
      builder: (context) => DsFormDialog(
        title: l.text(
          lines == null ? 'rulesNotCheckedTitle' : 'publishWithViolationsTitle',
        ),
        width: 520,
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              lines == null
                  ? l.text('rulesCheckFailed')
                  : l.text('publishWithViolationsBody'),
            ),
            if (lines != null) ...[
              const SizedBox(height: DsSpacing.x3),
              RuleWarningsList(lines: lines),
            ],
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text(l.text('cancel')),
          ),
          DsPrimaryButton(
            label: l.text('publishAnyway'),
            onPressed: () => Navigator.of(context).pop(true),
          ),
        ],
      ),
    );
    return proceed == true;
  }
}

/// Admin strip under the roster: how many hard rules the month on screen
/// breaks right now (C2), expandable to the full list.
class _ViolationsPanel extends StatelessWidget {
  const _ViolationsPanel({required this.lines});

  final List<String> lines;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return ExpansionTile(
      leading: const Icon(Icons.rule_outlined, color: DsColors.warning),
      title: Text('${lines.length} ${l.text('ruleViolationsInMonth')}'),
      childrenPadding: const EdgeInsets.fromLTRB(
        DsSpacing.x4,
        0,
        DsSpacing.x4,
        DsSpacing.x3,
      ),
      children: [RuleWarningsList(lines: lines, maxHeight: 200)],
    );
  }
}
