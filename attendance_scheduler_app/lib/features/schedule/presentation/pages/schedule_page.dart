import 'package:flutter/material.dart';

import '../../../../core/constants/shift_codes.dart';
import '../../../../design_system/design_system.dart';

class SchedulePage extends StatefulWidget {
  const SchedulePage({super.key});

  @override
  State<SchedulePage> createState() => _SchedulePageState();
}

class _SchedulePageState extends State<SchedulePage> {
  DateTime _month = DateTime(2026, 6);

  static const _rows = [
    DsRosterRowData(
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
      arrivals: 0,
      departures: 0,
      offDays: 4,
    ),
    DsRosterRowData(
      name: 'Chi Tran',
      role: 'M',
      shifts: [
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
        ShiftCode.oD,
      ],
      arrivals: 0,
      departures: 0,
      offDays: 4,
    ),
    DsRosterRowData(
      name: 'Vu Le',
      role: 'T',
      shifts: [
        ShiftCode.t,
        ShiftCode.t,
        ShiftCode.t,
        ShiftCode.x,
        ShiftCode.x,
        ShiftCode.t,
        ShiftCode.t,
        ShiftCode.t,
        ShiftCode.t,
        ShiftCode.x,
        ShiftCode.x,
        ShiftCode.t,
        ShiftCode.t,
        ShiftCode.t,
      ],
      arrivals: 0,
      departures: 0,
      offDays: 4,
    ),
    DsRosterRowData(
      name: 'Agne',
      role: 'A1',
      shifts: [
        ShiftCode.a,
        ShiftCode.d,
        ShiftCode.x,
        ShiftCode.x,
        ShiftCode.d,
        ShiftCode.a,
        ShiftCode.d,
        ShiftCode.a,
        ShiftCode.d,
        ShiftCode.x,
        ShiftCode.x,
        ShiftCode.a,
        ShiftCode.d,
        ShiftCode.a,
      ],
      arrivals: 5,
      departures: 5,
      offDays: 4,
    ),
    DsRosterRowData(
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
      arrivals: 4,
      departures: 6,
      offDays: 4,
    ),
    DsRosterRowData(
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
        ShiftCode.a,
        ShiftCode.d,
        ShiftCode.a,
        ShiftCode.d,
      ],
      arrivals: 5,
      departures: 6,
      offDays: 4,
    ),
    DsRosterRowData(
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
      arrivals: 4,
      departures: 6,
      offDays: 4,
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return DsScheduleView(
      month: _month,
      rows: _rows,
      onPreviousMonth: () =>
          setState(() => _month = DateTime(_month.year, _month.month - 1)),
      onNextMonth: () =>
          setState(() => _month = DateTime(_month.year, _month.month + 1)),
      onGenerate: () => DsFeedback.show(
        context,
        'Schedule generation will use the solver API.',
      ),
      onPublish: () => DsFeedback.show(
        context,
        'Schedule marked ready to publish.',
        tone: DsTone.success,
      ),
    );
  }
}
