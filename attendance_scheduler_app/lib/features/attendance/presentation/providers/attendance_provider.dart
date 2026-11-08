import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../users/data/user_management_datasource.dart';
import '../../../auth/domain/entities/user.dart';
import '../../data/datasources/attendance_remote_datasource.dart';
import '../../data/datasources/calculations_remote_datasource.dart';
import '../../domain/entities/attendance_entities.dart';
import '../../domain/entities/calculations_entities.dart';

class AttendanceState {
  const AttendanceState({
    this.records = const [],
    this.users = const [],
    this.holidays = const [],
    this.isLoading = false,
    this.isMutating = false,
    this.error,
    this.lastSickCover,
  });

  final List<AttendanceRecord> records;
  final List<User> users; // id→name/role map (admin only)
  final List<Holiday> holidays;
  final bool isLoading;
  final bool isMutating;

  /// The caught error of the last failed call; the page and dialogs turn it
  /// into text with `apiErrorMessage` (backend detail, or a translated
  /// "server unavailable" / "server error"), never "ApiException(409): ...".
  final Object? error;
  final SickCoverResult? lastSickCover;

  AttendanceState copyWith({
    List<AttendanceRecord>? records,
    List<User>? users,
    List<Holiday>? holidays,
    bool? isLoading,
    bool? isMutating,
    Object? error,
    SickCoverResult? lastSickCover,
    bool clearError = false,
    bool clearSickCover = false,
  }) =>
      AttendanceState(
        records: records ?? this.records,
        users: users ?? this.users,
        holidays: holidays ?? this.holidays,
        isLoading: isLoading ?? this.isLoading,
        isMutating: isMutating ?? this.isMutating,
        error: clearError ? null : (error ?? this.error),
        lastSickCover:
            clearSickCover ? null : (lastSickCover ?? this.lastSickCover),
      );
}

/// Every mutation re-checks `mounted` after its await: logout invalidates
/// this provider, possibly while a request is in flight.
class AttendanceController extends StateNotifier<AttendanceState> {
  AttendanceController(this._ds, this._userDs, this._calculationsDs)
      : super(const AttendanceState());

  final AttendanceRemoteDataSource _ds;
  final UserManagementDataSource _userDs;
  final CalculationsRemoteDataSource _calculationsDs;

  Future<void> load(int year, int month, {bool isAdmin = false}) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final futures = <Future>[
        isAdmin
            ? _ds.fetchAll(year: year, month: month)
            : _ds.fetchMine(year: year, month: month),
        _ds.fetchHolidays(year),
        if (isAdmin) _userDs.list(),
      ];
      final results = await Future.wait(futures);
      if (!mounted) return;
      final records = results[0] as List<AttendanceRecord>;
      final holidays = results[1] as List<Holiday>;
      final users = (isAdmin && results.length > 2)
          ? results[2] as List<User>
          : <User>[];

