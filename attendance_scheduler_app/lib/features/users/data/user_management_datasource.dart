import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants/api_endpoints.dart';
import '../../../core/network/api_client.dart';
import '../../../core/network/api_exception.dart';
import '../../auth/data/models/user_model.dart';
import '../../auth/domain/entities/user.dart';

final userManagementDataSourceProvider = Provider<UserManagementDataSource>(
  (ref) => UserManagementDataSource(ref.watch(dioProvider)),
);

/// Backend response shape for `PATCH /users/{id}` — includes soft warnings.
class UserUpdateResult {
  const UserUpdateResult({required this.user, required this.warnings});

  final UserModel user;
  final List<String> warnings;

  factory UserUpdateResult.fromJson(Map<String, dynamic> json) =>
      UserUpdateResult(
        user: UserModel.fromJson(json['user'] as Map<String, dynamic>),
        warnings: (json['warnings'] as List<dynamic>? ?? const [])
            .map((e) => e.toString())
            .toList(),
      );
}

/// One row of `GET /users/directory`: an active user's confidential code and
/// role, deliberately without a name (people are shown by code).
class UserDirectoryEntry {
  const UserDirectoryEntry({
    required this.id,
    required this.code,
    required this.role,
  });

  final int id;
  final String code;
  final UserRole role;

  factory UserDirectoryEntry.fromJson(Map<String, dynamic> json) =>
      UserDirectoryEntry(
        id: json['id'] as int,
        code: json['code'] as String? ?? '',
        role: UserRoleX.fromApi(json['role'] as String? ?? 'T'),
      );
}

/// User-management calls (F-01, F-03). Every route except [directory] is
/// admin-guarded on the backend.
///
/// Every call throws [ApiException] (never a raw [DioException]) carrying the
/// HTTP status and the backend's `detail`, so the Users page can show the
/// real reason (last-admin lockout, username taken, not pending, quota out of
/// range) instead of a generic failure.
class UserManagementDataSource {
  UserManagementDataSource(this._dio);

  final Dio _dio;

  /// Runs [call], turning a [DioException] into an [ApiException]. pydantic's
  /// 422 `detail` is a list of `{loc, msg, ...}` objects; its `msg`s are
  /// joined instead of showing the raw list.
  Future<T> _guard<T>(Future<T> Function() call) async {
    try {
      return await call();
    } on DioException catch (e) {
      final detail = e.response?.data is Map
          ? (e.response!.data as Map)['detail']
          : null;
      if (detail is List) {
        final messages = [
          for (final item in detail)
            if (item is Map && item['msg'] != null) item['msg'].toString(),
        ];
        if (messages.isNotEmpty) {
          throw ApiException(
            messages.join('\n'),
            statusCode: e.response?.statusCode,
          );
        }
      }
      throw ApiException.fromDio(e);
    }
  }

  /// GET /users — list every account (admin only).
  Future<List<UserModel>> list() => _guard(() async {
    final response = await _dio.get(ApiEndpoints.users);
    return (response.data as List<dynamic>)
        .map((e) => UserModel.fromJson(e as Map<String, dynamic>))
        .toList();
  });

  /// GET /users/directory — active users' codes and roles, readable by any
  /// signed-in user.
  Future<List<UserDirectoryEntry>> directory() => _guard(() async {
    final response = await _dio.get(ApiEndpoints.usersDirectory);
    return (response.data as List<dynamic>)
        .map((e) => UserDirectoryEntry.fromJson(e as Map<String, dynamic>))
        .toList();
  });

  /// POST /users — admin creates an active account with a role and,
  /// optionally, an annual leave quota (omitted → the server default).
  Future<UserModel> create({
    required String username,
    required String fullName,
    required String password,
    required String role,
    int? annualLeaveQuota,
  }) => _guard(() async {
    final response = await _dio.post(
      ApiEndpoints.users,
      data: {
        'username': username,
        'full_name': fullName,
        'password': password,
        'role': role,
        'annual_leave_quota': ?annualLeaveQuota,
      },
    );
    return UserModel.fromJson(response.data as Map<String, dynamic>);
  });

  /// POST /auth/users/{id}/approve — activate a pending account with the
  /// role the admin assigns (F-03); the backend requires the role.
  Future<UserModel> approve(int id, {required String role}) => _guard(() async {
    final response = await _dio.post(
      ApiEndpoints.approveUser(id),
      data: {'role': role},
    );
    return UserModel.fromJson(response.data as Map<String, dynamic>);
  });

  /// PATCH /users/{id} — update role / status (and optionally other fields).
  /// Returns the wrapped result so the UI can surface soft warnings.
  Future<UserUpdateResult> update(int id, Map<String, dynamic> changes) =>
      _guard(() async {
        final response = await _dio.patch(
          ApiEndpoints.userById(id),
          data: changes,
        );
        return UserUpdateResult.fromJson(response.data as Map<String, dynamic>);
      });

  /// DELETE /users/{id} — hard-delete with history cascade. Throws on failure.
  Future<void> delete(int id) =>
      _guard(() => _dio.delete<void>(ApiEndpoints.userById(id)));
}
