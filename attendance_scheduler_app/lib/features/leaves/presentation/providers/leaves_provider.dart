import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../design_system/view_models.dart';
import '../../../auth/domain/entities/user.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../../home/presentation/providers/pending_counts_provider.dart';
import '../../../users/data/user_management_datasource.dart';
import '../../data/datasources/leaves_remote_datasource.dart';
import '../../data/models/leave_model.dart';

/// Paired display row + backend ID so approve/reject can pass the real ID.
class LeaveEntry {
  const LeaveEntry({required this.id, required this.row});
  final int id;
  final DsLeaveRowData row;
}

/// UI state for the leaves page.
class LeavesState {
  const LeavesState({
    required this.entries,
    this.window,
    this.compDays = 0,
    this.balance,
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

  LeavesState copyWith({
    AsyncValue<List<LeaveEntry>>? entries,
    LeaveWindow? window,
    int? compDays,
    AnnualLeaveBalance? balance,
  }) =>
      LeavesState(
        entries: entries ?? this.entries,
        window: window ?? this.window,
        compDays: compDays ?? this.compDays,
        balance: balance ?? this.balance,
      );

  /// Mapped display rows consumed by [DsLeavesView].
  AsyncValue<List<DsLeaveRowData>> get rows =>
      entries.whenData((e) => e.map((x) => x.row).toList());
}

/// Starts in the loading state without fetching: [LeavesPage] calls [load]
/// every time it is opened (and from its refresh button), so the list is
/// never the one from the first visit of the session (D4).
class LeavesController extends StateNotifier<LeavesState> {
  LeavesController(this._ds, this._ref, {this.onDecided})
      : super(const LeavesState(entries: AsyncValue.loading()));

  final LeavesRemoteDataSource _ds;
  final Ref _ref;

  /// Runs after every successful approve/reject (the nav badge refresh).
  final void Function()? onDecided;

  /// Bumped by every [load]; a load whose number is no longer the latest
  /// drops its result, so an older, slower response never overwrites a
  /// newer one (Refresh during a load, reload after a decision).
  int _loadSeq = 0;

  bool get _isAdmin =>
      _ref.read(authControllerProvider).user?.isAdmin ?? false;

  /// Load leaves — admin sees all (GET /leaves?all=true); others own only —
  /// together with today's registration window and, for employees, their
  /// remaining annual leave.
  ///
  /// Nothing is stored once the controller is disposed: logout invalidates
  /// this provider, possibly mid-load.
  Future<void> load() async {
    if (!mounted) return;
    final seq = ++_loadSeq;
    state = state.copyWith(entries: const AsyncValue.loading());
    final window = _loadWindow();
    final balance = _loadBalance();
    int? compDays;
    final entries = await AsyncValue.guard(() async {
      final leaves = _isAdmin ? await _ds.listAll() : await _ds.listOwn();
      final userById = await _loadUserMap();
      compDays = userById.values
          .where((u) => u.status == 'active')
          .fold<int>(0, (sum, u) => sum + u.carryComp);
      return leaves
          .map((l) => LeaveEntry(id: l.id, row: _toRow(l, userById)))
          .toList();
    });
    final loadedWindow = await window;
    final loadedBalance = await balance;
    if (!mounted || seq != _loadSeq) return;
    state = state.copyWith(
      entries: entries,
      window: loadedWindow,
      compDays: compDays,
      balance: loadedBalance,
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
  /// Like the window, a failure only hides the card.
  Future<AnnualLeaveBalance?> _loadBalance() async {
    if (_isAdmin) return null;
    try {
      return await _ds.fetchBalance();
    } catch (_) {
      return null;
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

  /// Admin: approve the leave at display [index]. Returns decision warnings
  /// (e.g. an already-generated month is now stale and needs a regenerate).
  Future<List<String>> approve(int index) async {
    final id = _idAt(index);
    if (id == null) return const [];
    final (_, warnings) = await _ds.decide(id, 'approved');
    onDecided?.call();
    await load();
    return warnings;
  }

  /// Admin: reject the leave at display [index].
  Future<List<String>> reject(int index) async {
    final id = _idAt(index);
    if (id == null) return const [];
    final (_, warnings) = await _ds.decide(id, 'rejected');
    onDecided?.call();
    await load();
    return warnings;
  }

  /// Admin: revoke an APPROVED leave at display [index] (owner 2026-07-17) —
  /// the request flips to rejected, so its days no longer count against the
  /// annual quota (the remaining balance is derived from approved leave), and
  /// span cells still on AL in a generated month go back to X.
  Future<List<String>> revoke(int index) async {
    final id = _idAt(index);
    if (id == null) return const [];
    final (_, warnings) = await _ds.revoke(id);
    await load();
    return warnings;
  }

  // ---------------------------------------------------------------------------

  int? _idAt(int index) {
    final data = state.entries.valueOrNull;
    if (data == null || index >= data.length) return null;
    return data[index].id;
  }

  /// id → User, for showing each request's confidential code + role.
  ///
  /// Admin fetches the full roster directly (fresh, no provider-lifecycle
  /// race that used to leave rows as "User id"). Employees only see their
  /// own rows and GET /users is admin-only, so they use the signed-in user.
  Future<Map<int, User>> _loadUserMap() async {
    if (_isAdmin) {
      final users = await _ref.read(userManagementDataSourceProvider).list();
      return {for (final u in users) u.id: u};
    }
    final me = _ref.read(authControllerProvider).user;
    return me == null ? {} : {me.id: me};
  }

  static DsLeaveRowData _toRow(LeaveModel m, Map<int, User> userById) {
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
    );
  }
}

final leavesControllerProvider =
    StateNotifierProvider<LeavesController, LeavesState>(
  (ref) => LeavesController(
    ref.watch(leavesDataSourceProvider),
    ref,
    onDecided: () => refreshPendingCounts(ref),
  ),
);
