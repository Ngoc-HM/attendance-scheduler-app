import '../core/constants/shift_codes.dart';

class DsRosterRowData {
  const DsRosterRowData({
    required this.name,
    required this.role,
    required this.shifts,
    required this.arrivals,
    required this.departures,
    required this.offDays,
  });

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

  final String date;
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
  });

  final String employee;
  final String role;
  final String type;
  final String range;
  final int days;
  final String status;
  final int carryComp;

  DsLeaveRowData copyWith({String? status}) {
    return DsLeaveRowData(
      employee: employee,
      role: role,
      type: type,
      range: range,
      days: days,
      status: status ?? this.status,
      carryComp: carryComp,
    );
  }
}

class DsAttendanceRowData {
  const DsAttendanceRowData({
    required this.name,
    required this.role,
    required this.shifts,
    required this.workdays,
    required this.absences,
  });

  final String name;
  final String role;
  final List<ShiftCode> shifts;
  final int workdays;
  final int absences;
}

class DsReportRowData {
  const DsReportRowData({
    required this.name,
    required this.period,
    required this.updated,
    required this.status,
  });

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
  });

  final int id;
  final String username;
  final String fullName;
  final String role;
  final String status;
}
