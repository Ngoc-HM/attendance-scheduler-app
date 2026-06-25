import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../data/models/flight_day_model.dart';
import '../../data/models/flight_preset_model.dart';

/// Batch-editor dialog: shows ALL days of [month] as a tick-grid.
///
/// Rows = days (1..N). Columns = one per active preset.
/// Admin ticks cells to assign presets to days, then hits "Apply whole month".
/// Returns ONLY the days whose selection CHANGED from the initial state.
class MonthBatchDialog extends ConsumerStatefulWidget {
  const MonthBatchDialog({
    super.key,
    required this.month,
    required this.presets,
    required this.existingDays,
    required this.onApply,
  });

  /// The month being edited (year + month, day is ignored).
  final DateTime month;

  /// Active presets only — these become the grid columns.
  final List<FlightPresetModel> presets;

  /// Current flight data for the month — used to compute initial selection.
  final List<FlightDayModel> existingDays;

  /// Called with the changed items when the admin taps "Apply".
  final void Function(List<({DateTime day, List<int> presetIds})> items)
      onApply;

  @override
  ConsumerState<MonthBatchDialog> createState() => _MonthBatchDialogState();
}

class _MonthBatchDialogState extends ConsumerState<MonthBatchDialog> {
  /// selection[dayOfMonth] = Set of selected preset ids for that day.
  late final Map<int, Set<int>> _selection;

  /// Initial snapshot — compared on apply to find changed days.
  late final Map<int, Set<int>> _initial;

  late final int _daysInMonth;

  @override
  void initState() {
    super.initState();
    _daysInMonth = DateUtils.getDaysInMonth(
      widget.month.year,
      widget.month.month,
    );
    _selection = _buildInitialSelection();
    // Deep-copy for diff at apply time.
    _initial = {
      for (final e in _selection.entries) e.key: Set<int>.of(e.value),
    };
  }

  /// Derives initial checkbox state from [existingDays].
  ///
  /// A preset is "applied" to a day when BOTH preset.fltArr AND preset.fltDep
  /// appear among that day's flight fltNumber values.
  Map<int, Set<int>> _buildInitialSelection() {
    final result = <int, Set<int>>{
      for (var d = 1; d <= _daysInMonth; d++) d: <int>{},
    };

    for (final dayModel in widget.existingDays) {
      final dom = dayModel.day.day;
      if (dom < 1 || dom > _daysInMonth) continue;
      final fltNumbers = dayModel.flights.map((f) => f.fltNumber).toSet();
      for (final preset in widget.presets) {
        if (fltNumbers.contains(preset.fltArr) &&
            fltNumbers.contains(preset.fltDep)) {
          result[dom]!.add(preset.id);
        }
      }
    }
    return result;
  }

  void _toggle(int day, int presetId) {
    setState(() {
      final daySet = _selection[day]!;
      if (daySet.contains(presetId)) {
        daySet.remove(presetId);
      } else if (daySet.length < 2) {
        daySet.add(presetId);
      }
    });
  }

  /// Toggle all days for a given preset column.
  ///
  /// If ALL days already have this preset ticked → untick all; otherwise → tick
  /// all days that still have room (< 2 selected or already have this preset).
  void _toggleColumn(int presetId) {
    setState(() {
      final allTicked = _selection.values.every((s) => s.contains(presetId));
      if (allTicked) {
        for (final s in _selection.values) {
          s.remove(presetId);
        }
      } else {
        for (final s in _selection.values) {
          if (!s.contains(presetId) && s.length < 2) {
            s.add(presetId);
          }
        }
      }
    });
  }

  /// Returns ONLY days whose selection differs from the initial state.
  List<({DateTime day, List<int> presetIds})> _computeChanges() {
    final changes = <({DateTime day, List<int> presetIds})>[];
    for (var dom = 1; dom <= _daysInMonth; dom++) {
      final current = _selection[dom]!;
      final initial = _initial[dom]!;
      if (!_setsEqual(current, initial)) {
        final sortedIds = current.toList()..sort();
        changes.add((
          day: DateTime(widget.month.year, widget.month.month, dom),
          presetIds: sortedIds,
        ));
      }
    }
    return changes;
  }

  bool _setsEqual(Set<int> a, Set<int> b) =>
      a.length == b.length && a.containsAll(b);

  void _submit() {
    final changes = _computeChanges();
    Navigator.of(context).pop();
    widget.onApply(changes);
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);

