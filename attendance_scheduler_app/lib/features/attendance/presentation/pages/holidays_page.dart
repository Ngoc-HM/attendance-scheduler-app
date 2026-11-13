import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/api_error_message.dart';
import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../data/datasources/attendance_remote_datasource.dart';
import '../../domain/entities/attendance_entities.dart';

/// The public holidays of a year (F-13), on their own screen (owner
/// 2026-11-13): add a day with its name, see the year's list, delete one.
final holidaysProvider = FutureProvider.autoDispose.family<List<Holiday>, int>((
  ref,
  year,
) async {
  final days = await ref
      .watch(attendanceRemoteDataSourceProvider)
      .fetchHolidays(year);
  return [...days]..sort((a, b) => a.day.compareTo(b.day));
});

class HolidaysPage extends ConsumerStatefulWidget {
  const HolidaysPage({super.key});

  @override
  ConsumerState<HolidaysPage> createState() => _HolidaysPageState();
}

class _HolidaysPageState extends ConsumerState<HolidaysPage> {
  int _year = DateTime.now().year;
  DateTime? _day;
  final _name = TextEditingController();
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _name.addListener(() => setState(() {}));
  }

  @override
  void dispose() {
    _name.dispose();
    super.dispose();
  }

  static String _date(DateTime d) =>
      '${d.day.toString().padLeft(2, '0')}/${d.month.toString().padLeft(2, '0')}/${d.year}';

  Future<void> _pickDay() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _day ?? DateTime(_year, DateTime.now().month),
      firstDate: DateTime(_year),
      lastDate: DateTime(_year, 12, 31),
    );
    if (picked != null) setState(() => _day = picked);
  }

  Future<void> _run(Future<void> Function() action, String doneKey) async {
    final l = AppLocalizations.of(context);
    setState(() => _busy = true);
    try {
      await action();
      ref.invalidate(holidaysProvider(_year));
      if (mounted) {
        DsFeedback.show(context, l.text(doneKey), tone: DsTone.success);
      }
    } catch (e) {
      if (mounted) {
        DsFeedback.show(context, apiErrorMessage(l, e), tone: DsTone.danger);
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _add() => _run(() async {
    await ref
        .read(attendanceRemoteDataSourceProvider)
        .upsertHoliday(day: _day!, name: _name.text.trim());
    setState(() {
      _day = null;
      _name.clear();
    });
  }, 'holidayAdded');

  Future<void> _delete(Holiday h) => _run(
    () => ref.read(attendanceRemoteDataSourceProvider).deleteHoliday(h.id),
    'holidayDeleted',
  );

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final holidays = ref.watch(holidaysProvider(_year));
    final canAdd = !_busy && _day != null && _name.text.trim().isNotEmpty;

    return DsPage(
      title: l.text('publicHolidays'),
      actions: [
        DsYearSwitcher(
          year: _year,
          onPrevious: () => setState(() => (_year--, _day = null)),
          onNext: () => setState(() => (_year++, _day = null)),
        ),
      ],
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          DsSurface(
            // One line, every control the field's height: the buttons stretch
            // to it so the three edges line up.
            child: IntrinsicHeight(
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // A fixed minimum width: picking a date must not shift the
                  // name field sideways.
                  ConstrainedBox(
                    constraints: const BoxConstraints(minWidth: 168),
                    child: DsSecondaryButton(
                      icon: Icons.calendar_today,
                      label: _day == null ? l.text('pickDate') : _date(_day!),
                      onPressed: _pickDay,
                    ),
                  ),
                  const SizedBox(width: DsSpacing.x3),
                  Expanded(
                    child: DsTextField(
                      controller: _name,
                      label: l.text('holidayName'),
                      onSubmitted: (_) => canAdd ? _add() : null,
                    ),
                  ),
                  const SizedBox(width: DsSpacing.x3),
                  DsPrimaryButton(
                    label: l.text('addHoliday'),
                    icon: Icons.add,
                    loading: _busy,
                    onPressed: canAdd ? _add : null,
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: DsSpacing.x4),
          holidays.when(
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (e, _) => Text(
              apiErrorMessage(l, e),
              style: const TextStyle(color: DsColors.danger),
            ),
            data: (days) => days.isEmpty
                ? Text(
                    l.text('noHolidaysYet'),
                    style: const TextStyle(color: DsColors.textMuted),
                  )
                : DsSurface(
                    padding: EdgeInsets.zero,
                    child: Column(
                      children: [
                        for (var i = 0; i < days.length; i++) ...[
                          if (i > 0) const Divider(height: 1),
                          // Same inset and type size as the form above: the
                          // date column lines up with the date button.
                          Padding(
                            padding: const EdgeInsets.symmetric(
                              horizontal: DsSpacing.x5,
                              vertical: DsSpacing.x2,
                            ),
                            child: Row(
                              children: [
                                SizedBox(
                                  // date button + gap + the field's text inset (14):
                                  // the name starts where the typed name does.
                                  width: 168 + DsSpacing.x3 + 14,
                                  child: Text(
                                    '${_date(days[i].day)} · '
                                    '${l.shortWeekday(days[i].day)}',
                                    style: Theme.of(context)
                                        .textTheme
                                        .bodyMedium
                                        ?.copyWith(fontWeight: FontWeight.w600),
                                  ),
                                ),
                                Expanded(
                                  child: Text(
                                    days[i].name,
                                    style: Theme.of(
                                      context,
                                    ).textTheme.bodyMedium,
                                  ),
                                ),
                                IconButton(
                                  icon: const Icon(
                                    Icons.delete_outline,
                                    size: 18,
                                  ),
                                  color: DsColors.danger,
                                  tooltip: l.text('delete'),
                                  onPressed: _busy
                                      ? null
                                      : () => _delete(days[i]),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
          ),
        ],
      ),
    );
  }
}
