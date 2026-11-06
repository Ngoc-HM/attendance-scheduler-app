import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../auth/domain/entities/user.dart';
import '../../data/user_management_datasource.dart';

/// Holds the admin user list as an [AsyncValue] and exposes mutating actions
/// (create / approve / update / delete) that refresh the list (F-01, F-03).
class UsersController extends StateNotifier<AsyncValue<List<User>>> {
  UsersController(this._ds) : super(const AsyncValue.loading()) {
    load();
  }

  final UserManagementDataSource _ds;

  Future<void> load() async {
    // Guard against the autoDispose lifecycle: navigating away (or the page
    // transition tearing down) can dispose this notifier mid-flight, so never
    // touch `state` once unmounted.
    if (!mounted) return;
    state = const AsyncValue.loading();
    final result = await AsyncValue.guard(() async => await _ds.list());
    if (mounted) state = result;
  }

  Future<void> create({
    required String username,
    required String fullName,
    required String password,
    required UserRole role,
  }) async {
    await _ds.create(
      username: username,
      fullName: fullName,
      password: password,
      role: role.apiValue,
    );
    await load();
  }

  /// Activates a pending account with the role the admin picked (F-03).
  Future<void> approve(int id, UserRole role) async {
    await _ds.approve(id, role: role.apiValue);
    await load();
  }

  /// Returns any soft warnings returned by the backend (e.g. fixed team would
  /// become empty). Throws on hard errors (including last-admin lockout).
  Future<List<String>> setStatus(int id, String status) async {
    final result = await _ds.update(id, {'status': status});
    await load();
    return result.warnings;
  }

  /// Returns any soft warnings. Throws on hard errors.
  Future<List<String>> setRole(int id, UserRole role) async {
    final result = await _ds.update(id, {'role': role.apiValue});
    await load();
    return result.warnings;
  }

  /// Hard delete with cascade (CSV TC-007). Throws on hard errors.
  Future<void> delete(int id) async {
    await _ds.delete(id);
    await load();
  }
}

/// `autoDispose` so the list reloads from the backend every time the Users
/// page is opened — otherwise newly self-registered (pending) accounts stay
/// hidden behind a stale cached list until a manual refresh (F-01).
final usersControllerProvider =
    StateNotifierProvider.autoDispose<UsersController, AsyncValue<List<User>>>(
      (ref) => UsersController(ref.watch(userManagementDataSourceProvider)),
    );
