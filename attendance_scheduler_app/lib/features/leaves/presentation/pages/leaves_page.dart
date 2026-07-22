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
            const SizedBox(height: DsSpacing.x3),
            DsPrimaryButton(label: l.text('retry'), onPressed: ctrl.load),
          ],
        ),
      ),
      data: (rows) => DsLeavesView(
        rows: rows,
        onNewRequest: () => _showRequestDialog(context, ref, l),
        // Null for employees → the actions column disappears entirely
        // (no-op Approve/Reject buttons looked like a permissions hole).
        onApprove: isAdmin
            ? (index) => _decide(context, ref, ctrl, index, true, l)
            : null,
        onReject: isAdmin
            ? (index) => _decide(context, ref, ctrl, index, false, l)
            : null,
        onRevoke: isAdmin
            ? (index) => _confirmRevoke(context, ref, ctrl, index, l)
            : null,
        // Development mode: registration is intentionally always open.
        registrationOpen: true,
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
      final warnings = approve
          ? await ctrl.approve(index)
          : await ctrl.reject(index);
      if (context.mounted) {
        final base = approve
            ? l.text('requestApproved')
            : l.text('requestRejected');
        // Decision-time warnings (e.g. an already-generated month is now
        // stale and must be regenerated) must reach the admin's eyes.
        DsFeedback.show(
          context,
          warnings.isEmpty ? base : '$base ${warnings.join('; ')}',
          tone: warnings.isNotEmpty
              ? DsTone.warning
              : (approve ? DsTone.success : DsTone.danger),
        );
      }
    } on ApiException catch (e) {
      if (context.mounted) {
        DsFeedback.show(context, e.message, tone: DsTone.danger);
      }
    }
  }

  /// Revoking undoes an approval (balance restored, request rejected) —
  /// destructive enough to warrant an explicit confirm (owner 2026-07-17).
  Future<void> _confirmRevoke(
    BuildContext context,
    WidgetRef ref,
    LeavesController ctrl,
    int index,
    AppLocalizations l,
  ) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => DsFormDialog(
        title: l.text('revokeApproval'),
        width: 380,
        content: Text(l.text('revokeConfirmMessage')),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: Text(l.cancel),
          ),
          DsPrimaryButton(
            label: l.text('revokeApproval'),
            onPressed: () => Navigator.of(ctx).pop(true),
          ),
        ],
      ),
    );
    if (confirmed != true || !context.mounted) return;
    try {
      final warnings = await ctrl.revoke(index);
      if (context.mounted) {
        final base = l.text('requestRevoked');
        DsFeedback.show(
          context,
          warnings.isEmpty ? base : '$base ${warnings.join('; ')}',
          tone: warnings.isEmpty ? DsTone.success : DsTone.warning,
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

    final now = DateTime.now();
    final firstAllowed = DateTime(2000);

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
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Registration-window guidance (matches backend leave_windows).
              Text(
                l.text('leaveWindowHint'),
                style: Theme.of(ctx).textTheme.bodySmall,
              ),
              const SizedBox(height: DsSpacing.x3),
              // Start date picker
              TextField(
                controller: startCtrl,
                readOnly: true,
                decoration: InputDecoration(
                  labelText: l.text('startDate'),
                  prefixIcon: const Icon(
                    Icons.calendar_today_outlined,
                    size: 20,
                  ),
                ),
                onTap: () async {
                  final picked = await showDatePicker(
                    context: ctx,
                    initialDate: startDate ?? now,
                    firstDate: firstAllowed,
                    lastDate: DateTime(2100),
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
              const SizedBox(height: DsSpacing.x3),
              // End date picker
              TextField(
                controller: endCtrl,
                readOnly: true,
                decoration: InputDecoration(
                  labelText: l.text('endDate'),
                  prefixIcon: const Icon(
                    Icons.calendar_today_outlined,
                    size: 20,
                  ),
                ),
                onTap: () async {
                  final picked = await showDatePicker(
                    context: ctx,
                    initialDate: endDate ?? startDate ?? now,
                    firstDate: startDate ?? firstAllowed,
                    lastDate: DateTime(2100),
                  );
                  if (picked != null) {
                    setS(() {
                      endDate = picked;
                      endCtrl.text = fmtDate(picked);
                    });
                  }
                },
              ),
              const SizedBox(height: DsSpacing.x3),
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
                // Empty dates used to silently no-op — tell the user.
                if (startDate == null || endDate == null) {
                  DsFeedback.show(ctx, l.fieldRequired, tone: DsTone.warning);
                  return;
                }
                final ctrl = ref.read(leavesControllerProvider.notifier);
                try {
                  await ctrl.submitRequest(
                    startDate: startDate!,
                    endDate: endDate!,
                    note: noteCtrl.text.trim().isEmpty
                        ? null
                        : noteCtrl.text.trim(),
                  );
                  // Close only AFTER success — a window-closed 400 used to
                  // wipe the user's input because the dialog popped first.
                  if (ctx.mounted) Navigator.of(ctx).pop();
                  if (context.mounted) {
                    DsFeedback.show(
                      context,
                      l.text('leaveSubmitted'),
                      tone: DsTone.success,
                    );
                  }
                } on ApiException catch (e) {
                  if (ctx.mounted) {
                    DsFeedback.show(ctx, e.message, tone: DsTone.danger);
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
