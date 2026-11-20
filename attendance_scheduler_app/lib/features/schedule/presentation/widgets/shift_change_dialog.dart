import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/shift_codes.dart';
import '../../../../core/network/api_error_message.dart';
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
/// [codesOnDay] is the roster on screen for [workDate] (person id → raw
/// code): a swap shows what each side gives before it is sent (owner
/// 2026-11-20); the submit button is the confirmation.
class ShiftChangeRequestDialog extends ConsumerStatefulWidget {
  const ShiftChangeRequestDialog({
    super.key,
    required this.workDate,
    required this.role,
    required this.people,
    required this.currentUserId,
    this.codesOnDay = const {},
  });

  final DateTime workDate;
  final UserRole role;
  final List<UserDirectoryEntry> people;
  final int currentUserId;
  final Map<int, String> codesOnDay;

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

  /// Height of each "Ca của …" row, so a badge row and a "—" row match.
  static const double _shiftRowHeight = 32;

  @override
  void dispose() {
    _noteCtrl.dispose();
    super.dispose();
  }

  /// Swap partners: colleagues of the requester's role only, in natural code
  /// order (T2 before T10). At approval the backend checks that each
  /// person's resulting code is requestable for their own role
  /// (`apply_shift_change`), so a cross-role swap usually fails late there;
  /// offering the same role only avoids that.
  /// [ShiftChangeRequestDialog.people] is GET /users/directory, which lists
  /// active users only.
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

  ShiftCode? _codeOf(int? userId) =>
      userId == null ? null : ShiftCodeX.tryParse(widget.codesOnDay[userId]);

  /// A swap needs a colleague who is on that day's roster (the backend
  /// refuses one without a cell).
  bool get _canSubmit =>
      _kind != 'swap_with' ||
      (_counterpartUserId != null && _codeOf(_counterpartUserId) != null);

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final ctrl = ref.watch(shiftChangeControllerProvider);
    final colleagues = _colleagues;
    final colleagueCode = colleagues
        .where((p) => p.id == _counterpartUserId)
        .map((p) => p.code)
        .firstOrNull;

    return DsFormDialog(
      title: l.text('requestShiftChange'),
      subtitle: l.weekdayDate(widget.workDate),
      width: 320,
      // Top-left corner: the form must not cover the person's roster
      // (customer 2026-11-18); shown with showDsCornerDialog.
      alignment: Alignment.topLeft,
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          DsSegmentedSwitch<String>(
            options: [
              DsSelectOption(value: 'change_code', label: l.text('changeCode')),
              DsSelectOption(value: 'swap_with', label: l.text('swapWith')),
            ],
            value: _kind,
            onChanged: (kind) => setState(() => _kind = kind),
          ),
          const SizedBox(height: DsSpacing.x4),
          if (_kind == 'change_code')
            DsSelectField<ShiftCode>(
              key: const ValueKey('shift-change-code'),
              label: l.text('newShiftCode'),
              value: _selectedCode,
              items: ShiftCodeX.requestableCodesFor(widget.role)
                  .map((c) => DropdownMenuItem(value: c, child: Text(c.code)))
                  .toList(),
              onChanged: (v) {
                if (v != null) setState(() => _selectedCode = v);
              },
            )
          else ...[
            DsSelectField<int?>(
              key: const ValueKey('shift-change-colleague'),
              label: l.text('selectColleague'),
              value: _counterpartUserId,
              items: colleagues
                  .map(
                    (p) => DropdownMenuItem<int?>(
                      value: p.id,
                      child: Text(p.code),
                    ),
                  )
                  .toList(),
              onChanged: (v) => setState(() => _counterpartUserId = v),
            ),
            const SizedBox(height: DsSpacing.x4),
            DsInset(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  _shiftRow(
                    context,
                    l.text('yourShift'),
                    _codeOf(widget.currentUserId),
                  ),
                  if (colleagueCode != null)
                    _shiftRow(
                      context,
                      l.shiftOf(colleagueCode),
                      _codeOf(_counterpartUserId),
                    ),
                ],
              ),
            ),
          ],
          const SizedBox(height: DsSpacing.x4),
          DsTextField(
            controller: _noteCtrl,
            label: l.text('note'),
            maxLines: 2,
          ),
        ],
      ),
      actions: [
        DsTextAction(
          label: l.text('cancel'),
          onPressed: () => Navigator.of(context).pop(),
        ),
        DsPrimaryButton(
          label: l.text('submitRequest'),
          loading: ctrl.isMutating,
          onPressed: ctrl.isMutating || !_canSubmit ? null : _submit,
        ),
      ],
    );
  }

  /// One "Ca của …" line: label left, the day's code right-aligned in a
  /// fixed-width slot so both rows' badges share one column; "—" without a
  /// roster cell.
  Widget _shiftRow(BuildContext context, String label, ShiftCode? code) {
    return SizedBox(
      height: _shiftRowHeight,
      child: Row(
        children: [
          Expanded(
            child: Text(
              label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ),
          SizedBox(
            width: 48,
            child: Align(
              alignment: Alignment.centerRight,
              child: code == null
                  ? const SizedBox(
                      width: 38,
                      child: Text('—', textAlign: TextAlign.center),
                    )
                  : DsShiftBadge(code: code),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _submit() async {
    if (!_canSubmit) return;
    final ok = await ref
        .read(shiftChangeControllerProvider.notifier)
        .submit(
          workDate: widget.workDate,
          kind: _kind,
          requestedCode: _kind == 'change_code' ? _selectedCode.code : null,
          counterpartUserId: _kind == 'swap_with' ? _counterpartUserId : null,
          note: _noteCtrl.text,
        );
    if (mounted) {
      Navigator.of(context).pop(ok);
    }
  }
}

String _isoDate(DateTime d) =>
    '${d.year}-${d.month.toString().padLeft(2, '0')}-'
    '${d.day.toString().padLeft(2, '0')}';

/// Asks the admin to confirm an approval that would break rules: the
/// [lines] are listed and the admin approves anyway or cancels. No lines →
/// true at once, without a dialog.
Future<bool> confirmApprovalWarnings(
  BuildContext context,
  List<String> lines,
) async {
  if (lines.isEmpty) return true;
  final l = AppLocalizations.of(context);
  final confirmed = await showDialog<bool>(
    context: context,
    builder: (ctx) => DsFormDialog(
      title: l.text('approveWarningsTitle'),
      content: RuleWarningsList(lines: lines),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(ctx).pop(false),
          child: Text(l.cancel),
        ),
        DsPrimaryButton(
          label: l.text('approveAnyway'),
          onPressed: () => Navigator.of(ctx).pop(true),
        ),
      ],
    ),
  );
  return confirmed == true;
}

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
        label: _statusLabel(l, request),
        tone: switch (request.status) {
          'approved' => DsTone.success,
          'rejected' => DsTone.danger,
          _ => DsTone.warning,
        },
      ),
    ];
  }

  /// A swap names its step: waiting for the colleague, waiting for the
  /// admin, or declined by the colleague; otherwise the plain status.
  String _statusLabel(AppLocalizations l, ShiftChangeRequest request) {
    if (request.kind != 'swap_with') return l.statusLabel(request.status);
    return switch ((request.status, request.counterpartStatus)) {
      ('pending', 'pending') => l.text('swapAwaitingColleague'),
      ('pending', 'approved') => l.text('swapAwaitingAdmin'),
      ('rejected', 'rejected') => l.text('swapDeclinedByColleague'),
      _ => l.statusLabel(request.status),
    };
  }
}

