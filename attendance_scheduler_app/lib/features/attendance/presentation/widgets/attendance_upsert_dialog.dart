import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/shift_codes.dart';
import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../../auth/domain/entities/user.dart';
import '../providers/attendance_provider.dart';

/// Admin dialog to record / update a single attendance cell.
/// Supports all AttendanceCode values including "S" (sick).
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
  ShiftCode _code = ShiftCode.a;
  bool _sickCoverMode = false;
  final _noteCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _userId = widget.preselectedUserId;
    _workDate = widget.preselectedDate;
    if (widget.preselectedCode != null) {
      _code = _parseCode(widget.preselectedCode!);
    }
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
              items: widget.users
                  .map(
                    (u) => DropdownMenuItem(
                      value: u.id,
                      child: Text(
                          u.fullName.isNotEmpty ? u.fullName : u.username),
                    ),
                  )
                  .toList(),
              onChanged: (v) => setState(() => _userId = v),
            ),
            const SizedBox(height: 12),
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
            const SizedBox(height: 12),
            // Code selector
            DropdownButton<ShiftCode>(
              value: _code,
              isExpanded: true,
              items: ShiftCode.values
                  .map(
                    (c) => DropdownMenuItem(
                      value: c,
                      child: Text(c.code),
                    ),
                  )
                  .toList(),
              onChanged: (v) {
                if (v != null) {
                  setState(() {
                    _code = v;
                    // Auto-enable sick-cover mode when S is selected.
                    _sickCoverMode = v == ShiftCode.s;
                  });
                }
              },
            ),
            if (_code == ShiftCode.s) ...[
              const SizedBox(height: 8),
              CheckboxListTile(
                value: _sickCoverMode,
                title: Text(l.text('autoAssignCover')),
                dense: true,
                contentPadding: EdgeInsets.zero,
                onChanged: (v) =>
                    setState(() => _sickCoverMode = v ?? true),
              ),
            ],
            const SizedBox(height: 12),
            TextField(
              controller: _noteCtrl,
              decoration: InputDecoration(
                labelText: l.text('note'),
                border: const OutlineInputBorder(),
                isDense: true,
              ),
            ),
            if (state.error != null) ...[
              const SizedBox(height: 8),
              Text(
                state.error!,
                style: const TextStyle(color: DsColors.danger, fontSize: 12),
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
          onPressed: state.isMutating || _userId == null || _workDate == null
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
      firstDate: DateTime(now.year - 1),
      lastDate: DateTime(now.year + 1),
    );
    if (picked != null) setState(() => _workDate = picked);
  }

  Future<void> _submit(BuildContext context, AppLocalizations l) async {
    final ctrl = ref.read(attendanceControllerProvider.notifier);
    bool ok;

    if (_code == ShiftCode.s && _sickCoverMode) {
      ok = await ctrl.markSick(userId: _userId!, workDate: _workDate!);
      if (context.mounted && ok) {
        final cover = ref.read(attendanceControllerProvider).lastSickCover;
        final msg = cover?.cover != null
            ? l.text('sickCoverAssigned')
            : (cover?.message ?? l.text('sickCoverNoneAvailable'));
        DsFeedback.show(context, msg,
            tone: cover?.cover != null ? DsTone.success : DsTone.warning);
      }
    } else {
      ok = await ctrl.upsert(
        userId: _userId!,
        workDate: _workDate!,
        code: _code.code,
        note: _noteCtrl.text.isNotEmpty ? _noteCtrl.text : null,
      );
      if (context.mounted && ok) {
        DsFeedback.show(context, l.text('attendanceUpdated'),
            tone: DsTone.success);
      }
    }

    if (context.mounted && !ok) {
      final err = ref.read(attendanceControllerProvider).error ?? 'error';
      DsFeedback.show(context, err, tone: DsTone.danger);
    } else if (context.mounted) {
      Navigator.of(context).pop(true);
    }
  }
}
