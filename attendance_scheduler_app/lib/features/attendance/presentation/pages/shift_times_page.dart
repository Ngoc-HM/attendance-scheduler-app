import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/api_error_message.dart';
import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../data/datasources/shift_times_remote_datasource.dart';

/// The frames of shifts A and D as stored, plus the derived A/D frame.
final shiftTimesProvider = FutureProvider.autoDispose<List<ShiftFrame>>(
  (ref) => ref.watch(shiftTimesRemoteDataSourceProvider).fetch(),
);

/// The admin sets the working-time frame of shifts A and D (decision #71,
/// store and display only). A third, read-only row shows the double shift's
/// frame: the earliest start to the latest end.
class ShiftTimesPage extends ConsumerStatefulWidget {
  const ShiftTimesPage({super.key});

  @override
  ConsumerState<ShiftTimesPage> createState() => _ShiftTimesPageState();
}

class _ShiftTimesPageState extends ConsumerState<ShiftTimesPage> {
  /// Unsaved edits by code ('A', 'D'); empty until the admin picks a time.
  final Map<String, ShiftFrame> _edits = {};
  bool _busy = false;

  /// Every time button has this width, so the rows line up.
  static const double _timeWidth = 136;
  static const double _codeWidth = 64;

  Future<void> _pick(ShiftFrame frame, {required bool start}) async {
    final current = (start ? frame.start : frame.end).split(':');
    final picked = await showTimePicker(
      context: context,
      initialTime: TimeOfDay(
        hour: int.parse(current[0]),
        minute: int.parse(current[1]),
      ),
      builder: (context, child) => MediaQuery(
        data: MediaQuery.of(context).copyWith(alwaysUse24HourFormat: true),
        child: child!,
      ),
    );
    if (picked == null) return;
    final hm =
        '${picked.hour.toString().padLeft(2, '0')}:'
        '${picked.minute.toString().padLeft(2, '0')}';
    setState(
      () => _edits[frame.code] = ShiftFrame(
        code: frame.code,
        start: start ? hm : frame.start,
        end: start ? frame.end : hm,
      ),
    );
  }

  Future<void> _save(List<ShiftFrame> singles) async {
    final l = AppLocalizations.of(context);
    setState(() => _busy = true);
    try {
      await ref.read(shiftTimesRemoteDataSourceProvider).save(singles);
      _edits.clear();
      ref.invalidate(shiftTimesProvider);
      if (mounted) {
        DsFeedback.show(
          context,
          l.text('shiftTimesSaved'),
          tone: DsTone.success,
        );
      }
    } catch (e) {
      if (mounted) {
        DsFeedback.show(context, apiErrorMessage(l, e), tone: DsTone.danger);
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  /// The double shift's frame from the frames on screen (edits included).
  static ShiftFrame _double(List<ShiftFrame> singles) {
    String pick(Iterable<String> v, bool earliest) =>
        v.reduce((a, b) => (a.compareTo(b) <= 0) == earliest ? a : b);
    return ShiftFrame(
      code: 'A/D',
      start: pick(singles.map((f) => f.start), true),
      end: pick(singles.map((f) => f.end), false),
      derived: true,
    );
  }

  Widget _row(BuildContext context, ShiftFrame frame) {
    final editable = !frame.derived && !_busy;
    Widget time(bool start) => SizedBox(
      width: _timeWidth,
      child: DsSecondaryButton(
        icon: Icons.schedule,
        label: start ? frame.start : frame.end,
        expand: true,
        onPressed: editable ? () => _pick(frame, start: start) : null,
      ),
    );
    return Padding(
      padding: const EdgeInsets.symmetric(
        horizontal: DsSpacing.x5,
        vertical: DsSpacing.x2,
      ),
      child: Row(
        children: [
          SizedBox(
            width: _codeWidth,
            child: Text(
              frame.code,
              style: Theme.of(
                context,
              ).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600),
            ),
          ),
          time(true),
          const SizedBox(width: DsSpacing.x3),
          time(false),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final frames = ref.watch(shiftTimesProvider);
    final singles = [
      for (final f in frames.valueOrNull ?? const <ShiftFrame>[])
        if (!f.derived) _edits[f.code] ?? f,
    ];

    return DsPage(
      title: l.text('navShiftTimes'),
      actions: [
        DsPrimaryButton(
          label: l.text('save'),
          icon: Icons.check,
          loading: _busy,
          onPressed: _edits.isEmpty || _busy ? null : () => _save(singles),
        ),
      ],
      child: frames.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Text(
          apiErrorMessage(l, e),
          style: const TextStyle(color: DsColors.danger),
        ),
        data: (_) {
          final rows = [...singles, if (singles.isNotEmpty) _double(singles)];
          return DsSurface(
            padding: EdgeInsets.zero,
            child: Column(
              children: [
                for (var i = 0; i < rows.length; i++) ...[
                  if (i > 0) const Divider(height: 1),
                  _row(context, rows[i]),
                ],
              ],
            ),
          );
        },
      ),
    );
  }
}
