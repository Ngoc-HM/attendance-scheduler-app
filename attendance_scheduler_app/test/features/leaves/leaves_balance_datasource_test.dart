// GET /leaves/balance (D4): request shape and parsing, answered by a Dio
// interceptor so no server is needed.

import 'package:attendance_scheduler_app/core/constants/api_endpoints.dart';
import 'package:attendance_scheduler_app/features/leaves/data/datasources/leaves_remote_datasource.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

/// A Dio whose every request is recorded and answered with [body].
(Dio, List<RequestOptions>) _dioAnswering(Map<String, dynamic> body) {
  final seen = <RequestOptions>[];
  final dio = Dio()
    ..interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          seen.add(options);
          handler.resolve(
            Response(requestOptions: options, data: body, statusCode: 200),
          );
        },
      ),
    );
  return (dio, seen);
}

const _body = {
  'year': 2040,
  'quota': 30,
  'used': 3,
  'pending': 2,
  'remaining': 27,
};

void main() {
  test('fetchBalance asks for the given year and parses the summary', () async {
    final (dio, seen) = _dioAnswering(_body);

    final balance = await LeavesRemoteDataSource(dio).fetchBalance(year: 2040);

    expect(seen.single.path, ApiEndpoints.leaveBalance);
    expect(ApiEndpoints.leaveBalance, '/leaves/balance');
    expect(seen.single.queryParameters, {'year': 2040});
    expect(
      (balance.year, balance.quota, balance.used, balance.pending),
      (2040, 30, 3, 2),
    );
    expect(balance.remaining, 27);
  });

  test('fetchBalance without a year leaves it to the server', () async {
    final (dio, seen) = _dioAnswering(_body);

    await LeavesRemoteDataSource(dio).fetchBalance();

    expect(seen.single.queryParameters, isEmpty);
  });
}
