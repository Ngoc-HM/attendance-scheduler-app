import 'package:flutter/foundation.dart' show visibleForTesting;
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../design_system/view_models.dart';
import '../../../auth/domain/entities/user.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../../home/presentation/providers/pending_counts_provider.dart';
import '../../../schedule/data/datasources/schedule_remote_datasource.dart';
import '../../../schedule/domain/entities/schedule_entities.dart';
import '../../../schedule/presentation/providers/schedule_provider.dart';
import '../../../users/data/user_management_datasource.dart';
import '../../data/datasources/leaves_remote_datasource.dart';
import '../../data/models/leave_model.dart';

/// Paired display row + backend ID so approve/reject can pass the real ID.
/// The table holds leave, shift-change and (admin) sign-up rows together
/// (owner 2026-11-20); [row]'s `kind` says which backend [id] belongs to.
class LeaveEntry {
  const LeaveEntry({
    required this.id,
    required this.row,
    this.createdAt,
    this.account,
  });
  final int id;
  final DsLeaveRowData row;

  /// When the request was filed (newest first); null sorts last.
  final DateTime? createdAt;

  /// A sign-up row's account, for the approval dialog's role pick.
  final User? account;

  DsRequestKind get kind => row.kind;
}

/// UI state for the leaves page.
class LeavesState {
  const LeavesState({
    required this.entries,
    this.window,
    this.compDays = 0,
    this.balance,
    this.nextBalance,
  });

  final AsyncValue<List<LeaveEntry>> entries;

  /// Today's registration window (GET /leaves/window); null until it loads
  /// or if it could not be fetched.
  final LeaveWindow? window;

  /// Carried comp days for the "Comp days" card — the employee's own
  /// balance, or for the admin the total over every active user. Taken from
  /// the users, not the leave rows, so it is right with no requests too.
  final int compDays;

  /// The employee's own annual leave this year (GET /leaves/balance, D4).
  /// Null for the admin, whose page covers everyone, until it loads, or if
  /// it could not be fetched.
  final AnnualLeaveBalance? balance;

  /// The same for next year: annual leave is registered the year before, so
  /// the employee needs to see what is left there too (customer 2026-11-18).
  final AnnualLeaveBalance? nextBalance;

  LeavesState copyWith({
    AsyncValue<List<LeaveEntry>>? entries,
    LeaveWindow? window,
    int? compDays,
    AnnualLeaveBalance? balance,
    AnnualLeaveBalance? nextBalance,
  }) => LeavesState(
    entries: entries ?? this.entries,
    window: window ?? this.window,
    compDays: compDays ?? this.compDays,
    balance: balance ?? this.balance,
    nextBalance: nextBalance ?? this.nextBalance,
  );

  /// Mapped display rows consumed by [DsLeavesView].
  AsyncValue<List<DsLeaveRowData>> get rows =>
      entries.whenData((e) => e.map((x) => x.row).toList());
}

/// Starts in the loading state without fetching: [LeavesPage] calls [load]
/// every time it is opened (and from its refresh button), so the list is
/// never the one from the first visit of the session (D4).
class LeavesController extends StateNotifier<LeavesState> {
  LeavesController(
    this._ds,
    this._ref, {
    this.onDecided,
    this.onShiftChangeApproved,
  })
    : super(const LeavesState(entries: AsyncValue.loading()));

  final LeavesRemoteDataSource _ds;
  final Ref _ref;

  /// Runs after every successful approve/reject (the nav badge refresh).
  final void Function()? onDecided;

  /// Runs after a shift change was approved (the roster refresh).
  final void Function()? onShiftChangeApproved;

  /// Bumped by every [load]; a load whose number is no longer the latest
  /// drops its result, so an older, slower response never overwrites a
  /// newer one (Refresh during a load, reload after a decision).
  int _loadSeq = 0;

  bool get _isAdmin => _ref.read(authControllerProvider).user?.isAdmin ?? false;

