import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/shift_codes.dart';
import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../../auth/domain/entities/user.dart';
import '../providers/shift_change_provider.dart';

/// Dialog for a user to request a shift-change on their own cell.
/// [workDate] is the day tapped. [users] is the full user list for swap_with.
/// [currentUserId] is used to exclude self from counterpart picker.
class ShiftChangeRequestDialog extends ConsumerStatefulWidget {
  const ShiftChangeRequestDialog({
    super.key,
    required this.workDate,
    required this.users,
    required this.currentUserId,
  });

  final DateTime workDate;
  final List<User> users;
  final int currentUserId;

  @override
  ConsumerState<ShiftChangeRequestDialog> createState() =>
      _ShiftChangeRequestDialogState();
}

class _ShiftChangeRequestDialogState
    extends ConsumerState<ShiftChangeRequestDialog> {
  String _kind = 'change_code';
  ShiftCode _selectedCode = ShiftCode.x;
  int? _counterpartUserId;
  final _noteCtrl = TextEditingController();

  @override
  void dispose() {
    _noteCtrl.dispose();
    super.dispose();
  }

  List<User> get _colleagues => widget.users
      .where((u) => u.id != widget.currentUserId)
      .toList();

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final ctrl = ref.watch(shiftChangeControllerProvider);

    return DsFormDialog(
      title: l.text('requestShiftChange'),
      width: 360,
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '${l.text('date')}: ${widget.workDate.year}-'
            '${widget.workDate.month.toString().padLeft(2, '0')}-'
            '${widget.workDate.day.toString().padLeft(2, '0')}',
          ),
          const SizedBox(height: DsSpacing.x4),
          SegmentedButton<String>(
            segments: [
              ButtonSegment(
                value: 'change_code',
                label: Text(l.text('changeCode')),
              ),
              ButtonSegment(
                value: 'swap_with',
                label: Text(l.text('swapWith')),
              ),
            ],
            selected: {_kind},
            onSelectionChanged: (s) => setState(() => _kind = s.first),
          ),
          const SizedBox(height: DsSpacing.x4),
          if (_kind == 'change_code') ...[
            Text(l.text('newShiftCode')),
            const SizedBox(height: DsSpacing.x2),
            DropdownButton<ShiftCode>(
              value: _selectedCode,
              isExpanded: true,
              items: ShiftCode.values
                  .map(
                    (c) => DropdownMenuItem(
                      value: c,
                      child: Text(c.code),
                    ),
                  )
                  .toList(),
              onChanged: (v) {
                if (v != null) setState(() => _selectedCode = v);
              },
            ),
          ] else ...[
            Text(l.text('selectColleague')),
            const SizedBox(height: DsSpacing.x2),
            DropdownButton<int>(
              value: _counterpartUserId,
              isExpanded: true,
              hint: Text(l.text('selectColleague')),
              items: _colleagues
                  .map(
                    (u) => DropdownMenuItem(
                      value: u.id,
                      child: Text(u.fullName.isNotEmpty
                          ? u.fullName
                          : u.username),
                    ),
                  )
                  .toList(),
              onChanged: (v) => setState(() => _counterpartUserId = v),
            ),
          ],
          const SizedBox(height: DsSpacing.x4),
          TextField(
            controller: _noteCtrl,
            decoration: InputDecoration(
              labelText: l.text('note'),
              border: const OutlineInputBorder(),
            ),
            maxLines: 2,
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: Text(l.text('cancel')),
        ),
        DsPrimaryButton(
          label: l.text('submitRequest'),
          loading: ctrl.isMutating,
          onPressed: ctrl.isMutating ? null : _submit,
        ),
      ],
    );
  }

  Future<void> _submit() async {
    if (_kind == 'swap_with' && _counterpartUserId == null) return;
    final ok = await ref.read(shiftChangeControllerProvider.notifier).submit(
          workDate: widget.workDate,
          kind: _kind,
          requestedCode:
              _kind == 'change_code' ? _selectedCode.code : null,
          counterpartUserId:
              _kind == 'swap_with' ? _counterpartUserId : null,
          note: _noteCtrl.text,
        );
    if (mounted) {
      Navigator.of(context).pop(ok);
    }
  }
}

/// Admin panel showing pending shift-change requests with approve/reject.
class ShiftChangePendingPanel extends ConsumerWidget {
  const ShiftChangePendingPanel({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final state = ref.watch(shiftChangeControllerProvider);
    final pending =
        state.requests.where((r) => r.status == 'pending').toList();

    if (state.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (pending.isEmpty) {
      return Padding(
        padding: const EdgeInsets.all(DsSpacing.x4),
        child: Text(l.text('noPendingShiftChanges')),
      );
    }

    return ListView.separated(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: pending.length,
      separatorBuilder: (_, _) => const Divider(height: 1),
      itemBuilder: (context, i) {
        final req = pending[i];
        return ListTile(
          leading: req.strictReview
              ? const Icon(Icons.warning_amber, color: DsColors.warning)
              : const Icon(Icons.swap_horiz_outlined),
          title: Text(
            '${req.kind} — ${req.workDate.year}-'
            '${req.workDate.month.toString().padLeft(2, '0')}-'
            '${req.workDate.day.toString().padLeft(2, '0')}',
          ),
          subtitle: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (req.strictReview)
                Text(
                  l.text('strictReviewRequired'),
                  style: const TextStyle(color: DsColors.warning),
                ),
              if (req.requestedCode != null)
                Text('${l.text("newShiftCode")}: ${req.requestedCode}'),
              if (req.warnings.isNotEmpty)
                Text(
                  req.warnings.join('; '),
                  style: const TextStyle(color: DsColors.danger, fontSize: DsFontSize.micro),
                ),
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
                icon: const Icon(Icons.cancel_outlined, color: DsColors.danger),
                tooltip: l.text('reject'),
                onPressed: state.isMutating
                    ? null
                    : () => _decide(context, ref, req.id, 'rejected', l),
              ),
            ],
          ),
        );
      },
    );
  }

  Future<void> _decide(
    BuildContext context,
    WidgetRef ref,
    int id,
    String status,
    AppLocalizations l,
  ) async {
    final ok = await ref
        .read(shiftChangeControllerProvider.notifier)
        .decide(id, status);
    if (context.mounted) {
      DsFeedback.show(
        context,
        ok
            ? (status == 'approved'
                ? l.text('requestApproved')
                : l.text('requestRejected'))
            : (ref.read(shiftChangeControllerProvider).error ?? 'error'),
        tone: ok ? DsTone.success : DsTone.danger,
      );
    }
  }
}
