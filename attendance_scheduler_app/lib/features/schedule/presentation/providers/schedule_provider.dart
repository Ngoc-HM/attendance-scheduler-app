import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../auth/presentation/providers/auth_provider.dart';
import '../../../users/data/user_management_datasource.dart';
import '../../../auth/domain/entities/user.dart';
import '../../data/datasources/schedule_remote_datasource.dart';
import '../../domain/entities/schedule_entities.dart';

// ── State classes ──────────────────────────────────────────────────────────────

class ScheduleState {
  const ScheduleState({
    this.schedule,
    this.users = const [],
    this.isLoading = false,
    this.isMutating = false,
    this.error,
    this.lastResult,
  });

  final MonthlySchedule? schedule;
  final List<User> users; // id→name map source (admin only)
  final bool isLoading;
  final bool isMutating;
  final String? error;
  final ScheduleResult? lastResult; // most-recent generate result

  ScheduleState copyWith({
    MonthlySchedule? schedule,
    List<User>? users,
    bool? isLoading,
    bool? isMutating,
    String? error,
    ScheduleResult? lastResult,
    bool clearError = false,
    bool clearResult = false,
  }) =>
      ScheduleState(
        schedule: schedule ?? this.schedule,
        users: users ?? this.users,
        isLoading: isLoading ?? this.isLoading,
        isMutating: isMutating ?? this.isMutating,
        error: clearError ? null : (error ?? this.error),
        lastResult: clearResult ? null : (lastResult ?? this.lastResult),
      );
}

// ── Controller ────────────────────────────────────────────────────────────────

class ScheduleController extends StateNotifier<ScheduleState> {
  ScheduleController(this._ds, this._userDs) : super(const ScheduleState());

  final ScheduleRemoteDataSource _ds;
  final UserManagementDataSource _userDs;

  Future<void> load(int year, int month, {bool isAdmin = false}) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final futures = <Future>[
        _ds.fetchSchedule(year, month),
        if (isAdmin) _userDs.list(),
      ];
      final results = await Future.wait(futures);
      final schedule = results[0] as MonthlySchedule;
      final users =
          (isAdmin && results.length > 1) ? results[1] as List<User> : <User>[];
      state = state.copyWith(
        schedule: schedule,
        users: users,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> generate(int year, int month, {bool force = false}) async {
    state = state.copyWith(isMutating: true, clearError: true, clearResult: true);
    try {
      final result = await _ds.generate(year: year, month: month, force: force);
      state = state.copyWith(
        isMutating: false,
        schedule: result.schedule ?? state.schedule,
        lastResult: result,
      );
    } catch (e) {
      state = state.copyWith(isMutating: false, error: e.toString());
    }
  }

  Future<void> overrideCell({
    required int userId,
    required DateTime workDate,
    required String code,
  }) async {
    final scheduleId = state.schedule?.id;
    if (scheduleId == null) return;
    state = state.copyWith(isMutating: true, clearError: true);
    try {
      final updated = await _ds.override(
        scheduleId: scheduleId,
        userId: userId,
        workDate: workDate,
        code: code,
      );
      state = state.copyWith(isMutating: false, schedule: updated);
    } catch (e) {
      state = state.copyWith(isMutating: false, error: e.toString());
    }
  }

  void clearResult() {
    state = state.copyWith(clearResult: true);
  }

  Future<void> publish() async {
    final scheduleId = state.schedule?.id;
    if (scheduleId == null) return;
    state = state.copyWith(isMutating: true, clearError: true);
    try {
      final updated = await _ds.publish(scheduleId);
      state = state.copyWith(isMutating: false, schedule: updated);
    } catch (e) {
      state = state.copyWith(isMutating: false, error: e.toString());
    }
  }
}

// ── Providers ─────────────────────────────────────────────────────────────────

final scheduleControllerProvider =
    StateNotifierProvider<ScheduleController, ScheduleState>(
  (ref) => ScheduleController(
    ref.watch(scheduleRemoteDataSourceProvider),
    ref.watch(userManagementDataSourceProvider),
  ),
);

/// Convenience: current user is admin.
final isAdminProvider = Provider<bool>((ref) {
  final user = ref.watch(authControllerProvider).user;
  return user?.isAdmin ?? false;
});
