import 'dart:convert';

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
    return ApiException(
      detailOf(e.response?.data) ?? e.message ?? fallback,
      statusCode: e.response?.statusCode,
    );
  }

  /// The backend `detail` of an error body, or null. A string detail is
  /// returned as is; FastAPI's 422 list is flattened to its `msg`s; an
  /// import rejection (`{message, errors}`) lists its first errors; a body
  /// fetched as bytes (file downloads) is decoded as UTF-8 JSON first.
  static String? detailOf(Object? data) {
    var body = data;
    if (body is List<int>) {
      try {
        body = jsonDecode(utf8.decode(body));
      } catch (_) {
        return null;
      }
    }
    if (body is! Map) return null;
    final detail = body['detail'];
    if (detail is List) {
      final messages = [
        for (final item in detail)
          if (item is Map && item['msg'] != null)
            item['msg'].toString()
          else if (item is String)
            item,
      ];
      return messages.isEmpty ? null : messages.join('; ');
    }
    if (detail is Map) return _messageWithErrors(detail);
    return detail?.toString();
  }

  /// Most row errors shown from one rejected import; the rest are counted.
  static const _maxListedErrors = 5;

  /// `{message, errors: [...]}` (a rejected Excel import) as one sentence:
  /// the message, then the first row/cell errors.
  static String? _messageWithErrors(Map<dynamic, dynamic> detail) {
    final message = detail['message']?.toString();
    final errors = [
      if (detail['errors'] is List)
        for (final item in detail['errors'] as List) item.toString(),
    ];
    if (errors.isEmpty) return message;
    final listed = errors.take(_maxListedErrors).join('; ');
    final more = errors.length > _maxListedErrors
        ? ' (+${errors.length - _maxListedErrors})'
        : '';
    return [?message, '$listed$more'].join(' ');
  }

  @override
  String toString() => 'ApiException($statusCode): $message';
}
