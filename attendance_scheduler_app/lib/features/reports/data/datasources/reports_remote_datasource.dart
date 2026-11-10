import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/api_endpoints.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/network/api_exception.dart';
import '../../../../core/utils/file_download.dart';

final reportsDataSourceProvider = Provider<ReportsRemoteDataSource>(
  (ref) => ReportsRemoteDataSource(ref.watch(dioProvider)),
);

/// Result from a report download — raw bytes + suggested filename.
typedef ReportDownload = FileDownload;

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
        filename: filenameFromContentDisposition(response, 'attendance_${year}_${_two(month)}.$format'),
      );
    } on DioException catch (e) {
      // The error body arrives as bytes (responseType.bytes); fromDio
      // decodes it so the user sees the backend's detail.
      throw ApiException.fromDio(e, 'Failed to download monthly report');
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
        filename: filenameFromContentDisposition(response, 'attendance_$year.$format'),
      );
    } on DioException catch (e) {
      // The error body arrives as bytes (responseType.bytes); fromDio
      // decodes it so the user sees the backend's detail.
      throw ApiException.fromDio(e, 'Failed to download yearly report');
    }
  }

  // ---------------------------------------------------------------------------

  static String _two(int v) => v.toString().padLeft(2, '0');
}