  /// Load leaves — admin sees all (GET /leaves?all=true); others own only —
  /// with the shift-change requests the same way and, for the admin, the
  /// sign-ups waiting for approval: one table, newest first (owner
  /// 2026-11-20). Also today's registration window and, for employees,
  /// their remaining annual leave.
  ///
  /// Nothing is stored once the controller is disposed: logout invalidates
  /// this provider, possibly mid-load.
  Future<void> load() async {
    if (!mounted) return;
    final seq = ++_loadSeq;
    state = state.copyWith(entries: const AsyncValue.loading());
    final window = _loadWindow();
    final balances = _loadBalances();
    int? compDays;
    final entries = await AsyncValue.guard(() async {
      final isAdmin = _isAdmin;
      final leaves = isAdmin ? await _ds.listAll() : await _ds.listOwn();
      final shiftChanges = await _scheduleDs.fetchShiftChanges(all: isAdmin);
      final userById = await _loadUserMap();
      final codeById = await _loadCodes(
        userById,
        swaps: shiftChanges.any((r) => r.kind == 'swap_with'),
      );
      compDays = userById.values
          .where((u) => u.status == 'active')
          .fold<int>(0, (sum, u) => sum + u.carryComp);
      final merged = [
        for (final l in leaves)
          LeaveEntry(
            id: l.id,
            row: toRow(l, userById),
            createdAt: l.createdAt,
          ),
        for (final r in shiftChanges)
          LeaveEntry(
            id: r.id,
            row: shiftChangeRow(r, userById, codeById),
            createdAt: r.createdAt,
          ),
        if (isAdmin)
          for (final u in userById.values)
            if (u.status == 'pending')
              LeaveEntry(
                id: u.id,
                row: signUpRow(u),
                createdAt: u.createdAt,
                account: u,
              ),
      ];
      return newestFirst(merged);
    });
    final loadedWindow = await window;
    final (loadedBalance, loadedNext) = await balances;
    if (!mounted || seq != _loadSeq) return;
    state = state.copyWith(
      entries: entries,
      window: loadedWindow,
      compDays: compDays,
      balance: loadedBalance,
      nextBalance: loadedNext,
    );
  }

  /// The window only drives the banner and subtitle, so a failed fetch must
  /// not take the leave list down with it; the server re-checks the window
  /// on every submit anyway.
  Future<LeaveWindow?> _loadWindow() async {
    try {
      return await _ds.fetchWindow();
    } catch (_) {
      return null;
    }
  }

  /// The signed-in employee's own balance. The admin's page aggregates every
  /// user, where one person's balance would mislead, so it is not fetched.
  /// Like the window, a failure only hides the card (or its second year).
  Future<(AnnualLeaveBalance?, AnnualLeaveBalance?)> _loadBalances() async {
    if (_isAdmin) return (null, null);
    final AnnualLeaveBalance current;
    try {
      current = await _ds.fetchBalance();
    } catch (_) {
      return (null, null);
    }
    try {
      return (current, await _ds.fetchBalance(year: current.year + 1));
    } catch (_) {
      return (current, null);
    }
  }

  /// Submit a new leave request then reload.
  Future<void> submitRequest({
    required DateTime startDate,
    required DateTime endDate,
    required String leaveType,
    String? note,
  }) async {
    await _ds.create(
      startDate: startDate,
      endDate: endDate,
      leaveType: leaveType,
      note: note,
    );
    await load();
  }

  /// Admin: what approving the leave or shift change at display [index]
  /// would break — asked BEFORE the decision; empty when nothing needs a
  /// confirmation (and for a sign-up, which breaks no rule).
  Future<List<String>> approvalPreview(int index) async {
    final entry = entryAt(index);
    if (entry == null) return const [];
    return switch (entry.kind) {
      DsRequestKind.leave => _ds.approvalPreview(entry.id),
      DsRequestKind.shiftChange => _scheduleDs.shiftChangeApprovalPreview(
        entry.id,
      ),
      DsRequestKind.signUp => Future.value(const <String>[]),
    };
  }

  /// Admin: approve the leave or shift change at display [index]. Returns
  /// decision warnings (e.g. an already-generated month is now stale and
  /// needs a regenerate). A sign-up needs a role: [approveAccount].
  Future<List<String>> approve(int index) => _decide(index, 'approved');

