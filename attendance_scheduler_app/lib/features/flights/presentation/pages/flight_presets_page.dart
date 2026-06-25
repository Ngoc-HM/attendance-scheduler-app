import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/api_exception.dart';
import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../data/models/flight_preset_model.dart';
import '../providers/flights_provider.dart';
import '../widgets/preset_form_dialog.dart';

/// Admin-only screen for managing reusable flight presets.
///
/// Reached via Navigator.push from [FlightsPage] — no new shell tab needed.
/// Lists all presets (label, route, FLT arr/dep, STA, STD, active status)
/// and supports add / edit / delete.
class FlightPresetsPage extends ConsumerWidget {
  const FlightPresetsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final presetsAsync = ref.watch(flightPresetsControllerProvider);
    final ctrl = ref.read(flightPresetsControllerProvider.notifier);

    return Scaffold(
      appBar: AppBar(
        title: Text(l.text('flightPresets')),
        actions: [
          IconButton(
            tooltip: l.text('addPreset'),
            icon: const Icon(Icons.add),
            onPressed: () => _showPresetDialog(context, ref, l, null),
          ),
        ],
      ),
      body: presetsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                err is ApiException
                    ? err.message
                    : l.text('flightsLoadFailed'),
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
        data: (presets) => presets.isEmpty
            ? DsEmptyState(
                icon: Icons.flight_outlined,
                title: l.text('noPresetsYet'),
                message: l.text('noPresetsMessage'),
                actionLabel: l.text('addPreset'),
                onAction: () => _showPresetDialog(context, ref, l, null),
              )
            : _PresetsTable(
                presets: presets,
                onEdit: (p) => _showPresetDialog(context, ref, l, p),
                onDelete: (p) => _confirmDelete(context, ref, l, p),
              ),
      ),
    );
  }

  Future<void> _showPresetDialog(
    BuildContext context,
    WidgetRef ref,
    AppLocalizations l,
    FlightPresetModel? initial,
  ) async {
    await showDialog<void>(
      context: context,
      builder: (_) => PresetFormDialog(
        initial: initial,
        onSave: (preset) => _save(context, ref, l, initial, preset),
      ),
    );
  }

  Future<void> _save(
    BuildContext context,
    WidgetRef ref,
    AppLocalizations l,
    FlightPresetModel? existing,
    FlightPresetModel preset,
  ) async {
    final ctrl = ref.read(flightPresetsControllerProvider.notifier);
    try {
      if (existing != null) {
        await ctrl.update(existing.id, preset);
      } else {
        await ctrl.create(preset);
      }
      if (context.mounted) {
        DsFeedback.show(
          context,
          l.text('presetSaved'),
          tone: DsTone.success,
        );
      }
    } on ApiException catch (e) {
      if (context.mounted) {
        DsFeedback.show(context, e.message, tone: DsTone.danger);
      }
    }
  }

  Future<void> _confirmDelete(
    BuildContext context,
    WidgetRef ref,
    AppLocalizations l,
    FlightPresetModel preset,
  ) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(l.text('delete')),
        content: Text(
          '${l.text('deletePresetConfirm')} "${preset.label}"?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: Text(l.cancel),
          ),
          FilledButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: Text(l.text('delete')),
          ),
        ],
      ),
    );
    if (ok != true) return;
    final ctrl = ref.read(flightPresetsControllerProvider.notifier);
    try {
      await ctrl.delete(preset.id);
      if (context.mounted) {
        DsFeedback.show(
          context,
          l.text('presetDeleted'),
          tone: DsTone.success,
        );
      }
    } on ApiException catch (e) {
      if (context.mounted) {
        DsFeedback.show(context, e.message, tone: DsTone.danger);
      }
    }
  }
}

// ---------------------------------------------------------------------------
// Table
// ---------------------------------------------------------------------------

class _PresetsTable extends StatelessWidget {
  const _PresetsTable({
    required this.presets,
    required this.onEdit,
    required this.onDelete,
  });

  final List<FlightPresetModel> presets;
  final ValueChanged<FlightPresetModel> onEdit;
  final ValueChanged<FlightPresetModel> onDelete;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    // label | route | flt arr | flt dep | STA | STD | active | actions
    final columns = [
      DsTableColumn(header: l.text('presetLabel'), flex: 3),
      DsTableColumn(header: l.text('presetRoute'), flex: 2),
      DsTableColumn(header: l.text('fltArr'), flex: 1),
      DsTableColumn(header: l.text('fltDep'), flex: 1),
      DsTableColumn(header: l.text('sta'), flex: 2),
      DsTableColumn(header: l.text('std'), flex: 2),
      DsTableColumn(header: l.text('isActive'), flex: 2),
      DsTableColumn(header: l.actions, flex: 3),
    ];

    return DsSurface(
      padding: EdgeInsets.zero,
      child: DsDataTable(
        columns: columns,
        rows: [
          for (final p in presets)
            [
              Text(p.label, style: DsType.tableCell, overflow: TextOverflow.ellipsis),
              Text(p.route ?? '—', style: DsType.tableCell, overflow: TextOverflow.ellipsis),
              Text('${p.fltArr}', style: DsType.tableCell),
              Text('${p.fltDep}', style: DsType.tableCell),
              Text(p.sta, style: DsType.tableCell),
              Text(p.std, style: DsType.tableCell),
              DsBadge(
                label: p.isActive ? l.text('active') : l.text('disabled'),
                tone: p.isActive ? DsTone.success : DsTone.neutral,
              ),
              // FittedBox guards against horizontal overflow: when the column
              // is too narrow for both actions it scales down instead of
              // throwing a RenderFlex "RIGHT OVERFLOWED" error.
              FittedBox(
                fit: BoxFit.scaleDown,
                alignment: Alignment.centerLeft,
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    DsTextAction(
                      label: l.text('edit'),
                      icon: Icons.edit_outlined,
                      onPressed: () => onEdit(p),
                    ),
                    const SizedBox(width: DsSpacing.x2),
                    DsTextAction(
                      label: l.text('delete'),
                      icon: Icons.delete_outline,
                      tone: DsTone.danger,
                      onPressed: () => onDelete(p),
                    ),
                  ],
                ),
              ),
            ],
        ],
      ),
    );
  }
}
