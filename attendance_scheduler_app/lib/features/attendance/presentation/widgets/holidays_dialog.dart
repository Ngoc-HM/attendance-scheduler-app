import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../domain/entities/attendance_entities.dart';
import '../providers/attendance_provider.dart';

/// Admin dialog to list, add, and delete public holidays for the given year.
class HolidaysDialog extends ConsumerStatefulWidget {
  const HolidaysDialog({super.key, required this.year});

  final int year;

  @override
  ConsumerState<HolidaysDialog> createState() => _HolidaysDialogState();
}

class _HolidaysDialogState extends ConsumerState<HolidaysDialog> {
  DateTime? _selectedDay;
  final _nameCtrl = TextEditingController();

  @override
  void dispose() {
    _nameCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final state = ref.watch(attendanceControllerProvider);
    final holidays = state.holidays
        .where((h) => h.day.year == widget.year)
        .toList()
      ..sort((a, b) => a.day.compareTo(b.day));

    return DsFormDialog(
      title: l.text('publicHolidays'),
      width: 400,
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('${widget.year}',
              style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 12),
          if (holidays.isEmpty)
            Text(l.text('noHolidaysYet'))
          else
            ConstrainedBox(
              constraints: const BoxConstraints(maxHeight: 220),
              child: ListView.separated(
                shrinkWrap: true,
                itemCount: holidays.length,
                separatorBuilder: (_, _) => const Divider(height: 1),
                itemBuilder: (context, i) =>
                    _HolidayTile(holiday: holidays[i]),
              ),
            ),
          const Divider(height: 24),
          Text(l.text('addHoliday'),
              style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  icon: const Icon(Icons.calendar_today, size: 16),
                  label: Text(
                    _selectedDay == null
                        ? l.text('pickDate')
                        : '${_selectedDay!.year}-'
                            '${_selectedDay!.month.toString().padLeft(2, '0')}-'
                            '${_selectedDay!.day.toString().padLeft(2, '0')}',
                  ),
                  onPressed: () => _pickDate(context),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _nameCtrl,
            decoration: InputDecoration(
              labelText: l.text('holidayName'),
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
          label: l.text('addHoliday'),
          loading: state.isMutating,
          onPressed: state.isMutating ||
                  _selectedDay == null ||
                  _nameCtrl.text.trim().isEmpty
              ? null
              : () => _add(context, l),
        ),
      ],
    );
  }

  Future<void> _pickDate(BuildContext context) async {
    final picked = await showDatePicker(
      context: context,
      initialDate: DateTime(widget.year, 1, 1),
      firstDate: DateTime(widget.year, 1, 1),
      lastDate: DateTime(widget.year, 12, 31),
    );
    if (picked != null) setState(() => _selectedDay = picked);
  }

  Future<void> _add(BuildContext context, AppLocalizations l) async {
    final ok = await ref
        .read(attendanceControllerProvider.notifier)
        .upsertHoliday(day: _selectedDay!, name: _nameCtrl.text.trim());
    if (context.mounted) {
      if (ok) {
        setState(() {
          _selectedDay = null;
          _nameCtrl.clear();
        });
        DsFeedback.show(context, l.text('holidayAdded'), tone: DsTone.success);
      } else {
        final err = ref.read(attendanceControllerProvider).error ?? 'error';
        DsFeedback.show(context, err, tone: DsTone.danger);
      }
    }
  }
}

class _HolidayTile extends ConsumerWidget {
  const _HolidayTile({required this.holiday});

  final Holiday holiday;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final isMutating =
        ref.watch(attendanceControllerProvider).isMutating;

    return ListTile(
      dense: true,
      leading: const Icon(Icons.event_outlined, size: 18),
      title: Text(holiday.name),
      subtitle: Text(
        '${holiday.day.year}-'
        '${holiday.day.month.toString().padLeft(2, '0')}-'
        '${holiday.day.day.toString().padLeft(2, '0')}',
      ),
      trailing: IconButton(
        icon: const Icon(Icons.delete_outline, size: 18, color: DsColors.danger),
        tooltip: l.text('delete'),
        onPressed: isMutating
            ? null
            : () => _delete(context, ref, l),
      ),
    );
  }

  Future<void> _delete(
      BuildContext context, WidgetRef ref, AppLocalizations l) async {
    final ok = await ref
        .read(attendanceControllerProvider.notifier)
        .deleteHoliday(holiday.id);
    if (context.mounted && !ok) {
      final err = ref.read(attendanceControllerProvider).error ?? 'error';
      DsFeedback.show(context, err, tone: DsTone.danger);
    }
  }
}
