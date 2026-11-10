import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/datasources/schedule_remote_datasource.dart';
import '../../data/datasources/self_arrange_remote_datasource.dart';
import '../../domain/entities/schedule_entities.dart';
import '../../domain/entities/self_arrange_entities.dart';

// ── Employee side ──────────────────────────────────────────────────────────────

class SelfArrangeState {
  const SelfArrangeState({
    this.myAssignments = const [],
    this.draft = const {},
    this.myRequests = const [],
    this.isLoading = false,
    this.isSubmitting = false,
    this.error,
    this.notPublished = false,
  });

  /// Own row of the published month, sorted by date.
  final List<ShiftAssignment> myAssignments;

  /// date → proposed code, only where it differs from the current cell.
  final Map<DateTime, String> draft;

  final List<SelfArrangeBatch> myRequests;
  final bool isLoading;
  final bool isSubmitting;

  /// The caught error of the last failed call, turned into text by the page
  /// with `apiErrorMessage` — never the exception's debug text.
  final Object? error;
  final bool notPublished;

  /// Effective code for a day after applying the draft.
  String? codeFor(DateTime date) {
    if (draft.containsKey(date)) return draft[date];
    for (final a in myAssignments) {
      if (a.workDate == date) return a.code;
    }
    return null;
  }

  /// 7-day blocks anchored at day 1 (mirrors `calendar_utils.build_weeks`):
  /// block index → (X count after draft, required target). Only genuine X
  /// counts — AL/S/CD are their own codes and never consume the quota.
  ///
  /// A full block needs exactly 2 X. The month's leftover days (29–31) have
  /// no quota (owner 2026-11-10): there the draft must only keep the number
  /// of X the plan already has, so the target is that number.
  Map<int, (int, int)> blockOffCounts() {
    if (myAssignments.isEmpty) return const {};
    final byBlock = <int, List<ShiftAssignment>>{};
    for (final a in myAssignments) {
      byBlock.putIfAbsent((a.workDate.day - 1) ~/ 7, () => []).add(a);
    }
    return byBlock.map((block, cells) {
      final target = cells.length >= 7
          ? 2
          : cells.where((a) => a.code == 'X').length;
      final got = cells.where((a) => codeFor(a.workDate) == 'X').length;
      return MapEntry(block, (got, target));
    });
  }

  bool get draftKeepsQuota =>
      blockOffCounts().values.every((c) => c.$1 == c.$2);

  SelfArrangeState copyWith({
    List<ShiftAssignment>? myAssignments,
    Map<DateTime, String>? draft,
    List<SelfArrangeBatch>? myRequests,
    bool? isLoading,
    bool? isSubmitting,
    Object? error,
    bool? notPublished,
    bool clearError = false,
  }) => SelfArrangeState(
    myAssignments: myAssignments ?? this.myAssignments,
    draft: draft ?? this.draft,
    myRequests: myRequests ?? this.myRequests,
    isLoading: isLoading ?? this.isLoading,
    isSubmitting: isSubmitting ?? this.isSubmitting,
    error: clearError ? null : (error ?? this.error),
    notPublished: notPublished ?? this.notPublished,
  );
}

class SelfArrangeController extends StateNotifier<SelfArrangeState> {
  SelfArrangeController(this._scheduleDs, this._ds)
    : super(const SelfArrangeState());

  final ScheduleRemoteDataSource _scheduleDs;
  final SelfArrangeRemoteDataSource _ds;

  /// Monotonic token: rapid month switches must not let an older response
  /// overwrite a newer one (stale-response race).
  int _loadSeq = 0;

  /// Load own row of the (published) month + own request history.
  Future<void> load(int year, int month, int userId) async {
    final seq = ++_loadSeq;
    state = state.copyWith(
      isLoading: true,
      clearError: true,
      draft: const {},
      notPublished: false,
    );
    try {
      final schedule = await _scheduleDs.fetchSchedule(year, month);
      final mine =
          schedule.assignments.where((a) => a.userId == userId).toList()
            ..sort((a, b) => a.workDate.compareTo(b.workDate));
      final requests = await _ds.list();
      if (!mounted || seq != _loadSeq) return; // disposed or superseded
      state = state.copyWith(
        isLoading: false,
        myAssignments: mine,
        myRequests: requests,
      );
    } catch (e) {
      // Unpublished (404) / beyond T+2 (403) → friendly empty state; the
      // request history is still loaded so the tab is never dead.
      if (!mounted) return;
      List<SelfArrangeBatch> requests = state.myRequests;
      try {
        requests = await _ds.list();
      } catch (_) {}
      if (!mounted || seq != _loadSeq) return; // disposed or superseded
      state = state.copyWith(
        isLoading: false,
        myAssignments: const [],
        myRequests: requests,
        notPublished: true,
        error: e,
      );
    }
  }

