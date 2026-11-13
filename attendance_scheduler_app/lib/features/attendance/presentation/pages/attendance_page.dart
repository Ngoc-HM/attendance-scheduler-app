import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/shift_codes.dart';
import '../../../../core/network/api_error_message.dart';
import '../../../../core/network/api_exception.dart';
import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../../auth/domain/entities/user.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../data/datasources/time_clock_remote_datasource.dart';
import '../../domain/entities/attendance_entities.dart';
import '../../domain/entities/calculations_entities.dart';
import '../clock_board_marks.dart';
import '../providers/attendance_provider.dart';
import '../widgets/attendance_upsert_dialog.dart';
import '../widgets/close_month_dialog.dart';
import '../widgets/holidays_dialog.dart';

/// isAdmin selector — avoids rebuilding the whole page on unrelated auth changes.
final _isAdminProvider = Provider<bool>(
  (ref) => ref.watch(authControllerProvider).user?.isAdmin ?? false,
);

class AttendancePage extends ConsumerStatefulWidget {
  const AttendancePage({super.key});

  @override
  ConsumerState<AttendancePage> createState() => _AttendancePageState();
}

class _AttendancePageState extends ConsumerState<AttendancePage> {
  DateTime _month = DateTime(DateTime.now().year, DateTime.now().month);

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _loadMonth());
  }

  void _loadMonth() {
    final isAdmin = ref.read(_isAdminProvider);
    ref
        .read(attendanceControllerProvider.notifier)
        .load(_month.year, _month.month, isAdmin: isAdmin);
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
    final isAdmin = ref.watch(_isAdminProvider);
    final state = ref.watch(attendanceControllerProvider);

    if (state.isLoading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    if (state.error != null && state.records.isEmpty) {
      return _AttendanceError(
        message: apiErrorMessage(l, state.error),
        onRetry: _loadMonth,
      );
    }

    final me = ref.watch(authControllerProvider.select((auth) => auth.user));
    // Admin: the check-in/out of each day, read against its code.
    final board = isAdmin
        ? ref.watch(clockBoardProvider((_month.year, _month.month))).value ??
            const <ClockBoardCell>[]
        : const <ClockBoardCell>[];
    final rows = _buildRows(state, me, l, board);

    // Employees get a read-only view of their own month (GET /attendance/me):
    // every admin action is null, so DsAttendanceView hides its button.
    return DsAttendanceView(
      month: _month,
      rows: rows,
      onPreviousMonth: _prevMonth,
      onNextMonth: _nextMonth,
      onUpdate: isAdmin ? () => _showUpsertDialog(context, state.users) : null,
      onHolidays: isAdmin ? () => _showHolidaysDialog(context) : null,
      onCloseMonth: isAdmin ? _closeMonth : null,
    );
  }

  // ── Month close (F-14) ────────────────────────────────────────────────────

  /// Confirm → POST close for the month on screen → show the stored carry-over
  /// balances. Uses the State's own [context]/[mounted] across the awaits.
  Future<void> _closeMonth() async {
    final l = AppLocalizations.of(context);
    final month = _month;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => DsFormDialog(
        title: l.closeMonthConfirmTitle(month),
        content: Text(l.text('closeMonthConfirmMessage')),
        actions: [
          DsTextAction(
            label: l.cancel,
            onPressed: () => Navigator.of(dialogContext).pop(false),
          ),
          DsPrimaryButton(
            label: l.text('closeMonth'),
            onPressed: () => Navigator.of(dialogContext).pop(true),
          ),
        ],
      ),
    );
    if (!(confirmed ?? false) || !mounted) return;

    final MonthCloseResult result;
    try {
      result = await ref
          .read(attendanceControllerProvider.notifier)
          .closeMonth(month.year, month.month);
    } on ApiException catch (e) {
      if (mounted) {
        DsFeedback.show(context, apiErrorMessage(l, e), tone: DsTone.danger);
      }
      return;
    } catch (_) {
      if (mounted) {
        DsFeedback.show(
          context,
          l.text('closeMonthFailed'),
          tone: DsTone.danger,
        );
      }
      return;
    }
    if (!mounted) return;

    final users = ref.read(attendanceControllerProvider).users;
    await showDialog<void>(
      context: context,
      builder: (_) => CloseMonthResultDialog(result: result, users: users),
    );
  }

  // ── Row builder ───────────────────────────────────────────────────────────

  List<DsAttendanceRowData> _buildRows(
    AttendanceState state,
    User? me,
    AppLocalizations l,
    List<ClockBoardCell> board,
  ) {
    final clock = {
      for (final c in board)
        if (c.workDate.year == _month.year && c.workDate.month == _month.month)
          (c.userId, c.workDate.day): c,
    };
    final byUser = <int, List<AttendanceRecord>>{};
    for (final r in state.records) {
      if (r.workDate.year == _month.year &&
          r.workDate.month == _month.month) {
        byUser.putIfAbsent(r.userId, () => []).add(r);
      }
    }
    for (final list in byUser.values) {
      list.sort((a, b) => a.workDate.compareTo(b.workDate));
    }

    // Admin: the full roster. Employee: GET /users is admin-only and the
    // records are their own, so the signed-in user names the single row.
    final userMap = <int, User>{
      for (final u in [?me, ...state.users]) u.id: u,
    };

    final daysInMonth = DateTime(_month.year, _month.month + 1, 0).day;

    return byUser.entries.map((entry) {
      final userId = entry.key;
      final records = entry.value;
      final recordByDay = {for (final r in records) r.workDate.day: r};
      final shifts = [
        for (var day = 1; day <= daysInMonth; day++)
          _codeToShiftCode(recordByDay[day]?.code ?? 'X'),
      ];
      final user = userMap[userId];
      final name = user != null
          ? (user.fullName.isNotEmpty ? user.fullName : user.username)
          : l.userFallback(userId);
      final role = user?.role.apiValue ?? '';
      final workdays = shifts.fold<int>(0, (s, c) => s + c.workdayValue);
      final absences = shifts.where((c) => c == ShiftCode.x).length;

      final cells = [
        for (var day = 1; day <= daysInMonth; day++) clock[(userId, day)],
      ];

      return DsAttendanceRowData(
        name: name,
        role: role,
        shifts: shifts,
        workdays: workdays,
        absences: absences,
        dayNotes: [for (final c in cells) c == null ? null : clockNote(c, l)],
        dayMarks: [for (final c in cells) c == null ? null : clockMark(c)],
      );
    }).toList();
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

  // ── Dialogs ───────────────────────────────────────────────────────────────

  Future<void> _showUpsertDialog(
      BuildContext context, List<User> users) async {
    await showDialog<bool>(
      context: context,
      builder: (_) => AttendanceUpsertDialog(users: users),
    );
    // A new code can make a day due at work (or off): re-read the board.
    ref.invalidate(clockBoardProvider);
  }

  Future<void> _showHolidaysDialog(BuildContext context) async {
    await showDialog<void>(
      context: context,
      builder: (_) => HolidaysDialog(year: _month.year),
    );
  }
}

// ── Error widget ──────────────────────────────────────────────────────────────

class _AttendanceError extends StatelessWidget {
  const _AttendanceError({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(DsSpacing.x6),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            DsInlineAlert(
              title: l.text('loadFailed'),
              message: message,
              tone: DsTone.danger,
            ),
            const SizedBox(height: DsSpacing.x4),
            DsSecondaryButton(
              label: l.text('retry'),
              icon: Icons.refresh,
              onPressed: onRetry,
            ),
          ],
        ),
      ),
    );
  }
}
