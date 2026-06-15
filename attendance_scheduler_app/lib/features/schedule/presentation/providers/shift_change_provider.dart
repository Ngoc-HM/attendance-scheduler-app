import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/datasources/schedule_remote_datasource.dart';
import '../../domain/entities/schedule_entities.dart';

class ShiftChangeState {
  const ShiftChangeState({
    this.requests = const [],
    this.isLoading = false,
    this.isMutating = false,
    this.error,
  });

  final List<ShiftChangeRequest> requests;
  final bool isLoading;
  final bool isMutating;
  final String? error;

  ShiftChangeState copyWith({
    List<ShiftChangeRequest>? requests,
    bool? isLoading,
    bool? isMutating,
    String? error,
    bool clearError = false,
  }) =>
      ShiftChangeState(
        requests: requests ?? this.requests,
        isLoading: isLoading ?? this.isLoading,
        isMutating: isMutating ?? this.isMutating,
        error: clearError ? null : (error ?? this.error),
      );
}

class ShiftChangeController extends StateNotifier<ShiftChangeState> {
  ShiftChangeController(this._ds) : super(const ShiftChangeState());

  final ScheduleRemoteDataSource _ds;

  Future<void> load({bool all = false}) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final requests = await _ds.fetchShiftChanges(all: all);
      state = state.copyWith(isLoading: false, requests: requests);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
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
      state = state.copyWith(isMutating: false);
      return true;
    } catch (e) {
      state = state.copyWith(isMutating: false, error: e.toString());
      return false;
    }
  }

  Future<bool> decide(int id, String status) async {
    state = state.copyWith(isMutating: true, clearError: true);
    try {
      final updated = await _ds.decideShiftChange(id: id, status: status);
      final newList = [
        for (final r in state.requests)
          if (r.id == id) updated else r,
      ];
      state = state.copyWith(isMutating: false, requests: newList);
      return true;
    } catch (e) {
      state = state.copyWith(isMutating: false, error: e.toString());
      return false;
    }
  }
}

final shiftChangeControllerProvider =
    StateNotifierProvider<ShiftChangeController, ShiftChangeState>(
  (ref) => ShiftChangeController(ref.watch(scheduleRemoteDataSourceProvider)),
);
