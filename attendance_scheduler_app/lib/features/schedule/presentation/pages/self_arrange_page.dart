import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../providers/self_arrange_provider.dart';
import '../widgets/self_arrange_week_blocks.dart';

/// Self-arrange tab for roles T & F (owner 2026-07-09): edit the OWN row of a
/// published month locally (X↔AD), keep every 7-day block on quota, then
/// submit ONE batch that the admin approves once more.
class SelfArrangePage extends ConsumerStatefulWidget {
  const SelfArrangePage({super.key});

  @override
  ConsumerState<SelfArrangePage> createState() => _SelfArrangePageState();
}

class _SelfArrangePageState extends ConsumerState<SelfArrangePage> {
  DateTime _month = DateTime(DateTime.now().year, DateTime.now().month);
  final _noteCtrl = TextEditingController();

  static int _idx(DateTime m) => m.year * 12 + m.month;

  /// Employees may look at most 2 months ahead (server enforces too).
  bool get _canGoNext {
    final now = DateTime.now();
    return _idx(DateTime(_month.year, _month.month + 1)) <=
        _idx(DateTime(now.year, now.month)) + 2;
  }

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _load());
  }

  @override
  void dispose() {
    _noteCtrl.dispose();
    super.dispose();
  }

  void _load() {
    final userId = ref.read(authControllerProvider).user?.id;
    if (userId == null) return;
    ref
        .read(selfArrangeControllerProvider.notifier)
        .load(_month.year, _month.month, userId);
  }

  void _shiftMonth(int delta) {
    setState(() => _month = DateTime(_month.year, _month.month + delta));
    _load();
  }

  Future<void> _submit(AppLocalizations l) async {
    final ok = await ref
        .read(selfArrangeControllerProvider.notifier)
        .submit(_month.year, _month.month, note: _noteCtrl.text);
    if (!mounted) return;
    if (ok) _noteCtrl.clear();
    DsFeedback.show(
      context,
      ok
          ? l.text('selfArrangeSubmitted')
          : (ref.read(selfArrangeControllerProvider).error ??
              l.text('selfArrangeSubmitFailed')),
      tone: ok ? DsTone.success : DsTone.danger,
    );
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final state = ref.watch(selfArrangeControllerProvider);
    final ctrl = ref.read(selfArrangeControllerProvider.notifier);

    return SingleChildScrollView(
      padding: const EdgeInsets.all(DsSpacing.x4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              IconButton(
                icon: const Icon(Icons.chevron_left),
                onPressed: () => _shiftMonth(-1),
              ),
              Text(
                l.monthYear(_month),
                style: Theme.of(context).textTheme.titleMedium,
              ),
              IconButton(
                icon: const Icon(Icons.chevron_right),
                tooltip: _canGoNext ? null : l.text('selfArrangeMonthCap'),
                onPressed: _canGoNext ? () => _shiftMonth(1) : null,
              ),
            ],
          ),
          const SizedBox(height: DsSpacing.x2),
          DsInlineAlert(
            title: l.text('selfArrangeTitle'),
            message: l.text('selfArrangeHint'),
            tone: DsTone.primary,
          ),
          const SizedBox(height: DsSpacing.x4),
          if (state.isLoading)
            const Center(child: CircularProgressIndicator())
          else if (state.notPublished)
            Text(l.text('scheduleNotPublishedYet'))
          else ...[
            SelfArrangeWeekBlocks(state: state, onToggle: ctrl.toggle),
            const SizedBox(height: DsSpacing.x3),
            TextField(
              controller: _noteCtrl,
              decoration: InputDecoration(
                labelText: l.text('selfArrangeNote'),
                border: const OutlineInputBorder(),
              ),
              maxLines: 2,
            ),
            const SizedBox(height: DsSpacing.x3),
            Row(
              children: [
                DsPrimaryButton(
                  label: l.text('selfArrangeSubmit'),
                  loading: state.isSubmitting,
                  onPressed: state.draft.isEmpty ||
                          !state.draftKeepsQuota ||
                          state.isSubmitting
                      ? null
                      : () => _submit(l),
                ),
                const SizedBox(width: DsSpacing.x3),
                TextButton(
                  onPressed:
                      state.draft.isEmpty ? null : ctrl.discardDraft,
                  child: Text(l.text('selfArrangeDiscard')),
                ),
                const SizedBox(width: DsSpacing.x3),
                if (state.draft.isNotEmpty && !state.draftKeepsQuota)
                  Expanded(
                    child: Text(
                      l.text('selfArrangeQuotaBroken'),
                      style: const TextStyle(color: DsColors.danger),
                    ),
                  ),
              ],
            ),
          ],
          const SizedBox(height: DsSpacing.x6),
          Text(
            l.text('selfArrangeHistory'),
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: DsSpacing.x2),
          if (state.myRequests.isEmpty)
            Text(
              l.text('selfArrangeNoDraft'),
              style: const TextStyle(color: DsColors.textMuted),
            )
          else
            for (final req in state.myRequests)
              ListTile(
                dense: true,
                contentPadding: EdgeInsets.zero,
                leading: Icon(
                  switch (req.status) {
                    'approved' => Icons.check_circle_outline,
                    'rejected' => Icons.cancel_outlined,
                    _ => Icons.hourglass_top_outlined,
                  },
                  color: switch (req.status) {
                    'approved' => DsColors.success,
                    'rejected' => DsColors.danger,
                    _ => DsColors.warning,
                  },
                ),
                title: Text(
                  '${req.year}-${req.month.toString().padLeft(2, '0')} · '
                  '${req.changes.length} ${l.text('selfArrangeChanges')} · '
                  '${l.statusLabel(req.status)}',
                ),
                subtitle: (req.note ?? '').isEmpty ? null : Text(req.note!),
              ),
        ],
      ),
    );
  }
}
