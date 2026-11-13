import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/datasources/time_clock_remote_datasource.dart';

class StaffClockState {
  const StaffClockState({
    required this.month,
    this.entries = const [],
    this.isLoading = false,
    this.isSaving = false,
    this.error,
    this.now,
  });

  final DateTime month;

  /// The business clock when the list was loaded (null until then).
  final ClockNow? now;
  final List<StaffClockEntry> entries;
  final bool isLoading;
  final bool isSaving;

  /// The caught error of the last failed call (shown via `apiErrorMessage`).
  final Object? error;

  StaffClockState copyWith({
    DateTime? month,
    List<StaffClockEntry>? entries,
    bool? isLoading,
    bool? isSaving,
    Object? error,
    bool clearError = false,
    ClockNow? now,
  }) =>
      StaffClockState(
        now: now ?? this.now,
        month: month ?? this.month,
        entries: entries ?? this.entries,
        isLoading: isLoading ?? this.isLoading,
        isSaving: isSaving ?? this.isSaving,
        error: clearError ? null : (error ?? this.error),
      );
}

/// Admin: everyone's check-in/out of a month and corrections.
class StaffClockController extends StateNotifier<StaffClockState> {
  StaffClockController(this._ds, {DateTime? now, this.onChanged})
      : super(StaffClockState(
          month: DateTime((now ?? DateTime.now()).year,
              (now ?? DateTime.now()).month),
        ));

  final TimeClockRemoteDataSource _ds;

  /// Called after a correction, so views reading the punches reload.
  final void Function()? onChanged;

  Future<void> load() async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final now = await _ds.now();
      if (!mounted) return;
      final entries = await _ds.staffMonth(state.month.year, state.month.month);
      if (!mounted) return;
      state = state.copyWith(isLoading: false, entries: entries, now: now);
    } catch (e) {
      if (!mounted) return;
      state = state.copyWith(isLoading: false, error: e);
    }
  }

  Future<void> shiftMonth(int delta) {
    state = state.copyWith(
      month: DateTime(state.month.year, state.month.month + delta),
      entries: const [],
    );
    return load();
  }

  Future<bool> correct({
    required int userId,
    required DateTime workDate,
    required String checkIn,
    String? checkOut,
  }) async {
    state = state.copyWith(isSaving: true, clearError: true);
    try {
      await _ds.correct(
        userId: userId,
        workDate: workDate,
        checkIn: checkIn,
        checkOut: checkOut,
      );
      onChanged?.call();
      if (!mounted) return true;
      state = state.copyWith(isSaving: false);
      await load();
      return true;
    } catch (e) {
      if (!mounted) return false;
      state = state.copyWith(isSaving: false, error: e);
      return false;
    }
  }
}

final staffClockControllerProvider =
    StateNotifierProvider.autoDispose<StaffClockController, StaffClockState>(
  (ref) => StaffClockController(
    ref.watch(timeClockRemoteDataSourceProvider),
    onChanged: () => ref.invalidate(clockBoardProvider),
  ),
);
