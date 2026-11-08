import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/shift_codes.dart';
import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../../auth/domain/entities/user.dart';
import '../../../users/data/user_management_datasource.dart';
import '../../domain/entities/schedule_entities.dart';
import '../providers/shift_change_provider.dart';

/// Dialog for a user to request a shift-change on their own cell.
/// [workDate] is the day tapped; [role] (the requester's) limits the codes
/// offered to the requestable set (regular working or off codes, no AL / CD).
/// [people] is the code directory for swap_with (only same-role colleagues
/// are offered); [currentUserId] is excluded from the counterpart picker.
class ShiftChangeRequestDialog extends ConsumerStatefulWidget {
  const ShiftChangeRequestDialog({
    super.key,
    required this.workDate,
    required this.role,
    required this.people,
    required this.currentUserId,
  });

  final DateTime workDate;
  final UserRole role;
  final List<UserDirectoryEntry> people;
  final int currentUserId;

  @override
  ConsumerState<ShiftChangeRequestDialog> createState() =>
      _ShiftChangeRequestDialogState();
}

class _ShiftChangeRequestDialogState
    extends ConsumerState<ShiftChangeRequestDialog> {
  String _kind = 'change_code';
  ShiftCode _selectedCode = ShiftCode.x; // requestable for every role
  int? _counterpartUserId;
  final _noteCtrl = TextEditingController();

  @override
  void dispose() {
    _noteCtrl.dispose();
    super.dispose();
  }

  /// Swap partners: colleagues of the requester's role only (the backend
  /// refuses a cross-role swap at approval), in natural code order (T2
  /// before T10). [ShiftChangeRequestDialog.people] is GET /users/directory,
  /// which lists active users only.
  List<UserDirectoryEntry> get _colleagues =>
      widget.people
          .where((p) => p.id != widget.currentUserId && p.role == widget.role)
          .toList()
        ..sort((a, b) => _compareCodes(a.code, b.code));

  static int _compareCodes(String a, String b) {
    final prefix = _codePrefix(a).compareTo(_codePrefix(b));
    if (prefix != 0) return prefix;
    return _codeSeq(a).compareTo(_codeSeq(b));
  }

  static String _codePrefix(String code) =>
      code.replaceAll(RegExp(r'[0-9]'), '');

  static int _codeSeq(String code) =>
      int.tryParse(code.replaceAll(RegExp(r'[^0-9]'), '')) ?? 0;

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
              items: ShiftCodeX.requestableCodesFor(widget.role)
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
                    (p) => DropdownMenuItem(value: p.id, child: Text(p.code)),
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
/// Each row names the requester and, for a swap, the partner by code (D3).
/// Approving shows the backend's rule warnings and calls [onApproved] so the
/// page reloads the grid the approval changed.
class ShiftChangePendingPanel extends ConsumerWidget {
  const ShiftChangePendingPanel({
    super.key,
    this.codeById = const {},
    this.onApproved,
  });

  /// Person id → code (e.g. "A3").
  final Map<int, String> codeById;

  /// Called after a successful approval (e.g. to reload the schedule grid).
  final VoidCallback? onApproved;

  String _code(AppLocalizations l, int? id) =>
      id == null ? '—' : (codeById[id] ?? l.userFallback(id));

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
        final isSwap = req.kind == 'swap_with';
        return ListTile(
          leading: req.strictReview
              ? const Icon(Icons.warning_amber, color: DsColors.warning)
              : const Icon(Icons.swap_horiz_outlined),
          title: Text(
            '${_code(l, req.requesterId)} · '
            '${l.text(isSwap ? 'swapWith' : 'changeCode')} · '
            '${_isoDate(req.workDate)}',
          ),
          subtitle: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (req.strictReview)
                Text(
                  l.text('strictReviewRequired'),
                  style: const TextStyle(color: DsColors.warning),
                ),
              if (isSwap)
                Text(
                  '${l.text('swapPartner')}: '
                  '${_code(l, req.counterpartUserId)}',
                )
              else if (req.requestedCode != null)
                Text('${l.text("newShiftCode")}: ${req.requestedCode}'),
              if (req.note != null && req.note!.isNotEmpty)
                Text('${l.text('note')}: ${req.note}'),
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
    final decided = await ref
        .read(shiftChangeControllerProvider.notifier)
        .decide(id, status);
    if (!context.mounted) return;
    if (decided == null) {
      DsFeedback.show(
        context,
        ref.read(shiftChangeControllerProvider).error ??
            l.text('actionFailed'),
        tone: DsTone.danger,
      );
      return;
    }
    if (status != 'approved') {
      DsFeedback.show(
        context,
        l.text('requestRejected'),
        tone: DsTone.success,
      );
      return;
    }
    if (decided.warnings.isEmpty) {
      DsFeedback.show(
        context,
        l.text('requestApproved'),
        tone: DsTone.success,
      );
    } else {
      // The approval is saved; the warnings are the backend's rule recheck
      // of the changed cells, listed in full instead of a one-line toast.
      await showDialog<void>(
        context: context,
        builder: (context) => DsFormDialog(
          title: l.text('approvedWithWarnings'),
          content: RuleWarningsList(lines: decided.warnings),
          actions: [
            DsPrimaryButton(
              label: l.text('close'),
              onPressed: () => Navigator.of(context).pop(),
            ),
          ],
        ),
      );
    }
    onApproved?.call();
  }
}

String _isoDate(DateTime d) =>
    '${d.year}-${d.month.toString().padLeft(2, '0')}-'
    '${d.day.toString().padLeft(2, '0')}';

/// Rule warnings / violations, one per line with a warning icon, for a
/// dialog or panel; long lists scroll instead of growing past [maxHeight].
class RuleWarningsList extends StatelessWidget {
  const RuleWarningsList({
    super.key,
    required this.lines,
    this.maxHeight = 280,
  });

  final List<String> lines;
  final double maxHeight;

  @override
  Widget build(BuildContext context) {
    return ConstrainedBox(
      constraints: BoxConstraints(maxHeight: maxHeight),
      child: ListView.builder(
        shrinkWrap: true,
        itemCount: lines.length,
        itemBuilder: (context, i) => Padding(
          padding: const EdgeInsets.symmetric(vertical: DsSpacing.x1),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Padding(
                padding: EdgeInsets.only(right: DsSpacing.x2),
                child: Icon(
                  Icons.warning_amber_outlined,
                  size: 16,
                  color: DsColors.warning,
                ),
              ),
              Expanded(child: Text(lines[i])),
            ],
          ),
        ),
      ),
    );
  }
}

