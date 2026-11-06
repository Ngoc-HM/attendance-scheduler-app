// Session restore on app start (C6): a stored, still-valid token signs the
// user straight back in; a rejected one is wiped so the login page shows.

import 'package:attendance_scheduler_app/core/storage/locale_storage.dart';
import 'package:attendance_scheduler_app/core/storage/token_storage.dart';
import 'package:attendance_scheduler_app/features/auth/data/datasources/auth_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/auth/data/models/user_model.dart';
import 'package:attendance_scheduler_app/features/auth/data/repositories/auth_repository_impl.dart';
import 'package:attendance_scheduler_app/features/auth/domain/entities/user.dart';
import 'package:attendance_scheduler_app/features/auth/presentation/providers/auth_provider.dart';
import 'package:attendance_scheduler_app/i18n/locale_provider.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

class _MemoryTokenStorage extends TokenStorage {
  _MemoryTokenStorage([this.token]);

  String? token;

  @override
  Future<void> save(String value) async => token = value;

  @override
  Future<String?> read() async => token;

  @override
  Future<void> clear() async => token = null;
}

class _MemoryLocaleStorage extends LocaleStorage {
  final Map<int, String> values = {};

  @override
  Future<String?> read(int userId) async => values[userId];

  @override
  Future<void> write(int userId, String languageCode) async {
    values[userId] = languageCode;
  }
}

/// Stands in for `GET /users/me`: answers with [user], or throws [error].
class _FakeAuthRemote implements AuthRemoteDataSource {
  _FakeAuthRemote({this.user, this.error});

  final UserModel? user;
  final Object? error;
  int meCalls = 0;

  @override
  Future<UserModel> me() async {
    meCalls++;
    if (error != null) throw error!;
    return user!;
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

const _employee = UserModel(
  id: 7,
  username: 'anna',
  fullName: 'Anna',
  role: UserRole.t,
  status: 'active',
  code: 'T3',
  carryComp: 2,
);

DioException _unauthorized() {
  final request = RequestOptions(path: '/users/me');
  return DioException(
    requestOptions: request,
    response: Response(requestOptions: request, statusCode: 401),
    type: DioExceptionType.badResponse,
  );
}

({AuthController controller, LocaleController locale}) _build(
  _FakeAuthRemote remote,
  _MemoryTokenStorage tokens,
  _MemoryLocaleStorage locales,
) {
  final locale = LocaleController(locales);
  final controller = AuthController(
    AuthRepositoryImpl(remote, tokens),
    locale,
    tokenStorage: tokens,
  );
  return (controller: controller, locale: locale);
}

void main() {
  test('restoreSession signs in from a stored token', () async {
    final tokens = _MemoryTokenStorage('stored-jwt');
    final locales = _MemoryLocaleStorage()..values[7] = 'vi';
    final remote = _FakeAuthRemote(user: _employee);
    final (:controller, :locale) = _build(remote, tokens, locales);

    await controller.restoreSession();

    expect(controller.state.user, _employee);
    expect(controller.state.error, isNull);
    expect(tokens.token, 'stored-jwt');
    // The restored user gets their own saved language, as after a login.
    expect(locale.state.languageCode, 'vi');
  });

  test('restoreSession clears a rejected token', () async {
    final tokens = _MemoryTokenStorage('expired-jwt');
    final remote = _FakeAuthRemote(error: _unauthorized());
    final (:controller, locale: _) =
        _build(remote, tokens, _MemoryLocaleStorage());

    await controller.restoreSession();

    expect(controller.state.user, isNull);
    expect(controller.state.isAuthenticated, isFalse);
    expect(controller.state.error, isNull);
    expect(tokens.token, isNull);
  });

  test('restoreSession keeps the token when the server is unreachable', () async {
    final tokens = _MemoryTokenStorage('stored-jwt');
    final remote = _FakeAuthRemote(
      error: DioException(
        requestOptions: RequestOptions(path: '/users/me'),
        type: DioExceptionType.connectionError,
      ),
    );
    final (:controller, locale: _) =
        _build(remote, tokens, _MemoryLocaleStorage());

    await controller.restoreSession();

    expect(controller.state.user, isNull);
    // The login page explains the failure; the next start can retry.
    expect(controller.state.error, 'server_unavailable');
    expect(tokens.token, 'stored-jwt');
  });

  test('restoreSession without a stored token never calls the API', () async {
    final tokens = _MemoryTokenStorage();
    final remote = _FakeAuthRemote(user: _employee);
    final (:controller, locale: _) =
        _build(remote, tokens, _MemoryLocaleStorage());

    await controller.restoreSession();

    expect(controller.state.user, isNull);
    expect(remote.meCalls, 0);
  });

  test('UserModel reads carry_comp from /users/me', () {
    final user = UserModel.fromJson({
      'id': 7,
      'username': 'anna',
      'full_name': 'Anna',
      'role': 'T',
      'status': 'active',
      'code': 'T3',
      'carry_comp': 4,
      'carry_streak': 1,
    });

    expect(user.carryComp, 4);
  });
}
