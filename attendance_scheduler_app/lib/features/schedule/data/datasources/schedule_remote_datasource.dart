import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/api_endpoints.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/network/api_exception.dart';
import '../models/schedule_model.dart';
import '../../domain/entities/schedule_entities.dart';

final scheduleRemoteDataSourceProvider =
    Provider<ScheduleRemoteDataSource>(
  (ref) => ScheduleRemoteDataSource(ref.watch(dioProvider)),
);

/// All schedule + shift-change API calls (F-07..F-09, decision #8).
class ScheduleRemoteDataSource {
  ScheduleRemoteDataSource(this._dio);

  final Dio _dio;

  /// GET /schedules/{year}/{month}
  Future<MonthlySchedule> fetchSchedule(int year, int month) async {
    try {
      final response = await _dio.get(ApiEndpoints.schedule(year, month));
      return MonthlyScheduleModel.fromJson(
          response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDio(e, 'fetch_failed');
    }
  }

  /// POST /schedules/generate
  Future<ScheduleResult> generate({
    required int year,
    required int month,
    bool force = false,
  }) async {
    try {
      final response = await _dio.post(
        ApiEndpoints.generateSchedule,
        data: {'year': year, 'month': month, 'force': force},
      );
      return ScheduleResultModel.fromJson(
          response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDio(e, 'generate_failed');
    }
  }

  /// POST /schedules/{id}/override
  Future<MonthlySchedule> override({
    required int scheduleId,
    required int userId,
    required DateTime workDate,
    required String code,
  }) async {
    try {
      final response = await _dio.post(
        ApiEndpoints.scheduleOverride(scheduleId),
        data: {
          'user_id': userId,
          'work_date':
              '${workDate.year}-${workDate.month.toString().padLeft(2, '0')}-${workDate.day.toString().padLeft(2, '0')}',
          'code': code,
        },
      );
      return MonthlyScheduleModel.fromJson(
          response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDio(e, 'override_failed');
    }
  }

  /// POST /schedules/{id}/publish
  Future<MonthlySchedule> publish(int scheduleId) async {
    try {
      final response =
          await _dio.post(ApiEndpoints.schedulePublish(scheduleId));
      return MonthlyScheduleModel.fromJson(
          response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDio(e, 'publish_failed');
    }
  }

  /// GET /shift-changes — all=true for admin list.
  Future<List<ShiftChangeRequest>> fetchShiftChanges({
    bool all = false,
  }) async {
    try {
      final response = await _dio.get(
        ApiEndpoints.shiftChanges,
        queryParameters: all ? {'all': true} : null,
      );
      final list = response.data as List<dynamic>;
      return list
          .map((e) =>
              ShiftChangeRequestModel.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException.fromDio(e, 'shift_changes_fetch_failed');
    }
  }

  /// POST /shift-changes — user submits own request.
  Future<ShiftChangeRequest> createShiftChange({
    required DateTime workDate,
    required String kind,
    String? requestedCode,
    int? counterpartUserId,
    String? note,
  }) async {
    try {
      final data = <String, dynamic>{
        'work_date':
            '${workDate.year}-${workDate.month.toString().padLeft(2, '0')}-${workDate.day.toString().padLeft(2, '0')}',
        'kind': kind,
      };
      if (requestedCode != null) data['requested_code'] = requestedCode;
      if (counterpartUserId != null) {
        data['counterpart_user_id'] = counterpartUserId;
      }
      if (note != null && note.isNotEmpty) data['note'] = note;

      final response = await _dio.post(ApiEndpoints.shiftChanges, data: data);
      return ShiftChangeRequestModel.fromJson(
          response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDio(e, 'shift_change_create_failed');
    }
  }

  /// POST /shift-changes/{id}/decide
  Future<ShiftChangeRequest> decideShiftChange({
    required int id,
    required String status, // "approved" | "rejected"
  }) async {
    try {
      final response = await _dio.post(
        ApiEndpoints.shiftChangeDecide(id),
        data: {'status': status},
      );
      return ShiftChangeRequestModel.fromJson(
          response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDio(e, 'shift_change_decide_failed');
    }
  }
}
