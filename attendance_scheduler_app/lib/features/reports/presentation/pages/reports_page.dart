import 'package:flutter/material.dart';

import '../../../../design_system/design_system.dart';

class ReportsPage extends StatelessWidget {
  const ReportsPage({super.key});

  static const _rows = [
    DsReportRowData(
      name: 'Monthly attendance',
      period: 'June 2026',
      updated: '11 Jun 2026, 14:20',
      status: 'Ready',
    ),
    DsReportRowData(
      name: 'Monthly roster',
      period: 'June 2026',
      updated: '10 Jun 2026, 09:15',
      status: 'Ready',
    ),
    DsReportRowData(
      name: 'Annual attendance',
      period: '2025',
      updated: '05 Jan 2026, 11:40',
      status: 'Ready',
    ),
  ];

  @override
  Widget build(BuildContext context) {
    void notice(String message) => DsFeedback.show(context, message);
    return DsReportsView(
      rows: _rows,
      onExportMonthly: () => notice('Monthly export requested.'),
      onExportYearly: () => notice('Annual export requested.'),
      onDownload: (_) => notice('Report download requested.'),
    );
  }
}
