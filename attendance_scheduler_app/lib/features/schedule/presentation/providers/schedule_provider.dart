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
    this.loadError,
    this.loadErrorStatus,
    this.lastResult,
    this.violations,
  });

  /// The month last requested by [ScheduleController.load], or null when it
  /// has no schedule (404) or failed to load. Never a previous month's.
  final MonthlySchedule? schedule;

  /// id → code/role source for the roster columns (people are shown by
  /// their confidential code, never by name).
  final List<UserDirectoryEntry> people;
  final bool isLoading;
  final bool isMutating;

  /// Failed generate / edit / publish: the caught error, which the page
  /// turns into text with `apiErrorMessage` (backend detail, or a translated
  /// "server unavailable" / "server error"). Shown as a toast.
  final Object? error;

  /// Failed [ScheduleController.load] only (same kind of value as [error]),
  /// kept apart from [error] so a failed generate never reads as "could not
  /// load".
  final Object? loadError;

  /// HTTP status of the failed load (404 = month not generated / not
  /// published); null when the load did not fail or never reached a server.
  final int? loadErrorStatus;
  final ScheduleResult? lastResult; // most-recent generate result

  /// Admin only: hard-rule violations of [schedule] as it stands now.
  /// Null = not checked (employee, no schedule, or the check failed).
  final List<ConstraintViolation>? violations;

  /// True when [schedule] is the given month, so publish and cell edits
  /// never act on a month that is not on screen.
  bool holds(int year, int month) =>
      schedule != null && schedule!.year == year && schedule!.month == month;

  ScheduleState copyWith({
    MonthlySchedule? schedule,
    List<UserDirectoryEntry>? people,
    bool? isLoading,
    bool? isMutating,
    Object? error,
    Object? loadError,
    int? loadErrorStatus,
    ScheduleResult? lastResult,
    List<ConstraintViolation>? violations,
    bool clearError = false,
    bool clearLoadError = false,
    bool clearResult = false,
    bool clearSchedule = false,
    bool clearViolations = false,
  }) =>
      ScheduleState(
        schedule: clearSchedule ? null : (schedule ?? this.schedule),
        people: people ?? this.people,
        isLoading: isLoading ?? this.isLoading,
        isMutating: isMutating ?? this.isMutating,
        error: clearError ? null : (error ?? this.error),
        loadError: clearLoadError ? null : (loadError ?? this.loadError),
        loadErrorStatus: clearLoadError
            ? null
            : (loadErrorStatus ?? this.loadErrorStatus),
        lastResult: clearResult ? null : (lastResult ?? this.lastResult),
        violations: clearViolations ? null : (violations ?? this.violations),
      );
}

// ── Controller ────────────────────────────────────────────────────────────────

class ScheduleController extends StateNotifier<ScheduleState> {
  ScheduleController(this._ds, this._userDs) : super(const ScheduleState());

  final ScheduleRemoteDataSource _ds;
  final UserManagementDataSource _userDs;

  /// Bumped by every [load]; the response of an older load is dropped so a
  /// slow month can never overwrite the month on screen.
  int _loadSeq = 0;

  /// Loads the month and the people behind its columns. GET /users is
  /// admin-only, so employees read the name-free GET /users/directory.
  /// The previous month's grid is cleared at once (A3): an admin on a month
  /// without a schedule sees the empty state, never last month's roster.
  /// Admins also get the month's rule violations (C2).
  Future<void> load(int year, int month, {bool isAdmin = false}) async {
    final seq = ++_loadSeq;
    state = state.copyWith(
      isLoading: true,
      clearError: true,
      clearLoadError: true,
      clearSchedule: true,
      clearViolations: true,
      clearResult: true,
    );
    try {
      final results = await Future.wait<Object>([
        _ds.fetchSchedule(year, month),
        isAdmin ? _allUsers() : _directoryOrEmpty(),
      ]);
      final schedule = results[0] as MonthlySchedule;
      final violations = isAdmin ? await _violationsOrNull(schedule.id) : null;
      if (!mounted || seq != _loadSeq) return;
      state = state.copyWith(
        schedule: schedule,
        people: results[1] as List<UserDirectoryEntry>,
        violations: violations,
        isLoading: false,
      );
    } catch (e) {
      if (!mounted || seq != _loadSeq) return;
      state = state.copyWith(
        isLoading: false,
        clearSchedule: true,
        loadError: e,
        loadErrorStatus: e is ApiException ? e.statusCode : null,
      );
    }
  }

