import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../data/models/flight_day_model.dart';
import '../../data/models/flight_preset_model.dart';

/// Batch-editor dialog: shows the whole [month] as a tick-grid.
///
/// Transposed layout: DAYS run horizontally as columns (1..N, with weekday),
/// PRESETS are the vertical rows. Admin ticks cells to assign presets to days,
/// then hits "Apply whole month". Returns ONLY the days whose selection CHANGED
/// from the initial state.
class MonthBatchDialog extends ConsumerStatefulWidget {
  const MonthBatchDialog({
    super.key,
    required this.month,
    required this.presets,
    required this.existingDays,
    required this.loadMonth,
    required this.onApply,
  });

  /// The month shown when the dialog opens (year + month, day ignored).
  final DateTime month;

  /// Active presets only — these become the grid rows.
  final List<FlightPresetModel> presets;

  /// Flight data for the INITIAL month — seeds tick state without a refetch.
  final List<FlightDayModel> existingDays;

  /// Loads flight data for another month when the admin switches months.
  final Future<List<FlightDayModel>> Function(DateTime month) loadMonth;

  /// Called with the month last shown + the changed items (which may span
  /// several visited months) when the admin taps "Apply".
  final void Function(
    DateTime month,
    List<({DateTime day, List<int> presetIds})> items,
  ) onApply;

  @override
  ConsumerState<MonthBatchDialog> createState() => _MonthBatchDialogState();
}

class _MonthBatchDialogState extends ConsumerState<MonthBatchDialog> {
  /// Ticks keyed by FULL date, so selections persist across visited months
  /// (lets the admin fill the current month AND next month, then apply once).
  final Map<DateTime, Set<int>> _selection = {};
  final Map<DateTime, Set<int>> _initial = {};

  /// 'year-month' keys already ingested — avoids refetching / resetting them.
  final Set<String> _loaded = {};

