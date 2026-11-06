import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/api_exception.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../../users/data/user_management_datasource.dart';
import '../../data/datasources/schedule_remote_datasource.dart';
import '../../domain/entities/schedule_entities.dart';

// ── State classes ──────────────────────────────────────────────────────────────

class ScheduleState {
  const ScheduleState({
    this.schedule,
    this.people = const [],
    this.isLoading = false,
    this.isMutating = false,
    this.error,
    this.lastResult,
  });

  final MonthlySchedule? schedule;

  /// id → code/role source for the roster columns (people are shown by
  /// their confidential code, never by name).
  final List<UserDirectoryEntry> people;
  final bool isLoading;
  final bool isMutating;
  final String? error;
  final ScheduleResult? lastResult; // most-recent generate result

  ScheduleState copyWith({
    MonthlySchedule? schedule,
    List<UserDirectoryEntry>? people,
    bool? isLoading,
    bool? isMutating,
    String? error,
    ScheduleResult? lastResult,
    bool clearError = false,
    bool clearResult = false,
  }) =>
      ScheduleState(
        schedule: schedule ?? this.schedule,
        people: people ?? this.people,
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

  /// Loads the month and the people behind its columns. GET /users is
  /// admin-only, so employees read the name-free GET /users/directory.
  Future<void> load(int year, int month, {bool isAdmin = false}) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final results = await Future.wait<Object>([
        _ds.fetchSchedule(year, month),
        isAdmin ? _allUsers() : _userDs.directory(),
      ]);
      state = state.copyWith(
        schedule: results[0] as MonthlySchedule,
        people: results[1] as List<UserDirectoryEntry>,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  /// Admin view: every account (pending/disabled too), reduced to code + role.
  Future<List<UserDirectoryEntry>> _allUsers() async => [
    for (final u in await _userDs.list())
      UserDirectoryEntry(id: u.id, code: u.code, role: u.role),
  ];

  /// Rethrows the backend's 409 (month published or manually edited, needs
  /// [force]) so the page can confirm with the admin and retry; every other
  /// failure lands in [ScheduleState.error].
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
      if (e is ApiException && e.statusCode == 409) {
        state = state.copyWith(isMutating: false);
        rethrow;
      }
      state = state.copyWith(isMutating: false, error: e.toString());
    }
  }

  /// Admin cell edit (F-09). Returns the recheck warnings (empty = clean);
  /// null when the call itself failed (error is set on the state).
  Future<List<String>?> overrideCell({
    required int userId,
    required DateTime workDate,
    required String code,
  }) async {
    final scheduleId = state.schedule?.id;
    if (scheduleId == null) return null;
    state = state.copyWith(isMutating: true, clearError: true);
    try {
      final result = await _ds.override(
        scheduleId: scheduleId,
        userId: userId,
        workDate: workDate,
        code: code,
      );
      state = state.copyWith(
        isMutating: false,
        schedule: result.schedule ?? state.schedule,
      );
      return result.violations.map((v) => v.message).toList();
    } catch (e) {
      state = state.copyWith(isMutating: false, error: e.toString());
      return null;
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
