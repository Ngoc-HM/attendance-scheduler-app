// A2: POST /attendance/sick-cover takes the backend AttendanceUpsert
// {user_id, work_date, code, note?} and code must be "S". The app used to
// send no code, so every sick-cover call failed with 422.

import 'dart:convert';
import 'dart:typed_data';

import 'package:attendance_scheduler_app/core/network/api_exception.dart';
import 'package:attendance_scheduler_app/features/attendance/data/datasources/attendance_remote_datasource.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

/// Mimics FastAPI: AttendanceUpsert requires user_id, work_date AND code.
class _FastApiLike implements HttpClientAdapter {
  Map<String, dynamic>? lastBody;

  static const _json = {
    Headers.contentTypeHeader: [Headers.jsonContentType],
  };

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    final body = Map<String, dynamic>.from(options.data as Map);
    lastBody = body;
    final missing = [
      'user_id',
      'work_date',
      'code',
    ].where((k) => !body.containsKey(k)).toList();
    if (missing.isNotEmpty) {
      return ResponseBody.fromString(
        jsonEncode({
          'detail': [
            for (final m in missing)
              {
                'type': 'missing',
                'loc': ['body', m],
                'msg': 'Field required',
              },
          ],
        }),
        422,
        headers: _json,
      );
    }
    final record = {
      'id': 1,
      'user_id': body['user_id'],
      'work_date': body['work_date'],
      'code': body['code'],
    };
    return ResponseBody.fromString(
      jsonEncode({'sick': record, 'cover': null, 'message': null}),
      200,
      headers: _json,
    );
  }

  @override
  void close({bool force = false}) {}
}

DioException _badResponse(int status, Object? data) => DioException(
  requestOptions: RequestOptions(path: '/x'),
  response: Response(
    requestOptions: RequestOptions(path: '/x'),
    statusCode: status,
    data: data,
  ),
  type: DioExceptionType.badResponse,
);

void main() {
  test('sick_cover_body_contains_code_S', () async {
    final adapter = _FastApiLike();
    final dio = Dio(BaseOptions(baseUrl: 'http://x/api/v1'))
      ..httpClientAdapter = adapter;

    final result = await AttendanceRemoteDataSource(
      dio,
    ).sickCover(userId: 3, workDate: DateTime(2026, 11, 9), note: 'flu');

    expect(adapter.lastBody, {
      'user_id': 3,
      'work_date': '2026-11-09',
      'code': 'S',
      'note': 'flu',
    });
    expect(result.sick.code, 'S');
  });

  test('a 422 detail list is flattened to its messages', () {
    final api = ApiException.fromDio(
      _badResponse(422, {
        'detail': [
          {
            'type': 'missing',
            'loc': ['body', 'code'],
            'msg': 'Field required',
          },
          {
            'type': 'value_error',
            'loc': ['body', 'note'],
            'msg': 'Too long',
          },
        ],
      }),
      'fallback',
    );

    expect(api.message, 'Field required; Too long');
    expect(api.statusCode, 422);
  });

  test('a detail inside a bytes body (file download) is decoded', () {
    final api = ApiException.fromDio(
      _badResponse(
        409,
        Uint8List.fromList(utf8.encode('{"detail":"Tháng đã khoá"}')),
      ),
      'fallback',
    );

    expect(api.message, 'Tháng đã khoá');
  });
}