  late DateTime _month; // currently displayed month
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _month = DateTime(widget.month.year, widget.month.month);
    _ingest(_month, widget.existingDays);
  }

  String _mk(DateTime m) => '${m.year}-${m.month}';

  DateTime _date(int dom) => DateTime(_month.year, _month.month, dom);

  /// Seed selection + initial snapshot for [month] from its flight data.
  /// A preset is "applied" to a day when BOTH preset.fltArr AND preset.fltDep
  /// appear among that day's flight fltNumber values.
  void _ingest(DateTime month, List<FlightDayModel> days) {
    final n = DateUtils.getDaysInMonth(month.year, month.month);
    for (var dom = 1; dom <= n; dom++) {
      final date = DateTime(month.year, month.month, dom);
      _selection.putIfAbsent(date, () => <int>{});
      _initial.putIfAbsent(date, () => <int>{});
    }
    for (final dm in days) {
      final date = DateTime(dm.day.year, dm.day.month, dm.day.day);
      final flt = dm.flights.map((f) => f.fltNumber).toSet();
      final sel = <int>{};
      for (final p in widget.presets) {
        if (flt.contains(p.fltArr) && flt.contains(p.fltDep)) sel.add(p.id);
      }
      _selection[date] = Set<int>.of(sel);
      _initial[date] = Set<int>.of(sel);
    }
    _loaded.add(_mk(month));
  }

  /// Switch the displayed month; lazily loads its data the first time.
  Future<void> _goToMonth(DateTime target) async {
    final t = DateTime(target.year, target.month);
    if (_loaded.contains(_mk(t))) {
      setState(() => _month = t);
      return;
    }
    setState(() => _loading = true);
    try {
      final data = await widget.loadMonth(t);
      if (!mounted) return;
      setState(() {
        _ingest(t, data);
        _month = t;
        _loading = false;
      });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _toggle(int dom, int presetId) {
    setState(() {
      final s = _selection[_date(dom)]!;
      if (s.contains(presetId)) {
        s.remove(presetId);
      } else if (s.length < 2) {
        s.add(presetId);
      }
    });
  }

  /// Toggle a preset across all days of the CURRENT month (row "select all").
  void _togglePresetAll(int presetId) {
    final n = DateUtils.getDaysInMonth(_month.year, _month.month);
    setState(() {
      final allTicked = [
        for (var dom = 1; dom <= n; dom++) _selection[_date(dom)]!,
      ].every((s) => s.contains(presetId));
      for (var dom = 1; dom <= n; dom++) {
        final s = _selection[_date(dom)]!;
        if (allTicked) {
          s.remove(presetId);
        } else if (!s.contains(presetId) && s.length < 2) {
          s.add(presetId);
        }
      }
    });
  }

  /// Changed days across ALL visited months (vs their initial snapshot).
  List<({DateTime day, List<int> presetIds})> _computeChanges() {
    final changes = <({DateTime day, List<int> presetIds})>[];
    for (final entry in _selection.entries) {
      final init = _initial[entry.key] ?? const <int>{};
      if (!_setsEqual(entry.value, init)) {
        changes.add((day: entry.key, presetIds: entry.value.toList()..sort()));
      }
    }
    return changes;
  }

  bool _setsEqual(Set<int> a, Set<int> b) =>
      a.length == b.length && a.containsAll(b);

  void _submit() {
    final changes = _computeChanges();
    final shown = _month;
    Navigator.of(context).pop();
    widget.onApply(shown, changes);
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final screen = MediaQuery.of(context).size;
    final daysInMonth = DateUtils.getDaysInMonth(_month.year, _month.month);
    // Per-month view (day-of-month → tick set) the grid understands.
    final view = <int, Set<int>>{
      for (var dom = 1; dom <= daysInMonth; dom++) dom: _selection[_date(dom)]!,
    };

    return Dialog(
      insetPadding: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(DsRadius.xLarge),
      ),
      clipBehavior: Clip.antiAlias,
      child: SizedBox(
        // 90% of the app window — big canvas; days spread across the width.
        width: screen.width * 0.9,
        height: screen.height * 0.9,
        child: Column(
          children: [
            // ─── Title bar + month switcher ───────────────────────────────
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
                  // Pick which month to fill (current / next / any).
                  _MonthSwitcher(
                    label: l.monthYear(_month),
                    enabled: !_loading,
                    onPrev: () =>
                        _goToMonth(DateTime(_month.year, _month.month - 1)),
                    onNext: () =>
                        _goToMonth(DateTime(_month.year, _month.month + 1)),
                  ),
                  const SizedBox(width: DsSpacing.x2),
                  IconButton(
                    icon: const Icon(Icons.close),
                    color: DsColors.textMuted,
                    onPressed: () => Navigator.of(context).pop(),
                  ),
                ],
              ),
            ),

            // ─── Grid (transposed: days across, presets down) ─────────────
            Expanded(
              child: _loading
                  ? const Center(child: CircularProgressIndicator())
                  : _TransposedGrid(
                      month: _month,
                      daysInMonth: daysInMonth,
                      presets: widget.presets,
                      selection: view,
                      onToggleCell: _toggle,
                      onTogglePresetAll: _togglePresetAll,
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

/// Compact ‹ Month Year › selector for the dialog header.
class _MonthSwitcher extends StatelessWidget {
  const _MonthSwitcher({
    required this.label,
    required this.enabled,
    required this.onPrev,
    required this.onNext,
  });

  final String label;
  final bool enabled;
  final VoidCallback onPrev;
  final VoidCallback onNext;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        border: Border.all(color: DsColors.border),
        borderRadius: BorderRadius.circular(DsRadius.medium),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          IconButton(
            icon: const Icon(Icons.chevron_left),
            iconSize: 20,
            onPressed: enabled ? onPrev : null,
          ),
          ConstrainedBox(
            constraints: const BoxConstraints(minWidth: 110),
            child: Text(
              label,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: DsFontSize.body,
                fontWeight: FontWeight.w600,
                color: DsColors.textPrimary,
              ),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.chevron_right),
            iconSize: 20,
            onPressed: enabled ? onNext : null,
          ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Grid (transposed)
// ---------------------------------------------------------------------------

/// Column geometry shared by the fixed preset column and the scrollable days.
const double _presetColW = 210;
const double _minDayColW = 44; // days spread wider when there is room
const double _headerH = 52;
const double _rowH = 60;

/// Renders a sticky left column (preset labels + row "select all") next to a
/// horizontally-scrollable band of day columns. Vertical scroll kicks in only
/// if there are many presets.
class _TransposedGrid extends StatelessWidget {
  const _TransposedGrid({
    required this.month,
    required this.daysInMonth,
    required this.presets,
    required this.selection,
    required this.onToggleCell,
    required this.onTogglePresetAll,
  });

  final DateTime month;
  final int daysInMonth;
  final List<FlightPresetModel> presets;
  final Map<int, Set<int>> selection;
  final void Function(int day, int presetId) onToggleCell;
  final void Function(int presetId) onTogglePresetAll;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final gridHeight = _headerH + presets.length * _rowH;

    return LayoutBuilder(
      builder: (context, constraints) {
        // Spread the days to fill the width; only scroll if they won't fit.
        final availForDays = constraints.maxWidth - _presetColW;
        final fits = daysInMonth * _minDayColW <= availForDays;
        final dayW = fits ? availForDays / daysInMonth : _minDayColW;
        final daysWidth = daysInMonth * dayW;

        final dayBand = Column(
          children: [
            _DayHeaderRow(
              month: month,
              daysInMonth: daysInMonth,
              dayW: dayW,
              l: l,
            ),
            for (final preset in presets)
              _PresetCheckboxRow(
                preset: preset,
                month: month,
                daysInMonth: daysInMonth,
                selection: selection,
                onToggleCell: onToggleCell,
                dayW: dayW,
              ),
          ],
        );

        return SingleChildScrollView(
          // Vertical safety for many presets; normally not needed (2-3 rows).
          child: SizedBox(
            height: gridHeight,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── Fixed left column: preset labels + per-row select-all ──
                _PresetLabelColumn(
                  presets: presets,
                  selection: selection,
                  daysInMonth: daysInMonth,
                  onTogglePresetAll: onTogglePresetAll,
                ),
                // ── Day columns: fill width, or scroll horizontally ──
                if (fits)
                  SizedBox(width: daysWidth, child: dayBand)
                else
                  Expanded(
                    child: SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: SizedBox(width: daysWidth, child: dayBand),
                    ),
                  ),
              ],
            ),
          ),
        );
      },
    );
  }
}

/// Shared cell container so the fixed column and scroll band align pixel-perfect.
Widget _cell({
  required double width,
  required double height,
  Widget? child,
  Color? background,
  bool rightBorder = false,
  AlignmentGeometry alignment = Alignment.center,
  EdgeInsetsGeometry padding = EdgeInsets.zero,
}) {
  return Container(
    width: width,
    height: height,
    alignment: alignment,
    padding: padding,
    decoration: BoxDecoration(
      color: background,
      border: Border(
        bottom: const BorderSide(color: DsColors.border),
        right: rightBorder
            ? const BorderSide(color: DsColors.border)
            : BorderSide.none,
      ),
    ),
    child: child,
  );
}

/// Fixed left column: a corner cell + one labelled row per preset, each with a
/// tri-state "select all days" checkbox.
class _PresetLabelColumn extends StatelessWidget {
  const _PresetLabelColumn({
    required this.presets,
    required this.selection,
    required this.daysInMonth,
    required this.onTogglePresetAll,
  });

  final List<FlightPresetModel> presets;
  final Map<int, Set<int>> selection;
  final int daysInMonth;
  final void Function(int presetId) onTogglePresetAll;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Corner (sits above the day numbers).
        _cell(
          width: _presetColW,
          height: _headerH,
          background: DsColors.surfaceSubtle,
          rightBorder: true,
        ),
        for (final preset in presets)
          _cell(
            width: _presetColW,
            height: _rowH,
            rightBorder: true,
            alignment: Alignment.centerLeft,
            padding: const EdgeInsets.symmetric(horizontal: DsSpacing.x4),
            child: _PresetLabel(
              preset: preset,
              selection: selection,
              daysInMonth: daysInMonth,
              onToggle: () => onTogglePresetAll(preset.id),
            ),
          ),
      ],
    );
  }
}

