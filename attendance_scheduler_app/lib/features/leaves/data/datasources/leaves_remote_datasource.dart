import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/api_endpoints.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/network/api_exception.dart';
import '../models/leave_model.dart';

final leavesDataSourceProvider = Provider<LeavesRemoteDataSource>(
  (ref) => LeavesRemoteDataSource(ref.watch(dioProvider)),
);

/// Remote calls for Leaves (F-05, F-06).
class LeavesRemoteDataSource {
  LeavesRemoteDataSource(this._dio);

  final Dio _dio;

  /// GET /leaves — own requests; admin may pass ?all=true.
  Future<List<LeaveModel>> listOwn() async {
    try {
      final response = await _dio.get(ApiEndpoints.leaves);
      return _parseList(response.data);
    } on DioException catch (e) {
      throw ApiException(
        e.message ?? 'Failed to load leave requests',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// GET /leaves?all=true — admin: all users' requests.
  Future<List<LeaveModel>> listAll() async {
    try {
      final response = await _dio.get(
        ApiEndpoints.leaves,
        queryParameters: {'all': true},
      );
      return _parseList(response.data);
    } on DioException catch (e) {
      throw ApiException(
        e.message ?? 'Failed to load all leave requests',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// GET /leaves/pending — admin queue (pending only).
  Future<List<LeaveModel>> listPending() async {
    try {
      final response = await _dio.get(ApiEndpoints.leavesPending);
      return _parseList(response.data);
    } on DioException catch (e) {
      throw ApiException(
        e.message ?? 'Failed to load pending leaves',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// POST /leaves — submit a leave request.
  Future<LeaveModel> create({
    required DateTime startDate,
    required DateTime endDate,
    String? note,
  }) async {
    try {
      final response = await _dio.post(
        ApiEndpoints.leaves,
        data: {
          'start_date': _fmt(startDate),
          'end_date': _fmt(endDate),
          if (note != null && note.isNotEmpty) 'note': note,
        },
      );
      return LeaveModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(
        e.message ?? 'Failed to submit leave request',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// POST /leaves/{id}/decide — admin approve or reject.
  Future<LeaveModel> decide(int id, String status) async {
    try {
      final response = await _dio.post(
        ApiEndpoints.leaveDecide(id),
        data: {'status': status},
      );
      return LeaveModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(
        e.message ?? 'Failed to process leave decision',
        statusCode: e.response?.statusCode,
      );
    }
  }

  // ---------------------------------------------------------------------------

  static List<LeaveModel> _parseList(dynamic data) =>
      (data as List<dynamic>)
          .map((e) => LeaveModel.fromJson(e as Map<String, dynamic>))
          .toList();

  static String _fmt(DateTime d) =>
      '${d.year}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
}
