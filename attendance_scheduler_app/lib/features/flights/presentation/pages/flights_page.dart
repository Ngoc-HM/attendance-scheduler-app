import 'package:flutter/material.dart';

import '../../../../design_system/design_system.dart';

class FlightsPage extends StatefulWidget {
  const FlightsPage({super.key});

  @override
  State<FlightsPage> createState() => _FlightsPageState();
}

class _FlightsPageState extends State<FlightsPage> {
  DateTime _month = DateTime(2026, 6);

  static const _rows = [
    DsFlightRowData(
      date: '01 Jun, Mon',
      flightPairs: 2,
      flights: 'VN37 / VN36 · VN31 / VN30',
      arrival: '06:20 · 07:10',
      departure: '13:55 · 14:40',
      status: 'Complete',
    ),
    DsFlightRowData(
      date: '02 Jun, Tue',
      flightPairs: 1,
      flights: 'VN37 / VN36',
      arrival: '06:20',
      departure: '13:55',
      status: 'Complete',
    ),
    DsFlightRowData(
      date: '04 Jun, Thu',
      flightPairs: 2,
      flights: 'VN37 / VN36 · VN31 / VN30',
      arrival: '06:15 · 07:05',
      departure: '13:45 · 14:35',
      status: 'Complete',
    ),
    DsFlightRowData(
      date: '06 Jun, Sat',
      flightPairs: 1,
      flights: 'VN31 / VN30',
      arrival: '07:10',
      departure: '14:40',
      status: 'Review',
    ),
    DsFlightRowData(
      date: '08 Jun, Mon',
      flightPairs: 2,
      flights: 'VN37 / VN36 · VN31 / VN30',
      arrival: '06:20 · 07:10',
      departure: '13:55 · 14:40',
      status: 'Complete',
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return DsFlightsView(
      month: _month,
      rows: _rows,
      onPreviousMonth: () =>
          setState(() => _month = DateTime(_month.year, _month.month - 1)),
      onNextMonth: () =>
          setState(() => _month = DateTime(_month.year, _month.month + 1)),
      onImport: () => DsFeedback.show(
        context,
        'Excel import will be connected to the flight API.',
      ),
      onAdd: () => DsFeedback.show(context, 'Flight entry form opened.'),
    );
  }
}
