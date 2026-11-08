import 'package:flutter_dotenv/flutter_dotenv.dart';

/// Runtime configuration.
///
/// The API base URL is resolved in this order:
///   1. `--dart-define=API_BASE_URL=...` compile-time value, when non-empty —
///      a release build pointed at a real server must not be overridden by
///      the bundled `.env`, which ships with the local-dev URL.
///   2. `API_BASE_URL` from the bundled `.env` file (loaded in `main`).
///   3. The local-dev default (backend on port 8035).
class AppConfig {
  const AppConfig._();

  /// Backend started by `make dev`.
  static const String localDevBaseUrl = 'http://localhost:8035/api/v1';

  static const String _dartDefine = String.fromEnvironment('API_BASE_URL');

  static String get apiBaseUrl {
    // `isInitialized` guards the case where `.env` was never loaded (e.g. in
    // widget tests), so this getter never throws.
    final fromEnv = dotenv.isInitialized
        ? dotenv.maybeGet('API_BASE_URL')
        : null;
    return resolveApiBaseUrl(dartDefine: _dartDefine, bundledEnv: fromEnv);
  }

  /// Pure resolution rule behind [apiBaseUrl]; blank values count as unset.
  static String resolveApiBaseUrl({
    required String dartDefine,
    required String? bundledEnv,
  }) {
    final define = dartDefine.trim();
    if (define.isNotEmpty) return define;
    final env = bundledEnv?.trim() ?? '';
    if (env.isNotEmpty) return env;
    return localDevBaseUrl;
  }
}