  /// Admin: reject the leave or shift change at display [index]; a sign-up
  /// is rejected by deleting the account, as on the Users page before
  /// (owner 2026-11-20).
  Future<List<String>> reject(int index) async {
    final entry = entryAt(index);
    if (entry?.kind == DsRequestKind.signUp) {
      await _userDs.delete(entry!.id);
      onDecided?.call();
      await load();
      return const [];
    }
    return _decide(index, 'rejected');
  }

  /// Admin: activate the sign-up at display [index] with the [role] picked
  /// in the approval dialog (F-03).
  Future<void> approveAccount(int index, UserRole role) async {
    final entry = entryAt(index);
    if (entry == null || entry.kind != DsRequestKind.signUp) return;
    await _userDs.approve(entry.id, role: role.apiValue);
    onDecided?.call();
    await load();
  }

  Future<List<String>> _decide(int index, String status) async {
    final entry = entryAt(index);
    if (entry == null) return const [];
    final List<String> warnings;
    switch (entry.kind) {
      case DsRequestKind.leave:
        final (_, leaveWarnings) = await _ds.decide(entry.id, status);
        warnings = leaveWarnings;
      case DsRequestKind.shiftChange:
        final decided = await _scheduleDs.decideShiftChange(
          id: entry.id,
          status: status,
        );
        warnings = decided.warnings;
        // An approval rewrites roster cells: the Schedule page must show
        // them without a manual reload.
        if (status == 'approved') onShiftChangeApproved?.call();
      case DsRequestKind.signUp:
        return const [];
    }
    onDecided?.call();
    await load();
    return warnings;
  }

  /// Employee: withdraw the own PENDING leave at display [index]; its
  /// days go back to what can be registered (customer 2026-11-18).
  Future<void> cancel(int index) async {
    final entry = entryAt(index);
    if (entry == null || entry.kind != DsRequestKind.leave) return;
    await _ds.cancel(entry.id);
    await load();
  }

  /// Admin: revoke an APPROVED leave at display [index] (owner 2026-07-17) —
  /// the request flips to rejected, so its days no longer count against the
  /// annual quota (the remaining balance is derived from approved leave), and
  /// span cells still on AL in a generated month go back to X.
  Future<List<String>> revoke(int index) async {
    final entry = entryAt(index);
    if (entry == null || entry.kind != DsRequestKind.leave) return const [];
    final (_, warnings) = await _ds.revoke(entry.id);
    await load();
    return warnings;
  }

  // ---------------------------------------------------------------------------

  /// The row at display [index]; null when out of range or not loaded.
  LeaveEntry? entryAt(int index) {
    final data = state.entries.valueOrNull;
    if (data == null || index < 0 || index >= data.length) return null;
    return data[index];
  }

  ScheduleRemoteDataSource get _scheduleDs =>
      _ref.read(scheduleRemoteDataSourceProvider);

  UserManagementDataSource get _userDs =>
      _ref.read(userManagementDataSourceProvider);

  /// id → code of everyone a shift change may name. The admin has every
  /// account already; an employee with a swap reads the name-free
  /// directory, whose failure only leaves the partner as "—".
  Future<Map<int, String>> _loadCodes(
    Map<int, User> userById, {
    required bool swaps,
  }) async {
    final codes = {for (final u in userById.values) u.id: u.code};
    if (_isAdmin || !swaps) return codes;
    try {
      return {
        for (final p in await _userDs.directory()) p.id: p.code,
        ...codes,
      };
    } catch (_) {
      return codes;
    }
  }

  /// id → User, for showing each request's confidential code + role.
  ///
  /// Admin fetches the full roster directly (fresh, no provider-lifecycle
  /// race that used to leave rows as "User id"). Employees only see their
  /// own rows and GET /users is admin-only, so they use the signed-in user.
  Future<Map<int, User>> _loadUserMap() async {
    if (_isAdmin) {
      final users = await _userDs.list();
      return {for (final u in users) u.id: u};
    }
    final me = _ref.read(authControllerProvider).user;
    return me == null ? {} : {me.id: me};
  }

