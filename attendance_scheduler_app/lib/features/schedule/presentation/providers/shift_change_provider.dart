import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/datasources/schedule_remote_datasource.dart';
import '../../domain/entities/schedule_entities.dart';

class ShiftChangeState {
  const ShiftChangeState({
    this.requests = const [],
    this.isLoading = false,
    this.isMutating = false,
    this.error,
    this.loadFailed = false,
  });

  final List<ShiftChangeRequest> requests;
  final bool isLoading;
  final bool isMutating;

  /// The caught error of the last failed call; the page turns it into text
  /// with `apiErrorMessage` (backend detail, or a translated "server
  /// unavailable" / "server error"), never the exception's debug text.
  final Object? error;

  /// The last [ShiftChangeController.load] failed, so [requests] is not
  /// trustworthy (as opposed to [error] from a failed submit or decide).
  final bool loadFailed;

  ShiftChangeState copyWith({
    List<ShiftChangeRequest>? requests,
    bool? isLoading,
    bool? isMutating,
    Object? error,
    bool? loadFailed,
    bool clearError = false,
  }) =>
      ShiftChangeState(
        requests: requests ?? this.requests,
        isLoading: isLoading ?? this.isLoading,
        isMutating: isMutating ?? this.isMutating,
        error: clearError ? null : (error ?? this.error),
        loadFailed: loadFailed ?? this.loadFailed,
      );
}

class ShiftChangeController extends StateNotifier<ShiftChangeState> {
  ShiftChangeController(this._ds) : super(const ShiftChangeState());

  final ScheduleRemoteDataSource _ds;

  Future<void> load({bool all = false}) async {
    state = state.copyWith(
      isLoading: true,
      loadFailed: false,
      clearError: true,
    );
    try {
      final requests = await _ds.fetchShiftChanges(all: all);
      if (!mounted) return;
      state = state.copyWith(isLoading: false, requests: requests);
    } catch (e) {
      if (!mounted) return;
      state = state.copyWith(isLoading: false, loadFailed: true, error: e);
    }
  }

  Future<bool> submit({
    required DateTime workDate,
    required String kind,
    String? requestedCode,
    int? counterpartUserId,
    String? note,
  }) async {
    state = state.copyWith(isMutating: true, clearError: true);
    try {
      await _ds.createShiftChange(
        workDate: workDate,
        kind: kind,
        requestedCode: requestedCode,
        counterpartUserId: counterpartUserId,
        note: note,
      );
      if (!mounted) return true;
      state = state.copyWith(isMutating: false);
      return true;
    } catch (e) {
      if (!mounted) return false;
      state = state.copyWith(isMutating: false, error: e);
      return false;
    }
  }

  /// Returns the decided request, whose `warnings` carry the backend's rule
  /// recheck after an approval; null when the call failed (error is set).
  Future<ShiftChangeRequest?> decide(int id, String status) async {
    state = state.copyWith(isMutating: true, clearError: true);
    try {
      final updated = await _ds.decideShiftChange(id: id, status: status);
      if (!mounted) return updated;
      final newList = [
        for (final r in state.requests)
          if (r.id == id) updated else r,
      ];
      state = state.copyWith(isMutating: false, requests: newList);
      return updated;
    } catch (e) {
      if (!mounted) return null;
      state = state.copyWith(isMutating: false, error: e);
      return null;
    }
  }
}

final shiftChangeControllerProvider =
    StateNotifierProvider<ShiftChangeController, ShiftChangeState>(
  (ref) => ShiftChangeController(ref.watch(scheduleRemoteDataSourceProvider)),
);
