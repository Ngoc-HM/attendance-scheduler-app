import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/api_exception.dart';
import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../providers/flights_provider.dart';

/// Flights page (F-04) — live data from GET /flights/days.
///
/// Admin actions: manual add/upsert, Excel import.
/// All users: month navigation + table view.
class FlightsPage extends ConsumerWidget {
  const FlightsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(flightsControllerProvider);
    final ctrl = ref.read(flightsControllerProvider.notifier);
    final isAdmin =
        ref.watch(authControllerProvider).user?.isAdmin ?? false;
    final l = AppLocalizations.of(context);

    return state.rows.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (err, _) => Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              err is ApiException ? err.message : l.text('flightsLoadFailed'),
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 12),
            DsPrimaryButton(
              label: l.text('retry'),
              onPressed: ctrl.load,
            ),
          ],
        ),
      ),
      data: (rows) => DsFlightsView(
        month: state.month,
        rows: rows,
        onPreviousMonth: ctrl.previousMonth,
        onNextMonth: ctrl.nextMonth,
        onImport: isAdmin ? () => _pickAndImport(context, ref, l) : () {},
        onAdd: isAdmin
            ? () => _showAddDialog(context, ref, state.month, l)
            : () {},
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Excel import
  // ---------------------------------------------------------------------------

  Future<void> _pickAndImport(
    BuildContext context,
    WidgetRef ref,
    AppLocalizations l,
  ) async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['xlsx'],
      withData: true,
    );
    if (result == null || result.files.isEmpty) return;

    final ctrl = ref.read(flightsControllerProvider.notifier);
    try {
      await ctrl.importExcel(result.files.first);
      if (context.mounted) {
        DsFeedback.show(
          context,
          l.text('flightsImportSuccess'),
          tone: DsTone.success,
        );
      }
    } on ApiException catch (e) {
      if (context.mounted) {
        DsFeedback.show(
          context,
          e.message,
          tone: DsTone.danger,
        );
      }
    }
  }

  // ---------------------------------------------------------------------------
  // Manual add/upsert dialog
  // ---------------------------------------------------------------------------

  Future<void> _showAddDialog(
    BuildContext context,
    WidgetRef ref,
    DateTime month,
    AppLocalizations l,
  ) async {
    final dayCtrl = TextEditingController();
    final pairsCtrl = TextEditingController(text: '1');

    await showDialog<void>(
      context: context,
      builder: (ctx) => DsFormDialog(
        title: l.text('addFlightDay'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: dayCtrl,
              decoration: InputDecoration(
                labelText: l.text('dayOfMonth'),
                hintText: '1–31',
              ),
              keyboardType: TextInputType.number,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: pairsCtrl,
              decoration: InputDecoration(
                labelText: l.text('flightPairsCount'),
                hintText: '0 / 1 / 2',
              ),
              keyboardType: TextInputType.number,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: Text(l.cancel),
          ),
          DsPrimaryButton(
            label: l.create,
            onPressed: () async {
              final day = int.tryParse(dayCtrl.text.trim());
              final pairs = int.tryParse(pairsCtrl.text.trim());
              if (day == null || pairs == null || pairs < 0 || pairs > 2) {
                return;
              }
              Navigator.of(ctx).pop();
              final date = DateTime(month.year, month.month, day);
              final ctrl = ref.read(flightsControllerProvider.notifier);
              try {
                await ctrl.upsertDay(date, pairs);
                if (context.mounted) {
                  DsFeedback.show(
                    context,
                    l.text('flightDaySaved'),
                    tone: DsTone.success,
                  );
                }
              } on ApiException catch (e) {
                if (context.mounted) {
                  DsFeedback.show(context, e.message, tone: DsTone.danger);
                }
              }
            },
          ),
        ],
      ),
    );
  }
}
