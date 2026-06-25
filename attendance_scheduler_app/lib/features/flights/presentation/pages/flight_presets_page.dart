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
              const SizedBox(height: 12),
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

  // label | route | flt arr | flt dep | STA | STD | active | actions
  static const _flex = [3, 2, 1, 1, 2, 2, 2, 3];

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return DsSurface(
      padding: EdgeInsets.zero,
      child: Column(
        children: [
          _row(
            [
              _header(l.text('presetLabel')),
              _header(l.text('presetRoute')),
              _header(l.text('fltArr')),
              _header(l.text('fltDep')),
              _header(l.text('sta')),
              _header(l.text('std')),
              _header(l.text('isActive')),
              _header(l.actions),
            ],
            background: DsColors.surfaceSubtle,
          ),
          for (final p in presets) ...[
            const Divider(height: 1, color: DsColors.border),
            _row([
              _text(p.label),
              _text(p.route ?? '—'),
              _text('${p.fltArr}'),
              _text('${p.fltDep}'),
              _text(p.sta),
              _text(p.std),
              _leading(
                DsBadge(
                  label: p.isActive
                      ? l.text('active')
                      : l.text('disabled'),
                  tone: p.isActive ? DsTone.success : DsTone.neutral,
                ),
              ),
              // FittedBox guards against horizontal overflow: when the column
              // is too narrow for both actions it scales down instead of
              // throwing a RenderFlex "RIGHT OVERFLOWED" error.
              Align(
                alignment: Alignment.centerLeft,
                child: FittedBox(
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
              ),
            ]),
          ],
        ],
      ),
    );
  }

  Widget _row(List<Widget> cells, {Color? background}) => Container(
        color: background,
        padding: const EdgeInsets.symmetric(
          horizontal: DsSpacing.x5,
          vertical: DsSpacing.x4,
        ),
        child: Row(
          children: [
            for (var i = 0; i < cells.length; i++)
              Expanded(flex: _flex[i], child: cells[i]),
          ],
        ),
      );

  Widget _header(String label) => Text(
        label,
        style: const TextStyle(
          fontSize: 13,
          fontWeight: FontWeight.w600,
          color: DsColors.textMuted,
        ),
      );

  Widget _text(String value) => Text(
        value,
        style: const TextStyle(fontSize: 14, color: DsColors.textPrimary),
        overflow: TextOverflow.ellipsis,
      );

  Widget _leading(Widget child) =>
      Align(alignment: Alignment.centerLeft, child: child);
}
