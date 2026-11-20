import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/datasources/schedule_remote_datasource.dart';
import '../../domain/entities/schedule_entities.dart';

class ShiftChangeState {
  const ShiftChangeState({
    this.requests = const [],
    this.incoming = const [],
    this.isLoading = false,
    this.isMutating = false,
    this.error,
    this.loadFailed = false,
  });

  final List<ShiftChangeRequest> requests;

  /// Swaps a colleague asked the signed-in person into, still waiting for
  /// their answer (employee view only).
  final List<ShiftChangeRequest> incoming;
  final bool isLoading;
  final bool isMutating;

  /// The caught error of the last failed call; the page turns it into text
  /// with `apiErrorMessage` (backend detail, or a translated "server
  /// unavailable" / "server error"), never the exception's debug text.
  final Object? error;

  /// The last [ShiftChangeController.load] failed, so [requests] is not
  /// trustworthy (as opposed to [error] from a failed submit or answer).
  final bool loadFailed;

  ShiftChangeState copyWith({
    List<ShiftChangeRequest>? requests,
    List<ShiftChangeRequest>? incoming,
    bool? isLoading,
    bool? isMutating,
    Object? error,
    bool? loadFailed,
    bool clearError = false,
  }) => ShiftChangeState(
    requests: requests ?? this.requests,
    incoming: incoming ?? this.incoming,
    isLoading: isLoading ?? this.isLoading,
    isMutating: isMutating ?? this.isMutating,
    error: clearError ? null : (error ?? this.error),
    loadFailed: loadFailed ?? this.loadFailed,
  );
}

/// The signed-in employee's shift changes on the Schedule page: their own
/// requests and the swaps waiting for their answer. The admin decides
/// requests on the Approvals screen (owner 2026-11-20), through the leaves
/// controller.
class ShiftChangeController extends StateNotifier<ShiftChangeState> {
  ShiftChangeController(this._ds) : super(const ShiftChangeState());

  final ScheduleRemoteDataSource _ds;

  /// Own requests, then the swaps waiting for an answer ([loadIncoming]).
  Future<void> load() async {
    state = state.copyWith(
      isLoading: true,
      loadFailed: false,
      clearError: true,
    );
    try {
      final requests = await _ds.fetchShiftChanges();
      if (!mounted) return;
      state = state.copyWith(isLoading: false, requests: requests);
    } catch (e) {
      if (!mounted) return;
      state = state.copyWith(isLoading: false, loadFailed: true, error: e);
    }
    await loadIncoming();
  }

  /// Swaps waiting for the signed-in person's answer. The panel shows only
  /// when there is one, so a failed load keeps the last list silently.
  Future<void> loadIncoming() async {
    try {
      final incoming = await _ds.fetchIncomingShiftChanges();
      if (mounted) state = state.copyWith(incoming: incoming);
    } catch (_) {}
  }

  /// The swap partner's answer to request [id]; false when the call failed
  /// (error is set). The answered row leaves [ShiftChangeState.incoming].
  Future<bool> respond(int id, {required bool accept}) async {
    state = state.copyWith(isMutating: true, clearError: true);
    try {
      await _ds.respondToShiftChange(id: id, accept: accept);
      if (!mounted) return true;
      state = state.copyWith(
        isMutating: false,
        incoming: [
          for (final r in state.incoming)
            if (r.id != id) r,
        ],
      );
      await loadIncoming();
      return true;
    } catch (e) {
      if (!mounted) return false;
      state = state.copyWith(isMutating: false, error: e);
      return false;
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
}

final shiftChangeControllerProvider =
    StateNotifierProvider<ShiftChangeController, ShiftChangeState>(
      (ref) => ShiftChangeController(
        ref.watch(scheduleRemoteDataSourceProvider),
      ),
    );
