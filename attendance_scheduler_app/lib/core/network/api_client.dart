import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../i18n/locale_provider.dart';
import '../config/app_config.dart';
import '../storage/token_storage.dart';

/// Shared Dio instance, configured with the base URL, a bearer-token
/// interceptor, and the current UI language (so backend error messages come
/// back in the same language the user reads the app in).
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
  dio.interceptors.add(_LocaleInterceptor(
    () => ref.read(localeControllerProvider).languageCode,
  ));
  return dio;
});

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
