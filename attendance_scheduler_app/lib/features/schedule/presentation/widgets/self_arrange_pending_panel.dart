import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../providers/self_arrange_provider.dart';

/// Admin panel listing pending self-arrange batches with approve/reject
/// (owner 2026-07-09). Mounted on the admin schedule page next to the
/// shift-change panel. Approving applies every cell of the batch.
class SelfArrangePendingPanel extends ConsumerWidget {
  const SelfArrangePendingPanel({super.key, this.onDecided});

  /// Called after a successful decision (e.g. to reload the schedule grid).
  final VoidCallback? onDecided;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final state = ref.watch(selfArrangeAdminControllerProvider);
    final pending =
        state.requests.where((r) => r.status == 'pending').toList();

    if (state.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (pending.isEmpty) {
      return const SizedBox.shrink();
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(
              horizontal: DsSpacing.x4, vertical: DsSpacing.x2),
          child: Text(
            l.text('selfArrangePanelTitle'),
            style: Theme.of(context).textTheme.titleMedium,
          ),
        ),
        ListView.separated(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: pending.length,
          separatorBuilder: (_, _) => const Divider(height: 1),
          itemBuilder: (context, i) {
            final req = pending[i];
            final days = req.changes
                .map((c) => '${c.workDate.day}→${c.code}')
                .join(', ');
            return ListTile(
              leading: const Icon(Icons.edit_calendar_outlined),
              title: Text(
                '${l.userFallback(req.requesterId)} · ${req.year}-'
                '${req.month.toString().padLeft(2, '0')} · '
                '${req.changes.length} ${l.text('selfArrangeChanges')}',
              ),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(days,
                      style: const TextStyle(fontSize: DsFontSize.caption)),
                  if ((req.note ?? '').isNotEmpty)
                    Text(req.note!,
                        style:
                            const TextStyle(color: DsColors.textMuted)),
                ],
              ),
              trailing: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  IconButton(
                    icon: const Icon(Icons.check_circle_outline,
                        color: DsColors.success),
                    tooltip: l.text('approve'),
                    onPressed: state.isMutating
                        ? null
                        : () => _decide(context, ref, req.id, 'approved', l),
                  ),
                  IconButton(
                    icon: const Icon(Icons.cancel_outlined,
                        color: DsColors.danger),
                    tooltip: l.text('reject'),
                    onPressed: state.isMutating
                        ? null
                        : () => _decide(context, ref, req.id, 'rejected', l),
                  ),
                ],
              ),
            );
          },
        ),
      ],
    );
  }

  Future<void> _decide(
    BuildContext context,
    WidgetRef ref,
    int id,
    String status,
    AppLocalizations l,
  ) async {
    final decided = await ref
        .read(selfArrangeAdminControllerProvider.notifier)
        .decide(id, status);
    if (decided != null) onDecided?.call();
    if (!context.mounted) return;
    if (decided == null) {
      DsFeedback.show(
        context,
        ref.read(selfArrangeAdminControllerProvider).error ?? 'error',
        tone: DsTone.danger,
      );
      return;
    }
    // Surface the hard-rule recheck warnings the backend returns on approval
    // (F-09 parity) — the admin confirmed the change but must see the impact.
    final hasWarnings = decided.warnings.isNotEmpty;
    DsFeedback.show(
      context,
      hasWarnings
          ? '${l.text('selfArrangeDecided')} ${decided.warnings.join('; ')}'
          : l.text('selfArrangeDecided'),
      tone: hasWarnings ? DsTone.warning : DsTone.success,
    );
  }
}
