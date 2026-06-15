import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/api_endpoints.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/network/api_exception.dart';

final reportsDataSourceProvider = Provider<ReportsRemoteDataSource>(
  (ref) => ReportsRemoteDataSource(ref.watch(dioProvider)),
);

/// Result from a report download — raw bytes + suggested filename.
class ReportDownload {
  const ReportDownload({required this.bytes, required this.filename});
  final List<int> bytes;
  final String filename;
}

/// Remote calls for Reports (F-15).
///
/// Both endpoints stream a file (CSV or XLSX). We request responseType=bytes
/// and return raw bytes + a suggested filename derived from the
/// Content-Disposition header (with fallback).
class ReportsRemoteDataSource {
  ReportsRemoteDataSource(this._dio);

  final Dio _dio;

  /// GET /reports/monthly/{year}/{month}?format=csv|xlsx
  Future<ReportDownload> monthly(int year, int month, String format) async {
    try {
      final response = await _dio.get(
        ApiEndpoints.monthlyReport(year, month),
        queryParameters: {'format': format},
        options: Options(responseType: ResponseType.bytes),
      );
      return ReportDownload(
        bytes: response.data as List<int>,
        filename: _extractFilename(response, 'attendance_${year}_${_two(month)}.$format'),
      );
    } on DioException catch (e) {
      throw ApiException(
        e.message ?? 'Failed to download monthly report',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// GET /reports/yearly/{year}?format=csv|xlsx
  Future<ReportDownload> yearly(int year, String format) async {
    try {
      final response = await _dio.get(
        ApiEndpoints.yearlyReport(year),
        queryParameters: {'format': format},
        options: Options(responseType: ResponseType.bytes),
      );
      return ReportDownload(
        bytes: response.data as List<int>,
        filename: _extractFilename(response, 'attendance_$year.$format'),
      );
    } on DioException catch (e) {
      throw ApiException(
        e.message ?? 'Failed to download yearly report',
        statusCode: e.response?.statusCode,
      );
    }
  }

  // ---------------------------------------------------------------------------

  /// Parse Content-Disposition: attachment; filename="foo.csv" → "foo.csv".
  static String _extractFilename(Response<dynamic> response, String fallback) {
    final header = response.headers.value('content-disposition') ?? '';
    final match = RegExp(r'filename="?([^";]+)"?').firstMatch(header);
    return match?.group(1) ?? fallback;
  }

  static String _two(int v) => v.toString().padLeft(2, '0');
}
