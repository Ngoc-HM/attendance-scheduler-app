import 'package:dio/dio.dart';

import '../../../../core/constants/api_endpoints.dart';
import '../models/user_model.dart';

/// Talks to the backend auth/user endpoints.
class AuthRemoteDataSource {
  AuthRemoteDataSource(this._dio);

  final Dio _dio;

  /// POST /auth/login — OAuth2 password form → returns the access token (F-02).
  Future<String> login(String username, String password) async {
    final response = await _dio.post(
      ApiEndpoints.login,
      data: {'username': username, 'password': password},
      options: Options(contentType: Headers.formUrlEncodedContentType),
    );
    return (response.data as Map<String, dynamic>)['access_token'] as String;
  }

  /// GET /users/me — current user profile.
  Future<UserModel> me() async {
    final response = await _dio.get(ApiEndpoints.me);
    return UserModel.fromJson(response.data as Map<String, dynamic>);
  }
}
