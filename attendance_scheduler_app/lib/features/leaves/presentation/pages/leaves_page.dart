import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/api_exception.dart';
import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../providers/leaves_provider.dart';

/// Leaves page (F-05 / F-06).
///
/// All users: submit request, view own leaves.
/// Admin: view all leaves, approve / reject pending.
class LeavesPage extends ConsumerWidget {
  const LeavesPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(leavesControllerProvider);
    final ctrl = ref.read(leavesControllerProvider.notifier);
    final isAdmin = ref.watch(authControllerProvider).user?.isAdmin ?? false;
    final l = AppLocalizations.of(context);

    return state.rows.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (err, _) => Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              err is ApiException ? err.message : l.text('leavesLoadFailed'),
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 12),
            DsPrimaryButton(label: l.text('retry'), onPressed: ctrl.load),
          ],
        ),
      ),
      data: (rows) => DsLeavesView(
        rows: rows,
        onNewRequest: () => _showRequestDialog(context, ref, l),
        onApprove: isAdmin
            ? (index) => _decide(context, ref, ctrl, index, true, l)
            : (_) {},
        onReject: isAdmin
            ? (index) => _decide(context, ref, ctrl, index, false, l)
            : (_) {},
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Approve / reject
  // ---------------------------------------------------------------------------

  Future<void> _decide(
    BuildContext context,
    WidgetRef ref,
    LeavesController ctrl,
    int index,
    bool approve,
    AppLocalizations l,
  ) async {
    try {
      if (approve) {
        await ctrl.approve(index);
      } else {
        await ctrl.reject(index);
      }
      if (context.mounted) {
        DsFeedback.show(
          context,
          approve ? l.text('requestApproved') : l.text('requestRejected'),
          tone: approve ? DsTone.success : DsTone.danger,
        );
      }
    } on ApiException catch (e) {
      if (context.mounted) {
        DsFeedback.show(context, e.message, tone: DsTone.danger);
      }
    }
  }

  // ---------------------------------------------------------------------------
  // Submit request dialog
  // ---------------------------------------------------------------------------

  Future<void> _showRequestDialog(
    BuildContext context,
    WidgetRef ref,
    AppLocalizations l,
  ) async {
    DateTime? startDate;
    DateTime? endDate;
    final noteCtrl = TextEditingController();
    final startCtrl = TextEditingController();
    final endCtrl = TextEditingController();

    String fmtDate(DateTime d) =>
        '${d.day.toString().padLeft(2, '0')}/${d.month.toString().padLeft(2, '0')}/${d.year}';

    await showDialog<void>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setS) => DsFormDialog(
          title: l.text('requestLeave'),
          width: 340,
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Start date picker
              TextField(
                controller: startCtrl,
                readOnly: true,
                decoration: InputDecoration(
                  labelText: l.text('startDate'),
                  prefixIcon: const Icon(Icons.calendar_today_outlined, size: 20),
                ),
                onTap: () async {
                  final picked = await showDatePicker(
                    context: ctx,
                    initialDate: DateTime.now(),
                    firstDate: DateTime(2020),
                    lastDate: DateTime(2030),
                  );
                  if (picked != null) {
                    setS(() {
                      startDate = picked;
                      startCtrl.text = fmtDate(picked);
                      // Auto-fill end if not set yet.
                      if (endDate == null) {
                        endDate = picked;
                        endCtrl.text = fmtDate(picked);
                      }
                    });
                  }
                },
              ),
              const SizedBox(height: 12),
              // End date picker
              TextField(
                controller: endCtrl,
                readOnly: true,
                decoration: InputDecoration(
                  labelText: l.text('endDate'),
                  prefixIcon: const Icon(Icons.calendar_today_outlined, size: 20),
                ),
                onTap: () async {
                  final picked = await showDatePicker(
                    context: ctx,
                    initialDate: startDate ?? DateTime.now(),
                    firstDate: startDate ?? DateTime(2020),
                    lastDate: DateTime(2030),
                  );
                  if (picked != null) {
                    setS(() {
                      endDate = picked;
                      endCtrl.text = fmtDate(picked);
                    });
                  }
                },
              ),
              const SizedBox(height: 12),
              TextField(
                controller: noteCtrl,
                maxLines: 2,
                decoration: InputDecoration(labelText: l.text('note')),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(),
              child: Text(l.cancel),
            ),
            DsPrimaryButton(
              label: l.text('submitRequest'),
              onPressed: () async {
                if (startDate == null || endDate == null) return;
                Navigator.of(ctx).pop();
                final ctrl = ref.read(leavesControllerProvider.notifier);
                try {
                  await ctrl.submitRequest(
                    startDate: startDate!,
                    endDate: endDate!,
                    note: noteCtrl.text.trim().isEmpty
                        ? null
                        : noteCtrl.text.trim(),
                  );
                  if (context.mounted) {
                    DsFeedback.show(
                      context,
                      l.text('leaveSubmitted'),
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
      ),
    );
  }
}
