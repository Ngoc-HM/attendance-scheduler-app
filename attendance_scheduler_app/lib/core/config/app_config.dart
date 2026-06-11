import 'package:flutter_dotenv/flutter_dotenv.dart';

/// Runtime configuration.
///
/// The API base URL is resolved in this order:
///   1. `API_BASE_URL` from the bundled `.env` file (loaded in `main`).
///   2. `--dart-define=API_BASE_URL=...` compile-time value.
///   3. The local-dev default (backend on port 8035).
class AppConfig {
  const AppConfig._();

  static const String _dartDefine = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8035/api/v1',
  );

  static String get apiBaseUrl {
    // `isInitialized` guards the case where `.env` was never loaded (e.g. in
    // widget tests), so this getter never throws.
    final fromEnv = dotenv.isInitialized
        ? dotenv.maybeGet('API_BASE_URL')
        : null;
    return (fromEnv != null && fromEnv.isNotEmpty) ? fromEnv : _dartDefine;
  }
}
