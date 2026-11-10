import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../auth/presentation/providers/auth_provider.dart';
import '../../data/pending_counts_datasource.dart';

/// The admin's navigation badge numbers (owner 2026-11-10). `null` means "no
/// badges": not an admin, not loaded yet, or the last load failed — a number
/// is only shown while it comes from the latest successful load.
class PendingCountsController extends StateNotifier<PendingCounts?> {
  PendingCountsController(this._ds, this._isAdmin) : super(null);

  final PendingCountsDataSource _ds;
  final bool Function() _isAdmin;

  /// Bumped by every [refresh]; an older, slower answer is dropped.
  int _seq = 0;

  /// Reloads the counts. Employees never call the endpoint. A failure clears
  /// the badges silently: they are a hint, never worth an error toast.
  Future<void> refresh() async {
    if (!mounted) return;
    final seq = ++_seq;
    if (!_isAdmin()) {
      state = null;
      return;
    }
    PendingCounts? counts;
    try {
      counts = await _ds.fetch();
    } catch (_) {
      counts = null;
    }
    if (!mounted || seq != _seq) return;
    state = counts;
  }
}

final pendingCountsProvider =
    StateNotifierProvider<PendingCountsController, PendingCounts?>(
      (ref) => PendingCountsController(
        ref.watch(pendingCountsDataSourceProvider),
        () => ref.read(authControllerProvider).user?.isAdmin ?? false,
      ),
    );

/// For controllers that decide a pending item: refresh the badges so the
/// number drops right after the decision. Safe from a disposed controller.
void refreshPendingCounts(Ref ref) {
  ref.container.read(pendingCountsProvider.notifier).refresh();
}
