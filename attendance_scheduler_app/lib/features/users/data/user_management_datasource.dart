import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants/api_endpoints.dart';
import '../../../core/network/api_client.dart';
import '../../auth/data/models/user_model.dart';

final userManagementDataSourceProvider = Provider<UserManagementDataSource>(
  (ref) => UserManagementDataSource(ref.watch(dioProvider)),
);

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

  /// POST /auth/users/{id}/approve — activate a pending account.
  Future<UserModel> approve(int id) async {
    final response = await _dio.post(ApiEndpoints.approveUser(id));
    return UserModel.fromJson(response.data as Map<String, dynamic>);
  }

  /// PATCH /users/{id} — update role / status (and optionally other fields).
  Future<UserModel> update(int id, Map<String, dynamic> changes) async {
    final response = await _dio.patch(ApiEndpoints.userById(id), data: changes);
    return UserModel.fromJson(response.data as Map<String, dynamic>);
  }
}
