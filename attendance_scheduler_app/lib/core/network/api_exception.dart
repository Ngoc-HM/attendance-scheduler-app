import 'package:dio/dio.dart';

/// Normalized API error surfaced to the presentation layer.
class ApiException implements Exception {
  const ApiException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;

  /// Build from a [DioException], extracting the backend `detail` message
  /// safely. On 5xx the response body is often an HTML/text traceback (a
  /// String, not a JSON map) — indexing it with `['detail']` would throw
  /// "String is not a subtype of int of 'index'", so we only read `detail`
  /// when the body is actually a Map and fall back to a friendly message.
  factory ApiException.fromDio(DioException e, [String fallback = 'request_failed']) {
    final data = e.response?.data;
    final detail = data is Map ? data['detail']?.toString() : null;
    return ApiException(
      detail ?? e.message ?? fallback,
      statusCode: e.response?.statusCode,
    );
  }

  @override
  String toString() => 'ApiException($statusCode): $message';
}
