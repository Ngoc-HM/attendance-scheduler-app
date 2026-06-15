import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../providers/reports_provider.dart';

/// Reports page (F-15) — admin-only export of monthly / yearly attendance.
///
/// Lets the user pick year, month and format (CSV / XLSX), then triggers a
/// download from the backend, saves the file to the system downloads folder,
/// and surfaces the saved path via a [DsFeedback] snackbar.
class ReportsPage extends ConsumerWidget {
  const ReportsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(reportsControllerProvider);
    final ctrl = ref.read(reportsControllerProvider.notifier);
    final l = AppLocalizations.of(context);

    // Build the "recent exports" table rows from the last export result.
    final rows = _buildRows(state, l);

    return DsReportsView(
      rows: rows,
      onExportMonthly: state.isExporting
          ? () {}
          : () => _export(context, ref, ctrl.exportMonthly, l),
      onExportYearly: state.isExporting
          ? () {}
          : () => _export(context, ref, ctrl.exportYearly, l),
      onDownload: (_) => _showPicker(context, ref, ctrl, l),
    );
  }

  // ---------------------------------------------------------------------------
  // Export trigger
  // ---------------------------------------------------------------------------

  Future<void> _export(
    BuildContext context,
    WidgetRef ref,
    Future<ExportResult> Function() action,
    AppLocalizations l,
  ) async {
    final result = await action();
    if (!context.mounted) return;

    switch (result) {
      case ExportSuccess(:final path):
        DsFeedback.show(
          context,
          '${l.text('reportSavedTo')} $path',
          tone: DsTone.success,
        );
      case ExportFailure(:final message):
        DsFeedback.show(context, message, tone: DsTone.danger);
    }
  }

  // ---------------------------------------------------------------------------
  // Picker dialog: year / month / format
  // ---------------------------------------------------------------------------

  void _showPicker(
    BuildContext context,
    WidgetRef ref,
    ReportsController ctrl,
    AppLocalizations l,
  ) {
    final state = ref.read(reportsControllerProvider);
    int year = state.selectedYear ?? DateTime.now().year;
    int month = state.selectedMonth ?? DateTime.now().month;
    String format = state.selectedFormat;

    showDialog<void>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setS) => DsFormDialog(
          title: l.text('exportOptions'),
          width: 300,
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Year
              Row(
                children: [
                  Text('${l.text("year")}:  '),
                  DropdownButton<int>(
                    value: year,
                    items: List.generate(5, (i) => DateTime.now().year - i)
                        .map((y) => DropdownMenuItem(
                              value: y,
                              child: Text('$y'),
                            ))
                        .toList(),
                    onChanged: (v) => setS(() => year = v!),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              // Month (optional — blank = yearly export)
              Row(
                children: [
                  Text('${l.text("month")}:  '),
                  DropdownButton<int?>(
                    value: month,
                    items: [
                      DropdownMenuItem<int?>(
                        value: null,
                        child: Text(l.text('allYear')),
                      ),
                      ...List.generate(
                        12,
                        (i) => DropdownMenuItem<int?>(
                          value: i + 1,
                          child: Text('${i + 1}'),
                        ),
                      ),
                    ],
                    onChanged: (v) => setS(() => month = v ?? 0),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              // Format
              Row(
                children: [
                  Text('${l.text("format")}:  '),
                  DropdownButton<String>(
                    value: format,
                    items: const [
                      DropdownMenuItem(value: 'csv', child: Text('CSV')),
                      DropdownMenuItem(value: 'xlsx', child: Text('XLSX')),
                    ],
                    onChanged: (v) => setS(() => format = v!),
                  ),
                ],
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(),
              child: Text(l.cancel),
            ),
            DsPrimaryButton(
              label: l.text('download'),
              onPressed: () {
                Navigator.of(ctx).pop();
                ctrl.selectYear(year);
                ctrl.selectMonth(month);
                ctrl.selectFormat(format);
                if (month > 0) {
                  _export(context, ref, ctrl.exportMonthly, l);
                } else {
                  _export(context, ref, ctrl.exportYearly, l);
                }
              },
            ),
          ],
        ),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Build display rows from last export result
  // ---------------------------------------------------------------------------

  List<DsReportRowData> _buildRows(ReportsState state, AppLocalizations l) {
    final last = state.lastResult;
    if (last is ExportSuccess) {
      final now = DateTime.now();
      return [
        DsReportRowData(
          name: l.text('latestExport'),
          period: state.selectedMonth != null && (state.selectedMonth ?? 0) > 0
              ? l.monthYear(
                  DateTime(state.selectedYear ?? now.year,
                      state.selectedMonth ?? now.month),
                )
              : '${state.selectedYear ?? now.year}',
          updated: l.dateTime(now),
          status: 'Ready',
        ),
      ];
    }
    return [];
  }
}
