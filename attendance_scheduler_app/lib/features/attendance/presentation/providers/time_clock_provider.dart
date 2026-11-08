import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/datasources/time_clock_remote_datasource.dart';

class TimeClockState {
  const TimeClockState({
    this.today,
    this.monthEntries = const [],
    this.isLoading = false,
    this.isMutating = false,
    this.error,
  });

  final TimeClockEntry? today;
  final List<TimeClockEntry> monthEntries;
  final bool isLoading;
  final bool isMutating;

  /// The caught error of the last failed call; the page turns it into text
  /// with `apiErrorMessage` (backend detail, or a translated "server
  /// unavailable" / "server error"), never "ApiException(409): ...".
  final Object? error;

  bool get checkedIn => today?.checkInAt != null;
  bool get checkedOut => today?.checkOutAt != null;

  TimeClockState copyWith({
    TimeClockEntry? today,
    // `today` legitimately becomes null again after midnight — copyWith
    // needs an explicit clear flag or the stale entry sticks forever.
    bool clearToday = false,
    List<TimeClockEntry>? monthEntries,
    bool? isLoading,
    bool? isMutating,
    Object? error,
    bool clearError = false,
  }) =>
      TimeClockState(
        today: clearToday ? null : (today ?? this.today),
        monthEntries: monthEntries ?? this.monthEntries,
        isLoading: isLoading ?? this.isLoading,
        isMutating: isMutating ?? this.isMutating,
        error: clearError ? null : (error ?? this.error),
      );
}

class TimeClockController extends StateNotifier<TimeClockState> {
  TimeClockController(this._ds) : super(const TimeClockState());

  final TimeClockRemoteDataSource _ds;

  Future<void> load() async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final now = DateTime.now();
      final today = await _ds.today();
      if (!mounted) return;
      final entries = await _ds.month(now.year, now.month);
      if (!mounted) return;
      state = state.copyWith(
        isLoading: false,
        today: today,
        clearToday: today == null,
        monthEntries: entries.reversed.toList(), // newest first
      );
    } catch (e) {
      if (!mounted) return;
      state = state.copyWith(isLoading: false, error: e);
    }
  }

  Future<bool> checkIn() => _mutate(_ds.checkIn);

  Future<bool> checkOut() => _mutate(_ds.checkOut);

  Future<bool> _mutate(Future<TimeClockEntry> Function() action) async {
    state = state.copyWith(isMutating: true, clearError: true);
    try {
      await action();
      if (!mounted) return true;
      state = state.copyWith(isMutating: false);
      await load();
      return true;
    } catch (e) {
      if (!mounted) return false;
      state = state.copyWith(isMutating: false, error: e);
      return false;
    }
  }
}

final timeClockControllerProvider =
    StateNotifierProvider<TimeClockController, TimeClockState>(
  (ref) => TimeClockController(ref.watch(timeClockRemoteDataSourceProvider)),
);