/// Preset name + STA/STD + tri-state "tick every day" checkbox.
class _PresetLabel extends StatelessWidget {
  const _PresetLabel({
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
    var ticked = 0;
    for (var d = 1; d <= daysInMonth; d++) {
      if (selection[d]!.contains(preset.id)) ticked++;
    }
    final all = ticked == daysInMonth;
    final some = ticked > 0 && !all;

    return Row(
      children: [
        Expanded(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                preset.label,
                style: const TextStyle(
                  fontSize: DsFontSize.body,
                  fontWeight: FontWeight.w700,
                  color: DsColors.textPrimary,
                ),
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 1),
              Text(
                '${preset.sta} · ${preset.std}',
                style: const TextStyle(
                  fontSize: DsFontSize.caption,
                  color: DsColors.textMuted,
                ),
              ),
            ],
          ),
        ),
        Checkbox(
          value: all ? true : (some ? null : false),
          tristate: true,
          visualDensity: VisualDensity.compact,
          onChanged: (_) => onToggle(),
        ),
      ],
    );
  }
}

/// Header band: day number + weekday for each day (weekend tinted).
class _DayHeaderRow extends StatelessWidget {
  const _DayHeaderRow({
    required this.month,
    required this.daysInMonth,
    required this.dayW,
    required this.l,
  });

