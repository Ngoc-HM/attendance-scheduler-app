import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/api_exception.dart';
import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../data/datasources/flights_remote_datasource.dart';
import '../providers/flights_provider.dart';
import '../widgets/month_batch_dialog.dart';
import 'flight_presets_page.dart';

/// Flights page (F-04) — live data from GET /flights/days.
///
/// Admin primary action: "Add flight" opens the month-batch preset grid.
/// Admin secondary actions: Excel import, manage presets.
/// All users: month navigation + table view.
class FlightsPage extends ConsumerWidget {
  const FlightsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(flightsControllerProvider);
    final ctrl = ref.read(flightsControllerProvider.notifier);
    final isAdmin =
        ref.watch(authControllerProvider).user?.isAdmin ?? false;
    // Keep the autoDispose presets provider alive and preload it so the
    // month-batch dialog has presets ready by the time "Add flight" is tapped.
    // Without this watch the provider was only `ref.read` inside the dialog
    // handler → it returned a transient `loading` state and the dialog bailed.
    ref.watch(flightPresetsControllerProvider);
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
            const SizedBox(height: DsSpacing.x3),
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
            ? () => _showMonthBatchDialog(context, ref, state.month, l)
            : () {},
        onManagePresets: isAdmin
            ? () => Navigator.of(context).push(
                  MaterialPageRoute<void>(
                    builder: (_) => const FlightPresetsPage(),
                  ),
                )
            : null,
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
        DsFeedback.show(context, e.message, tone: DsTone.danger);
      }
    }
  }

  // ---------------------------------------------------------------------------
  // Month-batch preset dialog
  // ---------------------------------------------------------------------------

  Future<void> _showMonthBatchDialog(
    BuildContext context,
    WidgetRef ref,
    DateTime month,
    AppLocalizations l,
  ) async {
    // Presets come from the autoDispose provider — ensure it is alive while we
    // build the dialog by reading it here (watch keeps it alive in the widget).
    final presetsAsync = ref.read(flightPresetsControllerProvider);
    final activePresets = presetsAsync.asData?.value
            .where((p) => p.isActive)
            .toList() ??
        [];

    // If presets haven't loaded yet (very early tap before preload finishes),
    // bail with a hint — the build() watch means a retry will succeed.
    if (presetsAsync.isLoading) {
      DsFeedback.show(
        context,
        l.text('monthFlightsLoading'),
        tone: DsTone.primary,
      );
      return;
    }

    // No presets configured → guide the admin to create one first.
    if (activePresets.isEmpty) {
      DsFeedback.show(
        context,
        l.text('noPresetsMessage'),
        tone: DsTone.primary,
      );
      return;
    }

    final existingDays = ref.read(flightsControllerProvider).dayModels;

    if (!context.mounted) return;

    await showDialog<void>(
      context: context,
      builder: (_) => MonthBatchDialog(
        month: month,
        presets: activePresets,
        existingDays: existingDays,
        loadMonth: (m) =>
            ref.read(flightsDataSourceProvider).listDays(m.year, m.month),
        onApply: (appliedMonth, items) async {
          final ctrl = ref.read(flightsControllerProvider.notifier);
          try {
            await ctrl.applyMonth(appliedMonth, items);
            if (context.mounted) {
              DsFeedback.show(
                context,
                l.text('monthFlightsSaved'),
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
    );
  }
}
