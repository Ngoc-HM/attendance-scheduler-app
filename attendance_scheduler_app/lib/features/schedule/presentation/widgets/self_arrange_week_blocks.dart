import 'package:flutter/material.dart';

import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../domain/entities/schedule_entities.dart';
import '../providers/self_arrange_provider.dart';

/// Week-block editor for the self-arrange tab: 7-day blocks anchored at day 1,
/// each own cell tappable to flip X↔AD in the local draft. Non-flexible codes
/// (AL/S/CD…) render disabled. A per-block "X got/target" badge shows quota.
class SelfArrangeWeekBlocks extends StatelessWidget {
  const SelfArrangeWeekBlocks({
    super.key,
    required this.state,
    required this.onToggle,
  });

  final SelfArrangeState state;
  final void Function(DateTime date) onToggle;

  @override
  Widget build(BuildContext context) {
    final byBlock = <int, List<ShiftAssignment>>{};
    for (final a in state.myAssignments) {
      byBlock.putIfAbsent((a.workDate.day - 1) ~/ 7, () => []).add(a);
    }
    final counts = state.blockOffCounts();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (final block in byBlock.keys.toList()..sort())
          Padding(
            padding: const EdgeInsets.only(bottom: DsSpacing.x3),
            child: _blockCard(context, byBlock[block]!, counts[block]),
          ),
      ],
    );
  }

  Widget _blockCard(
    BuildContext context,
    List<ShiftAssignment> cells,
    (int, int)? count,
  ) {
    final l = AppLocalizations.of(context);
    final ok = count == null || count.$1 == count.$2;
    return DsSurface(
      padding: const EdgeInsets.all(DsSpacing.x3),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  '${cells.first.workDate.day}–${cells.last.workDate.day}',
                  style: const TextStyle(
                    fontWeight: FontWeight.w600,
                    color: DsColors.textSecondary,
                    fontSize: DsFontSize.footnote,
                  ),
                ),
              ),
              if (count != null)
                DsBadge(
                  label: 'X ${count.$1}/${count.$2}',
                  tone: ok ? DsTone.success : DsTone.danger,
                ),
            ],
          ),
          const SizedBox(height: DsSpacing.x2),
          Wrap(
            spacing: DsSpacing.x2,
            runSpacing: DsSpacing.x2,
            children: [for (final a in cells) _dayChip(l, a)],
          ),
        ],
      ),
    );
  }

  Widget _dayChip(AppLocalizations l, ShiftAssignment a) {
    final code = state.codeFor(a.workDate) ?? a.code;
    final changed = state.draft.containsKey(a.workDate);
    final editable = a.code == 'X' || a.code == 'AD';
    final weekend = a.workDate.weekday == DateTime.saturday ||
        a.workDate.weekday == DateTime.sunday;
    final off = code == 'X';

    return ChoiceChip(
      selected: changed,
      onSelected: editable ? (_) => onToggle(a.workDate) : null,
      showCheckmark: false,
      backgroundColor: !editable
          ? DsColors.surfaceMuted
          : off
              ? DsColors.successSoft
              : weekend
                  ? DsColors.primarySoft
                  : DsColors.surfaceSubtle,
      selectedColor: off ? DsColors.successSoft : DsColors.primarySoft,
      side: BorderSide(
        color: changed ? DsColors.primary : DsColors.border,
        width: changed ? 2 : 1,
      ),
      label: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            '${a.workDate.day} ${l.shortWeekday(a.workDate)}',
            style: TextStyle(
              fontSize: DsFontSize.caption,
              color: weekend ? DsColors.primary : DsColors.textMuted,
              fontWeight: FontWeight.w600,
            ),
          ),
          Text(
            code,
            style: TextStyle(
              fontSize: DsFontSize.footnote,
              fontWeight: FontWeight.w700,
              color: off ? DsColors.success : DsColors.textPrimary,
            ),
          ),
        ],
      ),
    );
  }
}