  @visibleForTesting
  static DsLeaveRowData toRow(LeaveModel m, Map<int, User> userById) {
    final u = userById[m.userId];
    return DsLeaveRowData(
      // Confidential per-person code (e.g. "T3", "A1", "F1") — the app's
      // anonymous identity, shown instead of names (fallback if not found).
      employee: (u != null && u.code.isNotEmpty) ? u.code : 'ID ${m.userId}',
      role: u?.role.apiValue ?? '—',
      type: m.typeLabel,
      range: m.dateRange,
      days: m.days,
      status: m.statusDisplay,
      // Comp days the requester carries into this month (last month close).
      carryComp: u?.carryComp ?? 0,
      // Kept on the row after the decision toast is gone (owner 2026-11-10).
      staffingWarnings: m.staffingWarnings,
    );
  }

  /// A shift change in the leave table's columns: the day with both
  /// people's shifts of that day ("08/11/2026 · F1 (AD) ⇄ F2 (X)" for a
  /// swap, "08/11/2026 · AD → X" for a code change), one day, and the
  /// requester's carry. A swap names its step until the colleague accepted
  /// it; then it is pending like any request the admin decides.
  @visibleForTesting
  static DsLeaveRowData shiftChangeRow(
    ShiftChangeRequest r,
    Map<int, User> userById,
    Map<int, String> codeById,
  ) {
    final u = userById[r.requesterId];
    final isSwap = r.kind == 'swap_with';
    String code(int? id) {
      final known = id == null ? null : codeById[id];
      return (known != null && known.isNotEmpty) ? known : '—';
    }

    final shifts = isSwap
        ? '${code(r.requesterId)} (${r.requesterShift ?? '—'}) ⇄ '
              '${code(r.counterpartUserId)} (${r.counterpartShift ?? '—'})'
        : '${r.requesterShift ?? '—'} → ${r.requestedCode ?? '—'}';
    return DsLeaveRowData(
      employee: code(r.requesterId) == '—'
          ? 'ID ${r.requesterId}'
          : code(r.requesterId),
      role: u?.role.apiValue ?? '—',
      type: isSwap ? 'Shift swap' : 'Code change',
      range: '${_ddmmyyyy(r.workDate)} · $shifts',
      days: 1,
      status: switch ((r.status, isSwap ? r.counterpartStatus : null)) {
        ('pending', 'pending') => DsLeaveRowData.statusAwaitingColleague,
        ('rejected', 'rejected') => DsLeaveRowData.statusDeclinedByColleague,
        ('pending', _) => 'Pending',
        ('approved', _) => 'Approved',
        ('rejected', _) => 'Rejected',
        (final other, _) => other,
      },
      carryComp: u?.carryComp ?? 0,
      kind: DsRequestKind.shiftChange,
    );
  }

  /// A self-registered account waiting for approval: shown by username (no
  /// code yet), with the role it holds now and its sign-up date.
  @visibleForTesting
  static DsLeaveRowData signUpRow(User u) => DsLeaveRowData(
    employee: u.username,
    role: u.role.apiValue,
    type: 'New account',
    range: u.createdAt == null ? '—' : _ddmmyyyy(u.createdAt!.toLocal()),
    days: null,
    status: 'Pending',
    carryComp: null,
    kind: DsRequestKind.signUp,
  );

  /// Newest first; rows without a date keep their order after the dated
  /// ones (the sort is stable).
  @visibleForTesting
  static List<LeaveEntry> newestFirst(List<LeaveEntry> entries) {
    final indexed = entries.indexed.toList()
      ..sort((a, b) {
        final ta = a.$2.createdAt;
        final tb = b.$2.createdAt;
        if (ta == null || tb == null) {
          if (ta != null) return -1;
          if (tb != null) return 1;
          return a.$1.compareTo(b.$1);
        }
        final byTime = tb.compareTo(ta);
        return byTime != 0 ? byTime : a.$1.compareTo(b.$1);
      });
    return [for (final (_, e) in indexed) e];
  }

  static String _ddmmyyyy(DateTime d) =>
      '${d.day.toString().padLeft(2, '0')}/'
      '${d.month.toString().padLeft(2, '0')}/${d.year}';
}

final leavesControllerProvider =
    StateNotifierProvider<LeavesController, LeavesState>(
      (ref) => LeavesController(
        ref.watch(leavesDataSourceProvider),
        ref,
        onDecided: () => refreshPendingCounts(ref),
        onShiftChangeApproved: () => refreshRosterAfterShiftChange(ref),
      ),
    );