  /// Admin view: every account (pending/disabled too), reduced to code + role.
  Future<List<UserDirectoryEntry>> _allUsers() async => [
    for (final u in await _userDs.list())
      UserDirectoryEntry(id: u.id, code: u.code, role: u.role),
  ];

  /// Employee view: the directory only supplies column codes (rows fall back
  /// to "ID n"), so its failure must not hide the published roster.
  Future<List<UserDirectoryEntry>> _directoryOrEmpty() async {
    try {
      return await _userDs.directory();
    } catch (_) {
      return const [];
    }
  }

  /// The rule check is advisory: its failure must not hide the roster.
  Future<List<ConstraintViolation>?> _violationsOrNull(int scheduleId) async {
    try {
      return await _ds.fetchViolations(scheduleId);
    } catch (_) {
      return null;
    }
  }

  /// Re-checks the loaded month (admin, e.g. right before publishing).
  /// Returns the violations, or null when there is no schedule or the check
  /// failed.
  Future<List<ConstraintViolation>?> refreshViolations() async {
    final scheduleId = state.schedule?.id;
    if (scheduleId == null) return null;
    final violations = await _violationsOrNull(scheduleId);
    if (!mounted) return violations;
    if (state.schedule?.id == scheduleId) {
      state = violations == null
          ? state.copyWith(clearViolations: true)
          : state.copyWith(violations: violations);
    }
    return violations;
  }

  /// Rethrows the backend's 409 (month published or manually edited, needs
  /// [force]) so the page can confirm with the admin and retry; every other
  /// failure lands in [ScheduleState.error].
  Future<void> generate(int year, int month, {bool force = false}) async {
    state = state.copyWith(isMutating: true, clearError: true, clearResult: true);
    try {
      final result = await _ds.generate(year: year, month: month, force: force);
      if (!mounted) return;
      final generated = result.schedule;
      state = generated != null
          ? state.copyWith(
              isMutating: false,
              schedule: generated,
              lastResult: result,
              violations: result.violations,
              clearLoadError: true,
            )
          : state.copyWith(isMutating: false, lastResult: result);
    } catch (e) {
      if (!mounted) return;
      if (e is ApiException && e.statusCode == 409) {
        state = state.copyWith(isMutating: false);
        rethrow;
      }
      state = state.copyWith(isMutating: false, error: e);
    }
  }

  /// Admin cell edit (F-09). Returns the recheck warnings (empty = clean);
  /// null when the call failed (error is set on the state) or the loaded
  /// schedule is not [workDate]'s month. A response that arrives after the
  /// admin moved to another month is not written into that month's state.
  Future<List<String>?> overrideCell({
    required int userId,
    required DateTime workDate,
    required String code,
  }) async {
    if (!state.holds(workDate.year, workDate.month)) return null;
    final scheduleId = state.schedule!.id;
    state = state.copyWith(isMutating: true, clearError: true);
    try {
      final result = await _ds.override(
        scheduleId: scheduleId,
        userId: userId,
        workDate: workDate,
        code: code,
      );
      final warnings = result.violations.map((v) => v.message).toList();
      if (!mounted) return warnings;
      if (state.schedule?.id != scheduleId) {
        state = state.copyWith(isMutating: false);
        return warnings;
      }
      state = state.copyWith(
        isMutating: false,
        schedule: result.schedule ?? state.schedule,
      );
      await refreshViolations();
      return warnings;
    } catch (e) {
      if (!mounted) return null;
      state = state.copyWith(isMutating: false, error: e);
      return null;
    }
  }

  void clearResult() {
    state = state.copyWith(clearResult: true);
  }

  /// Publishes the loaded schedule only when it is [year]/[month], the month
  /// on screen (A3). True on success; false when that month has nothing to
  /// publish or the call failed (error set on the state).
  Future<bool> publish({required int year, required int month}) async {
    if (!state.holds(year, month)) return false;
    final scheduleId = state.schedule!.id;
    state = state.copyWith(isMutating: true, clearError: true);
    try {
      final updated = await _ds.publish(scheduleId);
      if (!mounted) return true;
      state = state.copyWith(isMutating: false, schedule: updated);
      return true;
    } catch (e) {
      if (!mounted) return false;
      state = state.copyWith(isMutating: false, error: e);
      return false;
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
