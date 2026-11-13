import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/api_error_message.dart';
import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../../auth/domain/entities/user.dart';
import '../../../users/data/user_management_datasource.dart';
import '../../data/datasources/time_clock_remote_datasource.dart';
import '../providers/staff_clock_provider.dart';

/// Admin: everyone's check-in/out of a month, with corrections for a
/// forgotten check-out, a missed check-in or a wrong time (2026-11-13).
/// Times are Frankfurt time, as the server reports them.
class StaffClockPage extends ConsumerStatefulWidget {
  const StaffClockPage({super.key});

  @override
  ConsumerState<StaffClockPage> createState() => _StaffClockPageState();
}

class _StaffClockPageState extends ConsumerState<StaffClockPage> {
  /// Show only past days still waiting for a check-out.
  bool _onlyMissing = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback(
      (_) => ref.read(staffClockControllerProvider.notifier).load(),
    );
  }

  Future<void> _edit({StaffClockEntry? entry}) async {
    final saved = await showDialog<bool>(
      context: context,
      builder: (_) => _CorrectDialog(entry: entry),
    );
    if (saved == true && mounted) {
      DsFeedback.show(
        context,
        AppLocalizations.of(context).text('clockSaved'),
        tone: DsTone.success,
      );
    }
  }

  static Widget _filterChip(
    String label, {
    required bool selected,
    required VoidCallback? onSelected,
  }) =>
      ChoiceChip(
        label: Text(label),
        selected: selected,
        showCheckmark: false,
        selectedColor: DsColors.primarySoft,
        side: BorderSide(
          color: selected ? DsColors.primary : DsColors.border,
        ),
        labelStyle: TextStyle(
          color: selected ? DsColors.primary : DsColors.textSecondary,
          fontWeight: selected ? FontWeight.w600 : FontWeight.w400,
        ),
        onSelected: onSelected == null ? null : (_) => onSelected(),
      );

  /// A past day still open; "today" is the business clock's when known.
  bool _missing(StaffClockEntry e) {
    final device = DateTime.now();
    final today = ref.read(staffClockControllerProvider).now?.date ??
        DateTime(device.year, device.month, device.day);
    return e.checkOut == null && e.workDate.isBefore(today);
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final state = ref.watch(staffClockControllerProvider);
    final ctrl = ref.read(staffClockControllerProvider.notifier);
    final missing = state.entries.where(_missing).length;
    final shown = _onlyMissing
        ? state.entries.where(_missing).toList()
        : state.entries;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(DsSpacing.x4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(l.text('staffClockTitle'),
                    style: Theme.of(context).textTheme.titleLarge),
              ),
              DsMonthSwitcher(
                month: state.month,
                onPrevious: () => ctrl.shiftMonth(-1),
                onNext: () => ctrl.shiftMonth(1),
              ),
              const SizedBox(width: DsSpacing.x3),
              DsPrimaryButton(
                label: l.text('clockAddDay'),
                icon: Icons.add,
                onPressed: () => _edit(),
              ),
            ],
          ),
          const SizedBox(height: DsSpacing.x4),
          if (state.isLoading)
            const Center(child: CircularProgressIndicator())
          else if (state.error != null && state.entries.isEmpty)
            Row(
              children: [
                Text(apiErrorMessage(l, state.error),
                    style: const TextStyle(color: DsColors.danger)),
                const SizedBox(width: DsSpacing.x3),
                TextButton(onPressed: ctrl.load, child: Text(l.text('retry'))),
              ],
            )
          else if (state.entries.isEmpty)
            Text(l.text('clockNoEntries'),
                style: const TextStyle(color: DsColors.textMuted))
          else ...[
            Wrap(
              spacing: DsSpacing.x2,
              children: [
                _filterChip(
                  l.text('clockFilterAll'),
                  selected: !_onlyMissing,
                  onSelected: () => setState(() => _onlyMissing = false),
                ),
                _filterChip(
                  '${l.text('clockMissingOut')} ($missing)',
                  selected: _onlyMissing,
                  onSelected: missing == 0 && !_onlyMissing
                      ? null
                      : () => setState(() => _onlyMissing = true),
                ),
              ],
            ),
            const SizedBox(height: DsSpacing.x3),
            DsSurface(
              padding: EdgeInsets.zero,
              child: Column(
                children: [
                  DsClockTableRow.header(l),
                  for (var i = 0; i < shown.length; i++)
                    DsClockTableRow(
                      // The date only on a day's first row: the eye reads
                      // one block per day instead of 30 repeated dates.
                      day: i == 0 ||
                              shown[i - 1].workDate != shown[i].workDate
                          ? '${shown[i].workDate.day.toString().padLeft(2, '0')}/'
                              '${shown[i].workDate.month.toString().padLeft(2, '0')}'
                              ' ${l.shortWeekday(shown[i].workDate)}'
                          : null,
                      dayStart: i > 0 &&
                          shown[i - 1].workDate != shown[i].workDate,
                      person: '${shown[i].code} · ${shown[i].fullName}',
                      checkIn: shown[i].checkIn,
                      checkOut: shown[i].checkOut,
                      note: _missing(shown[i])
                          ? l.text('clockMissingOut')
                          : shown[i].corrected
                              ? l.text('clockCorrected')
                              : null,
                      noteIsAlert: _missing(shown[i]),
                      action: IconButton(
                        icon: const Icon(Icons.edit_outlined, size: 18),
                        tooltip: l.text('edit'),
                        onPressed: () => _edit(entry: shown[i]),
                      ),
                    ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

/// Correct one person's day. A new day picks the person and date; an
/// existing one only changes its times.
class _CorrectDialog extends ConsumerStatefulWidget {
  const _CorrectDialog({this.entry});

  final StaffClockEntry? entry;

  @override
  ConsumerState<_CorrectDialog> createState() => _CorrectDialogState();
}

class _CorrectDialogState extends ConsumerState<_CorrectDialog> {
  late final Future<List<User>> _people;
  int? _userId;
  DateTime? _day;
  TimeOfDay? _in;
  TimeOfDay? _out;

  static TimeOfDay? _parse(String? hm) {
    if (hm == null) return null;
    final parts = hm.split(':');
    return TimeOfDay(hour: int.parse(parts[0]), minute: int.parse(parts[1]));
  }

  static String _hm(TimeOfDay t) =>
      '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';

  @override
  void initState() {
    super.initState();
    final e = widget.entry;
    _userId = e?.userId;
    _day = e?.workDate;
    _in = _parse(e?.checkIn);
    _out = _parse(e?.checkOut);
    _people = ref
        .read(userManagementDataSourceProvider)
        .list()
        .then((users) => [
              for (final u in users)
                if (u.status == 'active' && !u.isAdmin) u,
            ]);
  }

  Future<void> _pickDay() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _day ?? now,
      firstDate: DateTime(now.year - 1),
      lastDate: now,
    );
    if (picked != null) setState(() => _day = picked);
  }

  Future<void> _pickTime(bool isIn) async {
    // Start from the value already set, else the check-in (for a forgotten
    // check-out), else the business clock now — never the device clock,
    // which may sit in another zone.
    final serverNow = _parse(ref.read(staffClockControllerProvider).now?.time);
    final picked = await showTimePicker(
      context: context,
      initialTime: (isIn ? _in : (_out ?? _in)) ?? serverNow ?? TimeOfDay.now(),
      builder: (context, child) => MediaQuery(
        data: MediaQuery.of(context).copyWith(alwaysUse24HourFormat: true),
        child: child!,
      ),
    );
    if (picked != null) setState(() => isIn ? _in = picked : _out = picked);
  }

  Future<void> _save() async {
    final ok = await ref.read(staffClockControllerProvider.notifier).correct(
          userId: _userId!,
          workDate: _day!,
          checkIn: _hm(_in!),
          checkOut: _out == null ? null : _hm(_out!),
        );
    if (ok && mounted) Navigator.of(context).pop(true);
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final state = ref.watch(staffClockControllerProvider);
    final isNew = widget.entry == null;
    final ready = _userId != null && _day != null && _in != null;

    return DsFormDialog(
      title: isNew
          ? l.text('clockAddDay')
          : '${widget.entry!.code} · ${widget.entry!.fullName}',
      width: 380,
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (isNew) ...[
            FutureBuilder<List<User>>(
              future: _people,
              builder: (context, snap) => DropdownButtonFormField<int>(
                initialValue: _userId,
                decoration: InputDecoration(
                  labelText: l.text('clockPerson'),
                  border: const OutlineInputBorder(),
                  isDense: true,
                ),
                items: [
                  for (final u in snap.data ?? const <User>[])
                    DropdownMenuItem(
                        value: u.id, child: Text('${u.code} · ${u.fullName}')),
                ],
                onChanged: (v) => setState(() => _userId = v),
              ),
            ),
            const SizedBox(height: DsSpacing.x3),
            DsSecondaryButton(
              icon: Icons.calendar_today,
              label: _day == null
                  ? l.text('pickDate')
                  : '${_day!.day.toString().padLeft(2, '0')}/'
                      '${_day!.month.toString().padLeft(2, '0')}/${_day!.year}',
              onPressed: _pickDay,
            ),
          ] else
            Text(
              '${_day!.day.toString().padLeft(2, '0')}/'
              '${_day!.month.toString().padLeft(2, '0')}/${_day!.year}',
              style: Theme.of(context).textTheme.titleSmall,
            ),
          const SizedBox(height: DsSpacing.x3),
          Row(
            children: [
              Expanded(
                child: DsSecondaryButton(
                  label:
                      '${l.text('clockCheckIn')}: ${_in == null ? '—' : _hm(_in!)}',
                  onPressed: () => _pickTime(true),
                ),
              ),
              const SizedBox(width: DsSpacing.x2),
              Expanded(
                child: DsSecondaryButton(
                  label:
                      '${l.text('clockCheckOut')}: ${_out == null ? '—' : _hm(_out!)}',
                  onPressed: () => _pickTime(false),
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
          if (state.error != null) ...[
            const SizedBox(height: DsSpacing.x2),
            Text(
              apiErrorMessage(l, state.error),
              style: const TextStyle(
                  color: DsColors.danger, fontSize: DsFontSize.caption),
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
          loading: state.isSaving,
          onPressed: !ready || state.isSaving ? null : _save,
        ),
      ],
    );
  }
}
