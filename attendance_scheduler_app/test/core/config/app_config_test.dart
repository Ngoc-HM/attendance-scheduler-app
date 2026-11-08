// API base URL resolution (review 2026-11-08 D6): a release built with
// `--dart-define=API_BASE_URL=...` must reach that server even though the
// bundled `.env` still says localhost.

import 'package:attendance_scheduler_app/core/config/app_config.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  const prod = 'https://api.example.eu/api/v1';
  const bundled = 'http://localhost:8035/api/v1';

  test('dart_define_wins_over_bundled_env', () {
    expect(AppConfig.resolveApiBaseUrl(dartDefine: prod, bundledEnv: bundled), prod);
  });

  test('without a define the bundled .env is used', () {
    expect(AppConfig.resolveApiBaseUrl(dartDefine: '', bundledEnv: bundled), bundled);
    expect(
      AppConfig.resolveApiBaseUrl(dartDefine: '', bundledEnv: 'https://staging.example.eu/api/v1'),
      'https://staging.example.eu/api/v1',
    );
  });

  test('with neither, the local-dev default applies', () {
    expect(AppConfig.resolveApiBaseUrl(dartDefine: '', bundledEnv: null), AppConfig.localDevBaseUrl);
    expect(AppConfig.resolveApiBaseUrl(dartDefine: '  ', bundledEnv: ''), AppConfig.localDevBaseUrl);
  });

  test('the getter works when .env was never loaded (tests)', () {
    expect(AppConfig.apiBaseUrl, isNotEmpty);
  });
}
