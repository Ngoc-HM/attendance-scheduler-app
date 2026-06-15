import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../design_system/view_models.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../../users/presentation/providers/users_provider.dart';
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
  const LeavesState({required this.entries});

  final AsyncValue<List<LeaveEntry>> entries;

  LeavesState copyWith({AsyncValue<List<LeaveEntry>>? entries}) =>
      LeavesState(entries: entries ?? this.entries);

  /// Mapped display rows consumed by [DsLeavesView].
  AsyncValue<List<DsLeaveRowData>> get rows =>
      entries.whenData((e) => e.map((x) => x.row).toList());
}

class LeavesController extends StateNotifier<LeavesState> {
  LeavesController(this._ds, this._ref)
      : super(const LeavesState(entries: AsyncValue.loading())) {
    load();
  }

  final LeavesRemoteDataSource _ds;
  final Ref _ref;

  bool get _isAdmin =>
      _ref.read(authControllerProvider).user?.isAdmin ?? false;

  /// Load leaves — admin sees all (GET /leaves?all=true); others own only.
  Future<void> load() async {
    state = state.copyWith(entries: const AsyncValue.loading());
    state = state.copyWith(
      entries: await AsyncValue.guard(() async {
        final leaves = _isAdmin ? await _ds.listAll() : await _ds.listOwn();
        final userMap = _buildUserMap();
        return leaves
            .map((l) => LeaveEntry(id: l.id, row: _toRow(l, userMap)))
            .toList();
      }),
    );
  }

  /// Submit a new leave request then reload.
  Future<void> submitRequest({
    required DateTime startDate,
    required DateTime endDate,
    String? note,
  }) async {
    await _ds.create(startDate: startDate, endDate: endDate, note: note);
    await load();
  }

  /// Admin: approve the leave at display [index].
  Future<void> approve(int index) async {
    final id = _idAt(index);
    if (id == null) return;
    await _ds.decide(id, 'approved');
    await load();
  }

  /// Admin: reject the leave at display [index].
  Future<void> reject(int index) async {
    final id = _idAt(index);
    if (id == null) return;
    await _ds.decide(id, 'rejected');
    await load();
  }

  // ---------------------------------------------------------------------------

  int? _idAt(int index) {
    final data = state.entries.valueOrNull;
    if (data == null || index >= data.length) return null;
    return data[index].id;
  }

  Map<int, String> _buildUserMap() {
    final usersValue = _ref.read(usersControllerProvider);
    return usersValue.whenOrNull(
          data: (users) => {for (final u in users) u.id: u.fullName},
        ) ??
        {};
  }

  static DsLeaveRowData _toRow(LeaveModel m, Map<int, String> userMap) =>
      DsLeaveRowData(
        employee: userMap[m.userId] ?? 'User ${m.userId}',
        role: '—',
        type: m.typeLabel,
        range: m.dateRange,
        days: m.days,
        status: m.statusDisplay,
        carryComp: 0,
      );
}

final leavesControllerProvider =
    StateNotifierProvider<LeavesController, LeavesState>(
  (ref) => LeavesController(
    ref.watch(leavesDataSourceProvider),
    ref,
  ),
);