      state = state.copyWith(
        records: records,
        holidays: holidays,
        users: users,
        isLoading: false,
      );
    } catch (e) {
      if (mounted) {
        state = state.copyWith(isLoading: false, error: e);
      }
    }
  }

  Future<bool> upsert({
    required int userId,
    required DateTime workDate,
    required String code,
    String? note,
  }) async {
    state = state.copyWith(isMutating: true, clearError: true);
    try {
      final updated = await _ds.upsert(
        userId: userId,
        workDate: workDate,
        code: code,
        note: note,
      );
      if (!mounted) return false;
      final newList = [
        for (final r in state.records)
          if (r.userId == userId &&
              r.workDate.year == workDate.year &&
              r.workDate.month == workDate.month &&
              r.workDate.day == workDate.day)
            updated
          else
            r,
        // add new if not already present
        if (!state.records.any((r) =>
            r.userId == userId &&
            r.workDate.year == workDate.year &&
            r.workDate.month == workDate.month &&
            r.workDate.day == workDate.day))
          updated,
      ];
      state = state.copyWith(isMutating: false, records: newList);
      return true;
    } catch (e) {
      if (mounted) {
        state = state.copyWith(isMutating: false, error: e);
      }
      return false;
    }
  }

  Future<bool> markSick({
    required int userId,
    required DateTime workDate,
    String? note,
  }) async {
    state = state.copyWith(
        isMutating: true, clearError: true, clearSickCover: true);
    try {
      final result = await _ds.sickCover(
        userId: userId,
        workDate: workDate,
        note: note,
      );
      if (!mounted) return false;
      // Refresh the records list to reflect the sick + cover entries.
      final updatedRecords = List<AttendanceRecord>.from(state.records);
      _upsertRecord(updatedRecords, result.sick);
      if (result.cover != null) _upsertRecord(updatedRecords, result.cover!);
      state = state.copyWith(
        isMutating: false,
        records: updatedRecords,
        lastSickCover: result,
      );
      return true;
    } catch (e) {
      if (mounted) {
        state = state.copyWith(isMutating: false, error: e);
      }
      return false;
    }
  }

  Future<bool> seed(int year, int month) async {
    state = state.copyWith(isMutating: true, clearError: true);
    try {
      await _ds.seed(year: year, month: month);
      if (!mounted) return false;
      // Reload to reflect seeded data.
      await load(year, month, isAdmin: true);
      return true;
    } catch (e) {
      if (mounted) {
        state = state.copyWith(isMutating: false, error: e);
      }
      return false;
    }
  }

  // ── Month close (F-14) ─────────────────────────────────────────────────────

  /// Admin: close [year]/[month] — the backend computes and stores each
  /// user's carry-over balances and returns them. Failures are rethrown (as
  /// `ApiException`) instead of going into [AttendanceState.error]: that field
  /// swaps the whole page for the error view, which must not happen because a
  /// one-shot action failed.
  Future<MonthCloseResult> closeMonth(int year, int month) async {
    state = state.copyWith(isMutating: true, clearError: true);
    try {
      return await _calculationsDs.closeMonth(year, month);
    } finally {
      if (mounted) state = state.copyWith(isMutating: false);
    }
  }

  // ── Holiday mutations ──────────────────────────────────────────────────────

  Future<bool> upsertHoliday({
    required DateTime day,
    required String name,
  }) async {
    state = state.copyWith(isMutating: true, clearError: true);
    try {
      final holiday = await _ds.upsertHoliday(day: day, name: name);
      if (!mounted) return false;
      final newList = [
        for (final h in state.holidays)
          if (h.day.year == day.year &&
              h.day.month == day.month &&
              h.day.day == day.day)
            holiday
          else
            h,
        if (!state.holidays.any((h) =>
            h.day.year == day.year &&
            h.day.month == day.month &&
            h.day.day == day.day))
          holiday,
      ];
      state = state.copyWith(isMutating: false, holidays: newList);
      return true;
    } catch (e) {
      if (mounted) {
        state = state.copyWith(isMutating: false, error: e);
      }
      return false;
    }
  }

  Future<bool> deleteHoliday(int id) async {
    state = state.copyWith(isMutating: true, clearError: true);
    try {
      await _ds.deleteHoliday(id);
      if (!mounted) return false;
      final newList =
          state.holidays.where((h) => h.id != id).toList();
      state = state.copyWith(isMutating: false, holidays: newList);
      return true;
    } catch (e) {
      if (mounted) {
        state = state.copyWith(isMutating: false, error: e);
      }
      return false;
    }
  }

  void clearSickCover() => state = state.copyWith(clearSickCover: true);

  // ── Private helpers ────────────────────────────────────────────────────────

  void _upsertRecord(List<AttendanceRecord> list, AttendanceRecord record) {
    final idx = list.indexWhere((r) =>
        r.userId == record.userId &&
        r.workDate.year == record.workDate.year &&
        r.workDate.month == record.workDate.month &&
        r.workDate.day == record.workDate.day);
    if (idx >= 0) {
      list[idx] = record;
    } else {
      list.add(record);
    }
  }
}

final attendanceControllerProvider =
    StateNotifierProvider<AttendanceController, AttendanceState>(
  (ref) => AttendanceController(
    ref.watch(attendanceRemoteDataSourceProvider),
    ref.watch(userManagementDataSourceProvider),
    ref.watch(calculationsRemoteDataSourceProvider),
  ),
);
