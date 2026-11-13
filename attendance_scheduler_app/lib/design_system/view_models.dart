import '../core/constants/shift_codes.dart';

class DsRosterRowData {
  const DsRosterRowData({
    required this.name,
    required this.role,
    required this.shifts,
    required this.arrivals,
    required this.departures,
    required this.offDays,
    this.id,
  });

  /// Backing user id — needed by cell-edit callbacks (admin F-09); null for
  /// read-only rosters that never edit cells.
  final int? id;

  final String name;
  final String role;
  final List<ShiftCode> shifts;
  final int arrivals;
  final int departures;
  final int offDays;
}

class DsFlightRowData {
  const DsFlightRowData({
    required this.date,
    required this.flightPairs,
    required this.flights,
    required this.arrival,
    required this.departure,
    required this.status,
  });

  /// [status] code of a fully planned day; shown via `statusLabel`
  /// (i18n key `statusComplete`).
  static const String statusComplete = 'complete';

  final DateTime date;
  final int flightPairs;
  final String flights;
  final String arrival;
  final String departure;
  final String status;
}

class DsLeaveRowData {
  const DsLeaveRowData({
    required this.employee,
    required this.role,
    required this.type,
    required this.range,
    required this.days,
    required this.status,
    required this.carryComp,
    this.staffingWarnings = const [],
  });

  final String employee;
  final String role;
  final String type;
  final String range;
  final int days;
  final String status;
  final int carryComp;

  /// Flight-staffing risk lines shown on the row (one per day or shift);
  /// empty → the row looks like any other.
  final List<String> staffingWarnings;

  DsLeaveRowData copyWith({String? status}) {
    return DsLeaveRowData(
      employee: employee,
      role: role,
      type: type,
      range: range,
      days: days,
      status: status ?? this.status,
      carryComp: carryComp,
      staffingWarnings: staffingWarnings,
    );
  }
}

/// The background of a day cell in the admin's grids (owner 2026-11-13):
/// [missing] light red — due at work by the published roster, no check-in
/// or no check-out; [adjusted] light yellow — the admin changed the day
/// after hearing from the person.
enum DsDayMark { missing, adjusted }

class DsAttendanceRowData {
  const DsAttendanceRowData({
    this.id,
    required this.name,
    required this.role,
    required this.shifts,
    required this.workdays,
    required this.absences,
    this.dayNotes = const [],
    this.dayMarks = const [],
  });

  /// Backing user id (admin cell edits); null for read-only rows.
  final int? id;

  final String name;
  final String role;
  final List<ShiftCode> shifts;
  final int workdays;
  final int absences;

  /// Per day (index 0 = the 1st): the tooltip of the cell, e.g. the
  /// check-in/out times; null or a short list = no tooltip.
  final List<String?> dayNotes;

  /// Per day: the cell's background tint; null = none.
  final List<DsDayMark?> dayMarks;
}

class DsReportRowData {
  const DsReportRowData({
    required this.name,
    required this.period,
    required this.updated,
    required this.status,
  });

  /// [status] code of a saved export; shown via `statusLabel` (i18n key
  /// `statusReady`).
  static const String statusReady = 'ready';

  final String name;
  final String period;
  final String updated;
  final String status;
}

class DsUserRowData {
  const DsUserRowData({
    required this.id,
    required this.username,
    required this.fullName,
    required this.role,
    required this.status,
    required this.code,
  });

  final int id;
  final String username;
  final String fullName;
  final String role;
  final String status;

  /// Confidential per-person identifier auto-assigned by the server (e.g. "A3").
  final String code;
}
