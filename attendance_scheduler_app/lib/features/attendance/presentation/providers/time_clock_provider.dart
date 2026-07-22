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
  final String? error;

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
    String? error,
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
      final entries = await _ds.month(now.year, now.month);
      state = state.copyWith(
        isLoading: false,
        today: today,
        clearToday: today == null,
        monthEntries: entries.reversed.toList(), // newest first
      );
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<bool> checkIn() => _mutate(_ds.checkIn);

  Future<bool> checkOut() => _mutate(_ds.checkOut);

  Future<bool> _mutate(Future<TimeClockEntry> Function() action) async {
    state = state.copyWith(isMutating: true, clearError: true);
    try {
      await action();
      state = state.copyWith(isMutating: false);
      await load();
      return true;
    } catch (e) {
      state = state.copyWith(isMutating: false, error: e.toString());
      return false;
    }
  }
}

final timeClockControllerProvider =
    StateNotifierProvider<TimeClockController, TimeClockState>(
  (ref) => TimeClockController(ref.watch(timeClockRemoteDataSourceProvider)),
);
