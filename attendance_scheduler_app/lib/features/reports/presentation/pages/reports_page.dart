import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/api_error_message.dart';
import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../providers/reports_provider.dart';

/// Reports page (F-15) — admin-only export of monthly / yearly attendance.
///
/// The year, month (or "Full year") and format selectors sit on the page
/// (D5); Export downloads the chosen period from the backend, saves the file
/// to the system downloads folder and surfaces the saved path via a
/// [DsFeedback] snackbar. "Full year" keeps the month null and uses the
/// yearly endpoint.
class ReportsPage extends ConsumerWidget {
  const ReportsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(reportsControllerProvider);
    final ctrl = ref.read(reportsControllerProvider.notifier);
    final l = AppLocalizations.of(context);
    final thisYear = DateTime.now().year;
    final year = state.selectedYear ?? thisYear;
    final years = {
      for (var i = 0; i < 5; i++) thisYear - i,
      year,
    }.toList()..sort((a, b) => b.compareTo(a));

    return DsReportsView(
      rows: _buildRows(state, l),
      exporting: state.isExporting,
      onExport: () => _export(context, ctrl, l),
      // Re-download the latest export with the current selection.
      onDownload: (_) => _export(context, ctrl, l),
      filters: [
        DsSelectField<int>(
          label: l.text('year'),
          value: year,
          items: [
            for (final y in years)
              DropdownMenuItem(value: y, child: Text('$y')),
          ],
          onChanged: (v) {
            if (v != null) ctrl.selectYear(v);
          },
        ),
        DsSelectField<int?>(
          label: l.text('month'),
          value: state.selectedMonth,
          items: [
            DropdownMenuItem<int?>(value: null, child: Text(l.text('allYear'))),
            for (var m = 1; m <= 12; m++)
              DropdownMenuItem<int?>(
                value: m,
                child: Text(l.monthYear(DateTime(year, m))),
              ),
          ],
          onChanged: ctrl.selectMonth,
        ),
        DsSelectField<String>(
          label: l.text('format'),
          value: state.selectedFormat,
          items: const [
            DropdownMenuItem(value: 'csv', child: Text('CSV')),
            DropdownMenuItem(value: 'xlsx', child: Text('XLSX')),
          ],
          onChanged: (v) {
            if (v != null) ctrl.selectFormat(v);
          },
        ),
      ],
    );
  }

  Future<void> _export(
    BuildContext context,
    ReportsController ctrl,
    AppLocalizations l,
  ) async {
    final result = await ctrl.export();
    // Null: an export was already running and this click was ignored.
    if (result == null || !context.mounted) return;

    switch (result) {
      case ExportSuccess(:final path):
        DsFeedback.show(
          context,
          '${l.text('reportSavedTo')} $path',
          tone: DsTone.success,
        );
      case ExportFailure(:final error, :final messageKey):
        DsFeedback.show(
          context,
          messageKey != null ? l.text(messageKey) : apiErrorMessage(l, error),
          tone: DsTone.danger,
        );
    }
  }

  /// The "recent exports" table: the last successful export, if any.
  List<DsReportRowData> _buildRows(ReportsState state, AppLocalizations l) {
    if (state.lastResult is! ExportSuccess) return [];
    final now = DateTime.now();
    final year = state.selectedYear ?? now.year;
    final month = state.selectedMonth;
    return [
      DsReportRowData(
        name: l.text('latestExport'),
        period: month == null ? '$year' : l.monthYear(DateTime(year, month)),
        updated: l.dateTime(now),
        status: DsReportRowData.statusReady,
      ),
    ];
  }
}
