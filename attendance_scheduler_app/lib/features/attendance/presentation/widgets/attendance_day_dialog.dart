import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/shift_codes.dart';
import '../../../../core/network/api_error_message.dart';
import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../../auth/domain/entities/user.dart';
import '../../data/datasources/time_clock_remote_datasource.dart';
import '../providers/attendance_provider.dart';

/// Admin: one person's day, opened by tapping its cell in the attendance
/// grid — the attendance code and the check-in/out in one place
/// (owner 2026-11-13). Times are on the business clock, as the server
/// reports them.
class AttendanceDayDialog extends ConsumerStatefulWidget {
  const AttendanceDayDialog({
    super.key,
    required this.user,
    required this.day,
    required this.code,
    this.checkIn,
    this.checkOut,
  });

  final User user;
  final DateTime day;

  /// The day's current attendance code.
  final String code;

  /// The day's punches ("HH:MM"), if any.
  final String? checkIn;
  final String? checkOut;

  @override
  ConsumerState<AttendanceDayDialog> createState() =>
      _AttendanceDayDialogState();
}

class _AttendanceDayDialogState extends ConsumerState<AttendanceDayDialog> {
  late ShiftCode _code = _parse(widget.code);
  bool _sickCover = false;
  late TimeOfDay? _in = _time(widget.checkIn);
  late TimeOfDay? _out = _time(widget.checkOut);
  ClockNow? _now;
  bool _saving = false;
  Object? _error;

  List<ShiftCode> get _codes {
    final codes = [
      ...ShiftCodeX.plannedCodesFor(widget.user.role),
      ShiftCode.s,
    ];
    return codes.contains(_code) ? codes : [_code, ...codes];
  }

  /// A day that has started on the business clock can carry punches.
  bool get _canPunch => _now != null && !widget.day.isAfter(_now!.date);

  @override
  void initState() {
    super.initState();
    ref.read(timeClockRemoteDataSourceProvider).now().then((now) {
      if (mounted) setState(() => _now = now);
    }, onError: (_) {});
  }

  static ShiftCode _parse(String c) => ShiftCode.values.firstWhere(
    (s) => s.code == c,
    orElse: () => ShiftCode.x,
  );

  static TimeOfDay? _time(String? hm) {
    if (hm == null) return null;
    final p = hm.split(':');
    return TimeOfDay(hour: int.parse(p[0]), minute: int.parse(p[1]));
  }

  static String _hm(TimeOfDay t) =>
      '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';

  Future<void> _pickTime(bool isIn) async {
    final picked = await showTimePicker(
      context: context,
      // The value already set, else the check-in, else the business clock.
      initialTime:
          (isIn ? _in : (_out ?? _in)) ?? _time(_now?.time) ?? TimeOfDay.now(),
      builder: (context, child) => MediaQuery(
        data: MediaQuery.of(context).copyWith(alwaysUse24HourFormat: true),
        child: child!,
      ),
    );
    if (picked != null) setState(() => isIn ? _in = picked : _out = picked);
  }

  Future<void> _save(AppLocalizations l) async {
    setState(() {
      _saving = true;
      _error = null;
    });
    final attendance = ref.read(attendanceControllerProvider.notifier);
    String? message;
    var ok = true;

    if (_code.code != widget.code) {
      if (_code == ShiftCode.s && _sickCover) {
        ok = await attendance.markSick(
          userId: widget.user.id,
          workDate: widget.day,
        );
        final cover = ref.read(attendanceControllerProvider).lastSickCover;
        message = cover?.cover != null
            ? l.text('sickCoverAssigned')
            : (cover?.message ?? l.text('sickCoverNoneAvailable'));
      } else {
        ok = await attendance.upsert(
          userId: widget.user.id,
          workDate: widget.day,
          code: _code.code,
        );
      }
      if (!ok) _error = ref.read(attendanceControllerProvider).error;
    }

    final timesChanged =
        _in != _time(widget.checkIn) || _out != _time(widget.checkOut);
    if (ok && _in != null && timesChanged) {
      try {
        await ref
            .read(timeClockRemoteDataSourceProvider)
            .correct(
              userId: widget.user.id,
              workDate: widget.day,
              checkIn: _hm(_in!),
              checkOut: _out == null ? null : _hm(_out!),
            );
      } catch (e) {
        ok = false;
        _error = e;
      }
    }

    ref.invalidate(clockBoardProvider);
    if (!mounted) return;
    if (!ok) {
      setState(() => _saving = false);
      return;
    }
    DsFeedback.show(
      context,
      message ?? l.text('attendanceUpdated'),
      tone: DsTone.success,
    );
    Navigator.of(context).pop(true);
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final name = widget.user.fullName.isNotEmpty
        ? widget.user.fullName
        : widget.user.username;
    final d = widget.day;

    return DsFormDialog(
      title: '${widget.user.code} · $name',
      width: 380,
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            '${d.day.toString().padLeft(2, '0')}/'
            '${d.month.toString().padLeft(2, '0')}/${d.year} · '
            '${l.shortWeekday(d)}',
            style: Theme.of(context).textTheme.titleSmall,
          ),
          const SizedBox(height: DsSpacing.x3),
          DropdownButtonFormField<ShiftCode>(
            initialValue: _code,
            decoration: InputDecoration(
              labelText: l.text('clockCode'),
              border: const OutlineInputBorder(),
              isDense: true,
            ),
            items: [
              for (final c in _codes)
                DropdownMenuItem(value: c, child: Text(c.code)),
            ],
            onChanged: (v) {
              if (v != null) {
                setState(() {
                  _code = v;
                  _sickCover = v == ShiftCode.s;
                });
              }
            },
          ),
          if (_code == ShiftCode.s && _code.code != widget.code)
            CheckboxListTile(
              value: _sickCover,
              title: Text(l.text('autoAssignCover')),
              dense: true,
              contentPadding: EdgeInsets.zero,
              onChanged: (v) => setState(() => _sickCover = v ?? false),
            ),
          if (_canPunch) ...[
            const SizedBox(height: DsSpacing.x3),
            Row(
              children: [
                Expanded(
                  child: DsSecondaryButton(
                    label:
                        '${l.text('clockIn')}: ${_in == null ? '—' : _hm(_in!)}',
                    onPressed: () => _pickTime(true),
                  ),
                ),
                const SizedBox(width: DsSpacing.x2),
                // The clear button sits inside the check-out button, so the
                // row spans exactly the code field's width.
                Expanded(
                  child: Stack(
                    alignment: Alignment.centerRight,
                    children: [
                      SizedBox(
                        width: double.infinity,
                        child: DsSecondaryButton(
                          label:
                              '${l.text('clockOut')}: ${_out == null ? '—' : _hm(_out!)}',
                          onPressed: _in == null
                              ? null
                              : () => _pickTime(false),
                        ),
                      ),
                      if (_out != null)
                        IconButton(
                          icon: const Icon(Icons.close, size: 16),
                          tooltip: l.text('clockClearOut'),
                          onPressed: () => setState(() => _out = null),
                        ),
                    ],
                  ),
                ),
              ],
            ),
          ],
          if (_error != null) ...[
            const SizedBox(height: DsSpacing.x2),
            Text(
              apiErrorMessage(l, _error, fallbackKey: 'saveFailed'),
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
          onPressed: () => Navigator.of(context).pop(false),
          child: Text(l.text('cancel')),
        ),
        DsPrimaryButton(
          label: l.text('save'),
          loading: _saving,
          onPressed: _saving ? null : () => _save(l),
        ),
      ],
    );
  }
}
