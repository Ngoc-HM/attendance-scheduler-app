import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/shift_codes.dart';
import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../../auth/domain/entities/user.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../domain/entities/attendance_entities.dart';
import '../providers/attendance_provider.dart';
import '../widgets/attendance_upsert_dialog.dart';
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
      return _AttendanceError(message: state.error!, onRetry: _loadMonth);
    }

    final rows = _buildRows(state);

    return DsAttendanceView(
      month: _month,
      rows: rows,
      onPreviousMonth: _prevMonth,
      onNextMonth: _nextMonth,
      onUpdate: isAdmin
          ? () => _showUpsertDialog(context, state.users)
          : () => DsFeedback.show(
                context,
                l.text('adminOnlyAction'),
                tone: DsTone.warning,
              ),
      onHolidays: () => _showHolidaysDialog(context),
    );
  }

  // ── Row builder ───────────────────────────────────────────────────────────

  List<DsAttendanceRowData> _buildRows(AttendanceState state) {
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

    final userMap = <int, User>{for (final u in state.users) u.id: u};

    return byUser.entries.map((entry) {
      final userId = entry.key;
      final records = entry.value;
      final shifts = records.map((r) => _codeToShiftCode(r.code)).toList();
      final user = userMap[userId];
      final name = user != null
          ? (user.fullName.isNotEmpty ? user.fullName : user.username)
          : 'User $userId';
      final role = user?.role.apiValue ?? '';
      final workdays = shifts.fold<int>(0, (s, c) => s + c.workdayValue);
      final absences = shifts.where((c) => c == ShiftCode.x).length;

      return DsAttendanceRowData(
        name: name,
        role: role,
        shifts: shifts,
        workdays: workdays,
        absences: absences,
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
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            DsInlineAlert(
              title: l.text('loadFailed'),
              message: message,
              tone: DsTone.danger,
            ),
            const SizedBox(height: 16),
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
