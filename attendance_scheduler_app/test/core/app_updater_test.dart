// Self-update check (2026-11-15): newer builds are offered, a build below the
// server's minimum must update, dev builds and network errors offer nothing.

import 'package:attendance_scheduler_app/core/update/app_updater.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

/// Answers every request with [body] (or fails when [body] is null).
class _Adapter implements HttpClientAdapter {
  _Adapter(this.body);
  final String? body;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<List<int>>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    if (body == null) {
      throw DioException.connectionError(
        requestOptions: options,
        reason: 'offline',
      );
    }
    return ResponseBody.fromString(body!, 200, headers: {
      Headers.contentTypeHeader: ['application/json'],
    });
  }

  @override
  void close({bool force = false}) {}
}

AppUpdater _updater(String? body, int build) => AppUpdater(
  dio: Dio(BaseOptions(baseUrl: 'http://x/api/v1'))
    ..httpClientAdapter = _Adapter(body),
  currentBuild: build,
);

const _release = '''
{"build": 230, "version": "1.0.0", "min_build": 225, "notes": "",
 "downloads": {"windows": "/app/download/windows",
               "macos": "/app/download/macos",
               "linux": "/app/download/linux"}}''';

void main() {
  test('a newer build is offered, optional above the minimum', () async {
    final offer = await _updater(_release, 228).check();
    expect(offer?.release.build, 230);
    expect(offer?.mandatory, isFalse);
  });

  test('a build below the minimum must update', () async {
    final offer = await _updater(_release, 220).check();
    expect(offer?.mandatory, isTrue);
  });

  test('same build, dev build, nothing published or offline: no offer',
      () async {
    expect(await _updater(_release, 230).check(), isNull);
    expect(await _updater(_release, 0).check(), isNull);
    expect(await _updater('null', 228).check(), isNull);
    expect(await _updater(null, 228).check(), isNull);
  });
}
