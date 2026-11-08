import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../i18n/locale_provider.dart';
import '../config/app_config.dart';
import '../constants/api_endpoints.dart';
import '../storage/token_storage.dart';

/// Monotonic counter bumped every time the backend rejects the bearer token
/// (401 on any request other than login — the JWT is invalid or expired, they
/// live 24h). `AuthController` listens to it and drops the session.
///
/// It lives here, not on the auth controller, so that [dioProvider] never
/// depends on `authControllerProvider` — which itself depends on Dio.
class SessionExpiredSignal extends StateNotifier<int> {
  SessionExpiredSignal() : super(0);

  void fire() => state = state + 1;
}

final sessionExpiredSignalProvider =
    StateNotifierProvider<SessionExpiredSignal, int>(
      (ref) => SessionExpiredSignal(),
    );

/// Monotonic counter bumped on every 403 outside login and `GET /users/me`.
/// A 403 is either a plain permission refusal or an account an admin disabled
/// mid-session; the backend's `detail` is translated text, so `AuthController`
/// tells them apart by re-reading `/users/me` (403 there → inactive → the
/// session ends). Same acyclic set-up as [SessionExpiredSignal].
class ForbiddenSignal extends StateNotifier<int> {
  ForbiddenSignal() : super(0);

  void fire() => state = state + 1;
}

final forbiddenSignalProvider = StateNotifierProvider<ForbiddenSignal, int>(
  (ref) => ForbiddenSignal(),
);

/// Shared Dio instance, configured with the base URL, a bearer-token
/// interceptor, the current UI language (so backend error messages come
/// back in the same language the user reads the app in) and a 401/403
/// watcher that ends the session when the token or the account is no longer
/// accepted.
final dioProvider = Provider<Dio>((ref) {
  final dio = Dio(
    BaseOptions(
      baseUrl: AppConfig.apiBaseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 30),
    ),
  );
  dio.interceptors.add(_AuthInterceptor(ref.read(tokenStorageProvider)));
  // Read lazily per request: language switches must not rebuild Dio.
  dio.interceptors.add(
    _LocaleInterceptor(() => ref.read(localeControllerProvider).languageCode),
  );
  // Read lazily inside the callbacks: keeps Dio free of any auth dependency.
  dio.interceptors.add(
    _SessionInterceptor(
      onUnauthorized: () =>
          ref.read(sessionExpiredSignalProvider.notifier).fire(),
      onForbidden: () => ref.read(forbiddenSignalProvider.notifier).fire(),
    ),
  );
  return dio;
});

/// Fires [_onUnauthorized] on every 401 except the login call itself (a 401
/// there means wrong credentials, handled by `AuthController.login`), and
/// [_onForbidden] on every 403 except login and `GET /users/me` (that call is
/// the inactive-account check itself; its callers handle the 403). The error
/// is always passed on so datasources still surface their `ApiException`.
class _SessionInterceptor extends Interceptor {
  _SessionInterceptor({
    required this._onUnauthorized,
    required this._onForbidden,
  });

  final void Function() _onUnauthorized;
  final void Function() _onForbidden;

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    final path = err.requestOptions.uri.path;
    final isLogin = path.endsWith(ApiEndpoints.login);
    final isMe = path.endsWith(ApiEndpoints.me);
    final status = err.response?.statusCode;
    if (status == 401 && !isLogin) _onUnauthorized();
    if (status == 403 && !isLogin && !isMe) _onForbidden();
    handler.next(err);
  }
}

class _LocaleInterceptor extends Interceptor {
  _LocaleInterceptor(this._languageCode);

  final String Function() _languageCode;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    options.headers['Accept-Language'] = _languageCode();
    handler.next(options);
  }
}

class _AuthInterceptor extends Interceptor {
  _AuthInterceptor(this._tokenStorage);

  final TokenStorage _tokenStorage;

  @override
  void onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await _tokenStorage.read();
    if (token != null && token.isNotEmpty) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }
}