/// Employee panel: swaps a colleague asked the signed-in person into, each
/// with Accept / Decline. The page shows it only while there is one; an
/// accepted swap goes on to the admin, a declined one is rejected.
/// A successful answer is handed to [onAnswered] (true = accepted); the
/// panel itself only reports a failed one, since answering the last row
/// removes the panel.
class IncomingSwapRequestsPanel extends ConsumerWidget {
  const IncomingSwapRequestsPanel({
    super.key,
    required this.codeById,
    required this.onAnswered,
  });

  /// Person id → code, to show who asks.
  final Map<int, String> codeById;

  final ValueChanged<bool> onAnswered;

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
            l.text('incomingSwapRequests'),
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: DsSpacing.x2),
          ConstrainedBox(
            constraints: const BoxConstraints(
              maxHeight: MyShiftChangeRequestsPanel._maxTableHeight,
            ),
            child: SingleChildScrollView(
              child: DsSurface(
                padding: EdgeInsets.zero,
                child: DsDataTable(
                  columns: [
                    DsTableColumn(header: l.text('employee'), flex: 2),
                    DsTableColumn(header: l.text('date'), flex: 2),
                    // What is exchanged (owner 2026-11-20): the asker's
                    // code of that day, then the colleague's own.
                    DsTableColumn(header: l.text('theirShift'), flex: 2),
                    DsTableColumn(header: l.text('yourShift'), flex: 2),
                    DsTableColumn(header: l.actions, flex: 5),
                  ],
                  rows: [
                    for (final request in state.incoming)
                      [
                        Text(
                          codeById[request.requesterId] ??
                              l.userFallback(request.requesterId),
                          style: DsType.tableCell,
                        ),
                        Text(
                          _isoDate(request.workDate),
                          style: DsType.tableCell,
                        ),
                        _shiftCell(request.requesterShift),
                        _shiftCell(request.counterpartShift),
                        Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            DsTextAction(
                              label: l.text('swapAccept'),
                              icon: Icons.check,
                              tone: DsTone.success,
                              onPressed: state.isMutating
                                  ? null
                                  : () =>
                                        _answer(context, ref, request.id, true),
                            ),
                            DsTextAction(
                              label: l.text('swapDecline'),
                              icon: Icons.close,
                              tone: DsTone.danger,
                              onPressed: state.isMutating
                                  ? null
                                  : () => _answer(
                                      context,
                                      ref,
                                      request.id,
                                      false,
                                    ),
                            ),
                          ],
                        ),
                      ],
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// A roster code as a badge; "—" without a cell (or an unknown code).
  static Widget _shiftCell(String? raw) {
    final code = ShiftCodeX.tryParse(raw);
    return code == null
        ? const Text('—', style: DsType.tableCell)
        : DsShiftBadge(code: code, compact: true);
  }

  Future<void> _answer(
    BuildContext context,
    WidgetRef ref,
    int id,
    bool accept,
  ) async {
    final ctrl = ref.read(shiftChangeControllerProvider.notifier);
    if (await ctrl.respond(id, accept: accept)) {
      onAnswered(accept);
      return;
    }
    if (!context.mounted) return;
    final l = AppLocalizations.of(context);
    DsFeedback.show(
      context,
      apiErrorMessage(
        l,
        ref.read(shiftChangeControllerProvider).error,
        fallbackKey: 'actionFailed',
      ),
      tone: DsTone.danger,
    );
  }
}