  final DateTime month;
  final int daysInMonth;
  final double dayW;
  final AppLocalizations l;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        for (var dom = 1; dom <= daysInMonth; dom++)
          _dayHeaderCell(DateTime(month.year, month.month, dom)),
      ],
    );
  }

  Widget _dayHeaderCell(DateTime date) {
    final weekend = date.weekday == DateTime.saturday ||
        date.weekday == DateTime.sunday;
    final color = weekend ? DsColors.primary : DsColors.textPrimary;
    return _cell(
      width: dayW,
      height: _headerH,
      background: DsColors.surfaceSubtle,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            '${date.day}',
            style: TextStyle(
              fontSize: DsFontSize.footnote,
              fontWeight: FontWeight.w700,
              color: color,
            ),
          ),
          Text(
            l.shortWeekday(date),
            style: TextStyle(
              fontSize: DsFontSize.micro,
              color: weekend ? DsColors.primary : DsColors.textMuted,
            ),
          ),
        ],
      ),
    );
  }
}

/// One preset row: a checkbox per day. Caps at 2 presets per day (column).
class _PresetCheckboxRow extends StatelessWidget {
  const _PresetCheckboxRow({
    required this.preset,
    required this.month,
    required this.daysInMonth,
    required this.selection,
    required this.onToggleCell,
    required this.dayW,
  });

  final FlightPresetModel preset;
  final DateTime month;
  final int daysInMonth;
  final Map<int, Set<int>> selection;
  final void Function(int day, int presetId) onToggleCell;
  final double dayW;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        for (var dom = 1; dom <= daysInMonth; dom++)
          _cell(
            width: dayW,
            height: _rowH,
            child: Checkbox(
              value: selection[dom]!.contains(preset.id),
              visualDensity: VisualDensity.compact,
              // Disable when the day already holds 2 other presets.
              onChanged: (selection[dom]!.length >= 2 &&
                      !selection[dom]!.contains(preset.id))
                  ? null
                  : (_) => onToggleCell(dom, preset.id),
            ),
          ),
      ],
    );
  }
}