/// Employee panel under the roster: the signed-in user's own shift-change
/// requests (GET /shift-changes) and where each one stands.
class MyShiftChangeRequestsPanel extends ConsumerWidget {
  const MyShiftChangeRequestsPanel({super.key, required this.codeById});

  /// Person id → code, to show who a swap request targets.
  final Map<int, String> codeById;

  /// Keeps the roster above usable; longer lists scroll inside the panel.
  static const double _maxTableHeight = 200;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final state = ref.watch(shiftChangeControllerProvider);

    return Padding(
      padding: const EdgeInsets.all(DsSpacing.x4),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            l.text('myShiftChangeRequests'),
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: DsSpacing.x2),
          if (state.isLoading)
            const LinearProgressIndicator()
          else if (state.loadFailed)
            Text(
              l.text('shiftChangesLoadFailed'),
              style: Theme.of(
                context,
              ).textTheme.bodySmall?.copyWith(color: DsColors.danger),
            )
          else if (state.requests.isEmpty)
            Text(
              l.text('noShiftChangeRequests'),
              style: Theme.of(context).textTheme.bodySmall,
            )
          else
            ConstrainedBox(
              constraints: const BoxConstraints(maxHeight: _maxTableHeight),
              child: SingleChildScrollView(
                child: DsSurface(
                  padding: EdgeInsets.zero,
                  child: DsDataTable(
                    columns: [
                      DsTableColumn(header: l.text('date'), flex: 2),
                      DsTableColumn(header: l.text('type'), flex: 3),
                      DsTableColumn(header: l.text('shiftCodeColumn'), flex: 2),
                      DsTableColumn(header: l.status, flex: 2),
                    ],
                    rows: [
                      for (final request in state.requests) _row(l, request),
                    ],
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }

  List<Widget> _row(AppLocalizations l, ShiftChangeRequest request) {
    final isSwap = request.kind == 'swap_with';
    final target = isSwap
        ? '⇄ ${codeById[request.counterpartUserId] ?? '—'}'
        : (request.requestedCode ?? '—');
    final date = request.workDate;
    return [
      Text(
        '${date.year}-${date.month.toString().padLeft(2, '0')}-'
        '${date.day.toString().padLeft(2, '0')}',
        style: DsType.tableCell,
      ),
      Text(
        l.text(isSwap ? 'swapWith' : 'changeCode'),
        style: DsType.tableCell,
        overflow: TextOverflow.ellipsis,
      ),
      Text(target, style: DsType.tableCell),
      DsBadge(
        label: l.statusLabel(request.status),
        tone: switch (request.status) {
          'approved' => DsTone.success,
          'rejected' => DsTone.danger,
          _ => DsTone.warning,
        },
      ),
    ];
  }
}