  /// Toggle an own X↔AD cell in the local draft (owner codes for T/F).
  void toggle(DateTime date) {
    ShiftAssignment? cell;
    for (final a in state.myAssignments) {
      if (a.workDate == date) cell = a;
    }
    if (cell == null) return;
    if (cell.code != 'X' && cell.code != 'AD') return; // AL/S/... untouchable
    final flipped = cell.code == 'X' ? 'AD' : 'X';
    final draft = Map<DateTime, String>.from(state.draft);
    if (draft.containsKey(date)) {
      draft.remove(date); // back to original
    } else {
      draft[date] = flipped;
    }
    state = state.copyWith(draft: draft);
  }

  void discardDraft() => state = state.copyWith(draft: const {});

  /// Submit the draft as one batch; returns true on success.
  Future<bool> submit(int year, int month, {String? note}) async {
    if (state.draft.isEmpty) return false;
    state = state.copyWith(isSubmitting: true, clearError: true);
    try {
      await _ds.create(
        year: year,
        month: month,
        changes: [
          for (final e in state.draft.entries)
            SelfArrangeChange(workDate: e.key, code: e.value),
        ],
        note: note,
      );
      if (!mounted) return true;
      final requests = await _ds.list();
      if (!mounted) return true;
      state = state.copyWith(
        isSubmitting: false,
        draft: const {},
        myRequests: requests,
      );
      return true;
    } catch (e) {
      if (!mounted) return false;
      state = state.copyWith(isSubmitting: false, error: e);
      return false;
    }
  }
}

final selfArrangeControllerProvider =
    StateNotifierProvider<SelfArrangeController, SelfArrangeState>(
      (ref) => SelfArrangeController(
        ref.watch(scheduleRemoteDataSourceProvider),
        ref.watch(selfArrangeRemoteDataSourceProvider),
      ),
    );

// ── Admin side (pending panel on the schedule page) ────────────────────────────

class SelfArrangeAdminState {
  const SelfArrangeAdminState({
    this.requests = const [],
    this.isLoading = false,
    this.isMutating = false,
    this.error,
  });

  final List<SelfArrangeBatch> requests;
  final bool isLoading;
  final bool isMutating;

  /// The caught error of the last failed call (see [SelfArrangeState.error]).
  final Object? error;

  SelfArrangeAdminState copyWith({
    List<SelfArrangeBatch>? requests,
    bool? isLoading,
    bool? isMutating,
    Object? error,
    bool clearError = false,
  }) => SelfArrangeAdminState(
    requests: requests ?? this.requests,
    isLoading: isLoading ?? this.isLoading,
    isMutating: isMutating ?? this.isMutating,
    error: clearError ? null : (error ?? this.error),
  );
}

class SelfArrangeAdminController extends StateNotifier<SelfArrangeAdminState> {
  SelfArrangeAdminController(this._ds) : super(const SelfArrangeAdminState());

  final SelfArrangeRemoteDataSource _ds;

  Future<void> load() async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final requests = await _ds.list(all: true);
      if (!mounted) return;
      state = state.copyWith(isLoading: false, requests: requests);
    } catch (e) {
      if (!mounted) return;
      state = state.copyWith(isLoading: false, error: e);
    }
  }

  /// Returns the decided batch (carrying recheck warnings) or null on failure.
  Future<SelfArrangeBatch?> decide(int id, String status) async {
    state = state.copyWith(isMutating: true, clearError: true);
    try {
      final updated = await _ds.decide(id: id, status: status);
      if (!mounted) return updated;
      state = state.copyWith(
        isMutating: false,
        requests: [
          for (final r in state.requests)
            if (r.id == id) updated else r,
        ],
      );
      return updated;
    } catch (e) {
      if (!mounted) return null;
      state = state.copyWith(isMutating: false, error: e);
      return null;
    }
  }
}

final selfArrangeAdminControllerProvider =
    StateNotifierProvider<SelfArrangeAdminController, SelfArrangeAdminState>(
      (ref) => SelfArrangeAdminController(
        ref.watch(selfArrangeRemoteDataSourceProvider),
      ),
    );