    return Dialog(
      insetPadding: const EdgeInsets.symmetric(horizontal: DsSpacing.x10, vertical: DsSpacing.x10),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(DsRadius.xLarge)),
      clipBehavior: Clip.antiAlias,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 660),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // ─── Title bar ────────────────────────────────────────────────
            Padding(
              padding: const EdgeInsets.fromLTRB(
                DsSpacing.x6,
                DsSpacing.x5,
                DsSpacing.x4,
                DsSpacing.x4,
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          l.text('monthFlightsTitle'),
                          style: Theme.of(context)
                              .textTheme
                              .titleLarge
                              ?.copyWith(fontWeight: FontWeight.w700),
                        ),
                        const SizedBox(height: DsSpacing.x1),
                        Text(
                          l.text('monthFlightsHint'),
                          style: const TextStyle(
                            fontSize: DsFontSize.footnote,
                            color: DsColors.textMuted,
                          ),
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close),
                    color: DsColors.textMuted,
                    onPressed: () => Navigator.of(context).pop(),
                  ),
                ],
              ),
            ),

            // ─── Grid ─────────────────────────────────────────────────────
            Flexible(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxHeight: 520),
                child: _BatchGrid(
                  month: widget.month,
                  daysInMonth: _daysInMonth,
                  presets: widget.presets,
                  selection: _selection,
                  onToggleCell: _toggle,
                  onToggleColumn: _toggleColumn,
                ),
              ),
            ),

            // ─── Footer ───────────────────────────────────────────────────
            Container(
              decoration: const BoxDecoration(
                border: Border(top: BorderSide(color: DsColors.border)),
              ),
              padding: const EdgeInsets.symmetric(
                horizontal: DsSpacing.x6,
                vertical: DsSpacing.x4,
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  TextButton(
                    onPressed: () => Navigator.of(context).pop(),
                    child: Text(l.cancel),
                  ),
                  const SizedBox(width: DsSpacing.x3),
                  DsPrimaryButton(
                    label: l.text('applyMonth'),
                    onPressed: _submit,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Grid
// ---------------------------------------------------------------------------

/// Renders the sticky header row + scrollable day rows.
///
/// Layout: narrow fixed Day + Wday columns; preset columns share the remaining
/// width evenly (Expanded) so the grid fills the dialog with no dead space.
/// When there are many presets (>4) it falls back to fixed-width columns with
/// horizontal scroll so they never get crushed.
class _BatchGrid extends StatelessWidget {
  const _BatchGrid({
    required this.month,
    required this.daysInMonth,
    required this.presets,
    required this.selection,
    required this.onToggleCell,
    required this.onToggleColumn,
  });

  final DateTime month;
  final int daysInMonth;
  final List<FlightPresetModel> presets;
  final Map<int, Set<int>> selection;
  final void Function(int day, int presetId) onToggleCell;
  final void Function(int presetId) onToggleColumn;

  static const double _dayColW = 56.0;
  static const double _wdColW = 72.0;
  static const double _presetScrollW = 150.0; // used only in scroll fallback

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final scroll = presets.length > 4;

    final grid = Column(
      children: [
        _HeaderRow(
          presets: presets,
          selection: selection,
          daysInMonth: daysInMonth,
          onToggleColumn: onToggleColumn,
          dayColW: _dayColW,
          wdColW: _wdColW,
          expand: !scroll,
          presetW: _presetScrollW,
          dayLabel: l.text('columnDay'),
          wdLabel: l.text('columnWeekday'),
        ),
        const Divider(height: 1, color: DsColors.border),
        Flexible(
          child: ListView.separated(
            shrinkWrap: true,
            itemCount: daysInMonth,
            separatorBuilder: (_, _) =>
                const Divider(height: 1, color: DsColors.border),
            itemBuilder: (context, index) {
              final dom = index + 1;
              final date = DateTime(month.year, month.month, dom);
              return _DayRow(
                date: date,
                presets: presets,
                selected: selection[dom]!,
                onToggle: (presetId) => onToggleCell(dom, presetId),
                dayColW: _dayColW,
                wdColW: _wdColW,
                expand: !scroll,
                presetW: _presetScrollW,
                striped: index.isOdd,
                l: l,
              );
            },
          ),
        ),
      ],
    );

    if (!scroll) return grid;

    final totalW = _dayColW + _wdColW + presets.length * _presetScrollW;
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: SizedBox(width: totalW, child: grid),
    );
  }
}

// ---------------------------------------------------------------------------
// Shared column layout helper
// ---------------------------------------------------------------------------

/// Builds a row of [dayCell] + [wdCell] + one cell per preset, using the same
/// flex rules for the header and every body row so columns stay aligned.
List<Widget> _columns({
  required Widget dayCell,
  required Widget wdCell,
  required List<Widget> presetCells,
  required double dayColW,
  required double wdColW,
  required bool expand,
  required double presetW,
}) {
  return [
    SizedBox(width: dayColW, child: dayCell),
    SizedBox(width: wdColW, child: wdCell),
    for (final cell in presetCells)
      if (expand)
        Expanded(child: Center(child: cell))
      else
        SizedBox(width: presetW, child: Center(child: cell)),
  ];
}

// ---------------------------------------------------------------------------
// Header
// ---------------------------------------------------------------------------

/// Sticky header: column labels + tri-state "select all" checkboxes, with each
/// preset's STA/STD shown so the admin knows what they are ticking.
class _HeaderRow extends StatelessWidget {
  const _HeaderRow({
    required this.presets,
    required this.selection,
    required this.daysInMonth,
    required this.onToggleColumn,
    required this.dayColW,
    required this.wdColW,
    required this.expand,
    required this.presetW,
    required this.dayLabel,
    required this.wdLabel,
  });

  final List<FlightPresetModel> presets;
  final Map<int, Set<int>> selection;
  final int daysInMonth;
  final void Function(int presetId) onToggleColumn;
  final double dayColW;
  final double wdColW;
  final bool expand;
  final double presetW;
  final String dayLabel;
  final String wdLabel;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: DsColors.surfaceSubtle,
      padding: const EdgeInsets.symmetric(
        horizontal: DsSpacing.x4,
        vertical: DsSpacing.x3,
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: _columns(
          dayColW: dayColW,
          wdColW: wdColW,
          expand: expand,
          presetW: presetW,
          dayCell: _headerLabel(dayLabel),
          wdCell: _headerLabel(wdLabel),
          presetCells: [
            for (final preset in presets)
              _PresetColumnHeader(
                preset: preset,
                selection: selection,
                daysInMonth: daysInMonth,
                onToggle: () => onToggleColumn(preset.id),
              ),
          ],
        ),
      ),
    );
  }

  Widget _headerLabel(String label) => Padding(
        padding: const EdgeInsets.only(bottom: DsSpacing.x3),
        child: Text(
          label,
          style: DsType.tableHeader.copyWith(fontSize: DsFontSize.caption),
          overflow: TextOverflow.ellipsis,
        ),
      );
}

