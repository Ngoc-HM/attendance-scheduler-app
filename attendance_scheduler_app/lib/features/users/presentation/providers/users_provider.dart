import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../auth/domain/entities/user.dart';
import '../../data/user_management_datasource.dart';

/// Holds the admin user list as an [AsyncValue] and exposes mutating actions
/// (create / approve / update) that refresh the list (F-01, F-03).
class UsersController extends StateNotifier<AsyncValue<List<User>>> {
  UsersController(this._ds) : super(const AsyncValue.loading()) {
    load();
  }

  final UserManagementDataSource _ds;

  Future<void> load() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() async => await _ds.list());
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

  Future<void> approve(int id) async {
    await _ds.approve(id);
    await load();
  }

  Future<void> setStatus(int id, String status) async {
    await _ds.update(id, {'status': status});
    await load();
  }

  Future<void> setRole(int id, UserRole role) async {
    await _ds.update(id, {'role': role.apiValue});
    await load();
  }
}

final usersControllerProvider =
    StateNotifierProvider<UsersController, AsyncValue<List<User>>>(
      (ref) => UsersController(ref.watch(userManagementDataSourceProvider)),
    );
