import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants/api_endpoints.dart';
import '../../../core/network/api_client.dart';
import '../../auth/data/models/user_model.dart';

final userManagementDataSourceProvider = Provider<UserManagementDataSource>(
  (ref) => UserManagementDataSource(ref.watch(dioProvider)),
);

/// Backend response shape for `PATCH /users/{id}` — includes soft warnings.
class UserUpdateResult {
  const UserUpdateResult({required this.user, required this.warnings});

  final UserModel user;
  final List<String> warnings;

  factory UserUpdateResult.fromJson(Map<String, dynamic> json) => UserUpdateResult(
    user: UserModel.fromJson(json['user'] as Map<String, dynamic>),
    warnings: (json['warnings'] as List<dynamic>? ?? const [])
        .map((e) => e.toString())
        .toList(),
  );
}

/// Admin user-management calls (F-01, F-03). All routes are admin-guarded
/// on the backend.
class UserManagementDataSource {
  UserManagementDataSource(this._dio);

  final Dio _dio;

  /// GET /users — list every account.
  Future<List<UserModel>> list() async {
    final response = await _dio.get(ApiEndpoints.users);
    return (response.data as List<dynamic>)
        .map((e) => UserModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// POST /users — admin creates an active account with a role.
  Future<UserModel> create({
    required String username,
    required String fullName,
    required String password,
    required String role,
  }) async {
    final response = await _dio.post(
      ApiEndpoints.users,
      data: {
        'username': username,
        'full_name': fullName,
        'password': password,
        'role': role,
      },
    );
    return UserModel.fromJson(response.data as Map<String, dynamic>);
  }

  /// POST /auth/users/{id}/approve — activate a pending account with the
  /// role the admin assigns (F-03); the backend requires the role.
  Future<UserModel> approve(int id, {required String role}) async {
    final response = await _dio.post(
      ApiEndpoints.approveUser(id),
      data: {'role': role},
    );
    return UserModel.fromJson(response.data as Map<String, dynamic>);
  }

  /// PATCH /users/{id} — update role / status (and optionally other fields).
  /// Returns the wrapped result so the UI can surface soft warnings.
  Future<UserUpdateResult> update(int id, Map<String, dynamic> changes) async {
    final response = await _dio.patch(ApiEndpoints.userById(id), data: changes);
    return UserUpdateResult.fromJson(response.data as Map<String, dynamic>);
  }

  /// DELETE /users/{id} — hard-delete with history cascade. Throws on failure.
  Future<void> delete(int id) async {
    await _dio.delete(ApiEndpoints.userById(id));
  }
}