/// One preset column header: label + STA/STD + tri-state checkbox (all/some/none).
class _PresetColumnHeader extends StatelessWidget {
  const _PresetColumnHeader({
    required this.preset,
    required this.selection,
    required this.daysInMonth,
    required this.onToggle,
  });

  final FlightPresetModel preset;
  final Map<int, Set<int>> selection;
  final int daysInMonth;
  final VoidCallback onToggle;

  @override
  Widget build(BuildContext context) {
    var tickedCount = 0;
    for (var d = 1; d <= daysInMonth; d++) {
      if (selection[d]!.contains(preset.id)) tickedCount++;
    }
    final allTicked = tickedCount == daysInMonth;
    final someTicked = tickedCount > 0 && !allTicked;

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          preset.label,
          style: DsType.gridHeader,
          overflow: TextOverflow.ellipsis,
          maxLines: 1,
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 1),
        Text(
          '${preset.sta} · ${preset.std}',
          style: DsType.micro,
          textAlign: TextAlign.center,
        ),
        Checkbox(
          value: allTicked ? true : (someTicked ? null : false),
          tristate: true,
          visualDensity: VisualDensity.compact,
          onChanged: (_) => onToggle(),
        ),
      ],
    );
  }
}

// ---------------------------------------------------------------------------
// Day row
// ---------------------------------------------------------------------------

/// One data row for a day-of-month. Weekend days get a tinted day/weekday label
/// and odd rows are subtly striped for readability.
class _DayRow extends StatelessWidget {
  const _DayRow({
    required this.date,
    required this.presets,
    required this.selected,
    required this.onToggle,
    required this.dayColW,
    required this.wdColW,
    required this.expand,
    required this.presetW,
    required this.striped,
    required this.l,
  });

  final DateTime date;
  final List<FlightPresetModel> presets;
  final Set<int> selected;
  final void Function(int presetId) onToggle;
  final double dayColW;
  final double wdColW;
  final bool expand;
  final double presetW;
  final bool striped;
  final AppLocalizations l;

  @override
  Widget build(BuildContext context) {
    final isWeekend =
        date.weekday == DateTime.saturday || date.weekday == DateTime.sunday;
    final labelColor = isWeekend ? DsColors.primary : DsColors.textPrimary;

    return Container(
      color: striped ? DsColors.surfaceSubtle.withValues(alpha: 0.5) : null,
      padding: const EdgeInsets.symmetric(
        horizontal: DsSpacing.x4,
        vertical: 2,
      ),
      child: Row(
        children: _columns(
          dayColW: dayColW,
          wdColW: wdColW,
          expand: expand,
          presetW: presetW,
          dayCell: Text(
            '${date.day}',
            style: TextStyle(
              fontSize: DsFontSize.body,
              fontWeight: FontWeight.w600,
              color: labelColor,
            ),
          ),
          wdCell: Text(
            l.shortWeekday(date),
            style: TextStyle(
              fontSize: DsFontSize.small,
              color: isWeekend ? DsColors.primary : DsColors.textMuted,
            ),
          ),
          presetCells: [
            for (final preset in presets)
              Checkbox(
                value: selected.contains(preset.id),
                visualDensity: VisualDensity.compact,
                // Disable unticked checkboxes when row already has 2 selected.
                onChanged:
                    (selected.length >= 2 && !selected.contains(preset.id))
                        ? null
                        : (_) => onToggle(preset.id),
              ),
          ],
        ),
      ),
    );
  }
}
