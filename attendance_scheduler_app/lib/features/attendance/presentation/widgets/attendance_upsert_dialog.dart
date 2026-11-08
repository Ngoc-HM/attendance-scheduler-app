import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/shift_codes.dart';
import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../../auth/domain/entities/user.dart';
import '../providers/attendance_provider.dart';

/// Admin dialog to record / update a single attendance cell.
///
/// Lists only active people. The code list is the selected person's planned
/// codes ([ShiftCodeX.plannedCodesFor] their role) plus "S" (sick), and
/// defaults to the role's first planned code.
class AttendanceUpsertDialog extends ConsumerStatefulWidget {
  const AttendanceUpsertDialog({
    super.key,
    required this.users,
    this.preselectedUserId,
    this.preselectedDate,
    this.preselectedCode,
  });

  final List<User> users;
  final int? preselectedUserId;
  final DateTime? preselectedDate;
  final String? preselectedCode;

  @override
  ConsumerState<AttendanceUpsertDialog> createState() =>
      _AttendanceUpsertDialogState();
}

class _AttendanceUpsertDialogState
    extends ConsumerState<AttendanceUpsertDialog> {
  int? _userId;
  DateTime? _workDate;
  ShiftCode? _code;
  bool _sickCoverMode = false;
  final _noteCtrl = TextEditingController();

  /// Disabled or pending people cannot work a shift.
  late final List<User> _activeUsers = widget.users
      .where((u) => u.status == 'active')
      .toList();

  User? get _selectedUser {
    for (final u in _activeUsers) {
      if (u.id == _userId) return u;
    }
    return null;
  }

  /// The selected person's planned codes plus S; empty until someone is
  /// selected.
  List<ShiftCode> get _codes {
    final user = _selectedUser;
    if (user == null) return const [];
    return [...ShiftCodeX.plannedCodesFor(user.role), ShiftCode.s];
  }

  @override
  void initState() {
    super.initState();
    _workDate = widget.preselectedDate;
    _selectUser(widget.preselectedUserId);
    final preselected = widget.preselectedCode;
    if (preselected != null) {
      final code = _parseCode(preselected);
      if (_codes.contains(code)) _setCode(code);
    }
  }

  /// Select [userId] (ignored unless active) and keep the code valid for the
  /// new person's role: a code outside it falls back to the first planned one.
  void _selectUser(int? userId) {
    _userId = _activeUsers.any((u) => u.id == userId) ? userId : null;
    final codes = _codes;
    if (codes.isEmpty) {
      _code = null;
      _sickCoverMode = false;
    } else if (!codes.contains(_code)) {
      _setCode(codes.first);
    }
  }

  /// Picking S switches on the automatic cover by default.
  void _setCode(ShiftCode code) {
    _code = code;
    _sickCoverMode = code == ShiftCode.s;
  }

  @override
  void dispose() {
    _noteCtrl.dispose();
    super.dispose();
  }

  ShiftCode _parseCode(String c) => switch (c) {
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

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final state = ref.watch(attendanceControllerProvider);

    return DsFormDialog(
      title: l.text('updateAttendance'),
      width: 360,
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Employee selector
          DropdownButton<int>(
            value: _userId,
            isExpanded: true,
            hint: Text(l.text('selectEmployee')),
            items: _activeUsers
                .map(
                  (u) => DropdownMenuItem(
                    value: u.id,
                    child: Text(
                      u.fullName.isNotEmpty ? u.fullName : u.username,
                    ),
                  ),
                )
                .toList(),
            onChanged: (v) => setState(() => _selectUser(v)),
          ),
          const SizedBox(height: DsSpacing.x3),
          // Date picker
          OutlinedButton.icon(
            icon: const Icon(Icons.calendar_today, size: 16),
            label: Text(
              _workDate == null
                  ? l.text('pickDate')
                  : '${_workDate!.year}-'
                        '${_workDate!.month.toString().padLeft(2, '0')}-'
                        '${_workDate!.day.toString().padLeft(2, '0')}',
            ),
            onPressed: () => _pickDate(context),
          ),
          const SizedBox(height: DsSpacing.x3),
          // Code selector
          DropdownButton<ShiftCode>(
            value: _code,
            isExpanded: true,
            items: _codes
                .map((c) => DropdownMenuItem(value: c, child: Text(c.code)))
                .toList(),
            onChanged: (v) {
              if (v != null) setState(() => _setCode(v));
            },
          ),
          if (_code == ShiftCode.s) ...[
            const SizedBox(height: DsSpacing.x2),
            CheckboxListTile(
              value: _sickCoverMode,
              title: Text(l.text('autoAssignCover')),
              dense: true,
              contentPadding: EdgeInsets.zero,
              onChanged: (v) => setState(() => _sickCoverMode = v ?? true),
            ),
          ],
          const SizedBox(height: DsSpacing.x3),
          TextField(
            controller: _noteCtrl,
            decoration: InputDecoration(
              labelText: l.text('note'),
              border: const OutlineInputBorder(),
              isDense: true,
            ),
          ),
          if (state.error != null) ...[
            const SizedBox(height: DsSpacing.x2),
            Text(
              state.error!,
              style: const TextStyle(
                color: DsColors.danger,
                fontSize: DsFontSize.caption,
              ),
            ),
          ],
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: Text(l.text('cancel')),
        ),
        DsPrimaryButton(
          label: l.text('save'),
          loading: state.isMutating,
          onPressed: state.isMutating ||
                  _userId == null ||
                  _workDate == null ||
                  _code == null
              ? null
              : () => _submit(context, l),
        ),
      ],
    );
  }

  Future<void> _pickDate(BuildContext context) async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _workDate ?? now,
      firstDate: DateTime(2000),
      lastDate: DateTime(2100),
    );
    if (picked != null) setState(() => _workDate = picked);
  }

  Future<void> _submit(BuildContext context, AppLocalizations l) async {
    final ctrl = ref.read(attendanceControllerProvider.notifier);
    final code = _code!;
    final note = _noteCtrl.text.isNotEmpty ? _noteCtrl.text : null;
    bool ok;

    if (code == ShiftCode.s && _sickCoverMode) {
      ok = await ctrl.markSick(
        userId: _userId!,
        workDate: _workDate!,
        note: note,
      );
      if (context.mounted && ok) {
        final cover = ref.read(attendanceControllerProvider).lastSickCover;
        final msg = cover?.cover != null
            ? l.text('sickCoverAssigned')
            : (cover?.message ?? l.text('sickCoverNoneAvailable'));
        DsFeedback.show(
          context,
          msg,
          tone: cover?.cover != null ? DsTone.success : DsTone.warning,
        );
      }
    } else {
      ok = await ctrl.upsert(
        userId: _userId!,
        workDate: _workDate!,
        code: code.code,
        note: note,
      );
      if (context.mounted && ok) {
        DsFeedback.show(
          context,
          l.text('attendanceUpdated'),
          tone: DsTone.success,
        );
      }
    }

    if (context.mounted && !ok) {
      final err =
          ref.read(attendanceControllerProvider).error ?? l.text('saveFailed');
      DsFeedback.show(context, err, tone: DsTone.danger);
    } else if (context.mounted) {
      Navigator.of(context).pop(true);
    }
  }
}
