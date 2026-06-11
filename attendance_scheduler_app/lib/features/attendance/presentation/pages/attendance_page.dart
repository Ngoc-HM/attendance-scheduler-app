import 'package:flutter/material.dart';

import '../../../../core/constants/shift_codes.dart';
import '../../../../design_system/design_system.dart';

class AttendancePage extends StatefulWidget {
  const AttendancePage({super.key});

  @override
  State<AttendancePage> createState() => _AttendancePageState();
}

class _AttendancePageState extends State<AttendancePage> {
  DateTime _month = DateTime(2026, 6);

  static const _rows = [
    DsAttendanceRowData(
      name: 'Toan Nguyen',
      role: 'M',
      shifts: [
        ShiftCode.oD,
        ShiftCode.oD,
        ShiftCode.x,
        ShiftCode.x,
        ShiftCode.oD,
        ShiftCode.oD,
        ShiftCode.oD,
        ShiftCode.oD,
        ShiftCode.x,
        ShiftCode.x,
        ShiftCode.oD,
        ShiftCode.oD,
        ShiftCode.oD,
        ShiftCode.oD,
      ],
      workdays: 10,
      absences: 4,
    ),
    DsAttendanceRowData(
      name: 'Agne',
      role: 'A1',
      shifts: [
        ShiftCode.a,
        ShiftCode.d,
        ShiftCode.x,
        ShiftCode.x,
        ShiftCode.d,
        ShiftCode.a,
        ShiftCode.s,
        ShiftCode.a,
        ShiftCode.d,
        ShiftCode.x,
        ShiftCode.x,
        ShiftCode.a,
        ShiftCode.d,
        ShiftCode.a,
      ],
      workdays: 9,
      absences: 5,
    ),
    DsAttendanceRowData(
      name: 'Joachim',
      role: 'A2',
      shifts: [
        ShiftCode.d,
        ShiftCode.a,
        ShiftCode.d,
        ShiftCode.x,
        ShiftCode.x,
        ShiftCode.d,
        ShiftCode.a,
        ShiftCode.d,
        ShiftCode.a,
        ShiftCode.x,
        ShiftCode.x,
        ShiftCode.d,
        ShiftCode.a,
        ShiftCode.d,
      ],
      workdays: 10,
      absences: 4,
    ),
    DsAttendanceRowData(
      name: 'Long',
      role: 'A3',
      shifts: [
        ShiftCode.x,
        ShiftCode.x,
        ShiftCode.a,
        ShiftCode.d,
        ShiftCode.a,
        ShiftCode.d,
        ShiftCode.aD,
        ShiftCode.x,
        ShiftCode.x,
        ShiftCode.d,
        ShiftCode.al,
        ShiftCode.al,
        ShiftCode.a,
        ShiftCode.d,
      ],
      workdays: 9,
      absences: 5,
    ),
    DsAttendanceRowData(
      name: 'Thomas',
      role: 'A4',
      shifts: [
        ShiftCode.d,
        ShiftCode.a,
        ShiftCode.d,
        ShiftCode.a,
        ShiftCode.x,
        ShiftCode.x,
        ShiftCode.d,
        ShiftCode.d,
        ShiftCode.a,
        ShiftCode.d,
        ShiftCode.x,
        ShiftCode.x,
        ShiftCode.d,
        ShiftCode.a,
      ],
      workdays: 10,
      absences: 4,
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return DsAttendanceView(
      month: _month,
      rows: _rows,
      onPreviousMonth: () =>
          setState(() => _month = DateTime(_month.year, _month.month - 1)),
      onNextMonth: () =>
          setState(() => _month = DateTime(_month.year, _month.month + 1)),
      onUpdate: () => DsFeedback.show(
        context,
        'Attendance editing will be connected to the attendance API.',
      ),
      onHolidays: () =>
          DsFeedback.show(context, 'Public holiday management opened.'),
    );
  }
}
