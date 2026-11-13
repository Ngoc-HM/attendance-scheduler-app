import 'package:flutter/material.dart';

import '../i18n/app_localizations.dart';
import 'components.dart';
import 'tokens.dart';

/// "HH:MM" to minutes; null stays null.
int? _minutes(String? hm) {
  if (hm == null) return null;
  final p = hm.split(':');
  return int.parse(p[0]) * 60 + int.parse(p[1]);
}

/// Worked time "H:MM" between two "HH:MM" punches, or null.
String? workedTime(String? checkIn, String? checkOut) {
  final a = _minutes(checkIn), b = _minutes(checkOut);
  if (a == null || b == null || b <= a) return null;
  final d = b - a;
  return '${d ~/ 60}:${(d % 60).toString().padLeft(2, '0')}';
}

/// One line of a check-in/out table: day · person · in · out · worked ·
/// note · action. Shared by the admin list and the employee's own month;
/// [DsClockTableRow.header] gives the column titles.
class DsClockTableRow extends StatelessWidget {
  const DsClockTableRow({
    super.key,
    this.day,
    this.person,
    this.checkIn,
    this.checkOut,
    this.note,
    this.noteIsAlert = false,
    this.dayStart = false,
    this.action,
  }) : _header = null;

  DsClockTableRow.header(
    AppLocalizations l, {
    super.key,
    bool withPerson = true,
  }) : day = l.text('clockDay'),
       person = withPerson ? l.text('clockPerson') : null,
       checkIn = l.text('clockIn'),
       checkOut = l.text('clockOut'),
       note = null,
       noteIsAlert = false,
       dayStart = false,
       action = null,
       _header = l.text('clockWorked');

  final String? day;
  final String? person;
  final String? checkIn;
  final String? checkOut;
  final String? note;
  final bool noteIsAlert;
  final bool dayStart;
  final Widget? action;

  /// Set only on the header row: the "worked" column title.
  final String? _header;

  @override
  Widget build(BuildContext context) {
    final isHeader = _header != null;
    final base = Theme.of(context).textTheme.bodyMedium!.copyWith(
      fontFeatures: const [FontFeature.tabularFigures()],
    );
    final head = base.copyWith(
      color: DsColors.textMuted,
      fontSize: DsFontSize.caption,
      fontWeight: FontWeight.w600,
    );
    Text cell(String? text, {TextStyle? style}) => Text(
      text ?? '—',
      overflow: TextOverflow.ellipsis,
      style: isHeader ? head : (style ?? base),
    );
    return DecoratedBox(
      decoration: BoxDecoration(
        color: isHeader ? DsColors.surfaceSubtle : null,
        border: Border(
          top: BorderSide(
            color: dayStart ? DsColors.borderStrong : DsColors.border,
            width: isHeader ? 0 : 1,
          ),
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: DsSpacing.x4),
        child: SizedBox(
          height: isHeader ? 36 : 44,
          child: Row(
            children: [
              SizedBox(
                width: 96,
                child: day == null
                    ? null
                    : cell(
                        day,
                        style: base.copyWith(fontWeight: FontWeight.w600),
                      ),
              ),
              if (person != null) Expanded(child: cell(person)),
              SizedBox(width: 72, child: cell(checkIn)),
              SizedBox(width: 72, child: cell(checkOut)),
              SizedBox(
                width: 72,
                child: cell(
                  isHeader ? _header : workedTime(checkIn, checkOut),
                  style: base.copyWith(color: DsColors.textSecondary),
                ),
              ),
              SizedBox(
                width: 132,
                child: note == null
                    ? null
                    : cell(
                        note,
                        style: base.copyWith(
                          color: noteIsAlert
                              ? DsColors.danger
                              : DsColors.textMuted,
                        ),
                      ),
              ),
              SizedBox(width: 40, child: action),
              if (person == null) const Spacer(),
            ],
          ),
        ),
      ),
    );
  }
}

/// The employee's month of punches: a titled surface like the attendance
/// board ("Bảng chấm công"), with the table or an empty line inside.
class DsOwnClockTable extends StatelessWidget {
  const DsOwnClockTable({
    super.key,
    required this.title,
    required this.emptyText,
    required this.rows,
  });

  final String title;
  final String emptyText;

  /// (day, check-in "HH:MM", check-out "HH:MM"), newest first.
  final List<(DateTime, String?, String?)> rows;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return DsSurface(
      padding: EdgeInsets.zero,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.all(DsSpacing.x4),
            child: DsSectionHeader(title),
          ),
          const Divider(height: 1),
          if (rows.isEmpty)
            Padding(
              padding: const EdgeInsets.all(DsSpacing.x4),
              child: Text(
                emptyText,
                style: const TextStyle(color: DsColors.textMuted),
              ),
            )
          else ...[
            DsClockTableRow.header(l, withPerson: false),
            for (final (day, cin, cout) in rows)
              DsClockTableRow(
                day:
                    '${day.day.toString().padLeft(2, '0')}/'
                    '${day.month.toString().padLeft(2, '0')} '
                    '${l.shortWeekday(day)}',
                checkIn: cin,
                checkOut: cout,
              ),
          ],
        ],
      ),
    );
  }
}
