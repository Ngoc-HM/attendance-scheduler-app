import '../../../design_system/design_system.dart';
import '../../../i18n/app_localizations.dart';
import '../data/datasources/time_clock_remote_datasource.dart';

/// The tooltip of a day cell in the admin's grids: the punches, and why the
/// day is tinted.
String clockNote(ClockBoardCell c, AppLocalizations l) {
  final times = [
    if (c.checkIn != null) '${l.text('clockIn')} ${c.checkIn}',
    if (c.checkOut != null) '${l.text('clockOut')} ${c.checkOut}',
  ];
  final parts = switch (c.status) {
    'absent' => [l.text('clockAbsent')],
    'missed_out' => [...times, l.text('clockMissingOut')],
    'working' => [...times, l.text('clockWorking')],
    'off_day' => [l.text('clockOffDay'), ...times],
    _ => times,
  };
  return [
    ...parts,
    if (c.tint == 'adjusted') l.text('clockMarkAdjusted'),
    if (c.corrected) l.text('clockCorrected'),
  ].join(' · ');
}

/// The tint of a day cell in the admin's grids (owner 2026-11-13).
DsDayMark? clockMark(ClockBoardCell c) => switch (c.tint) {
      'missing' => DsDayMark.missing,
      'adjusted' => DsDayMark.adjusted,
      _ => null,
    };

/// The board of a month as {(user id, day of month): cell}.
Map<(int, int), ClockBoardCell> clockBoardByDay(
  List<ClockBoardCell> board,
  DateTime month,
) => {
      for (final c in board)
        if (c.workDate.year == month.year && c.workDate.month == month.month)
          (c.userId, c.workDate.day): c,
    };
