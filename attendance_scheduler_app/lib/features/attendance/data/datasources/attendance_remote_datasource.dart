import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/api_endpoints.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/network/api_exception.dart';
import '../models/attendance_model.dart';
import '../../domain/entities/attendance_entities.dart';

final attendanceRemoteDataSourceProvider =
    Provider<AttendanceRemoteDataSource>(
  (ref) => AttendanceRemoteDataSource(ref.watch(dioProvider)),
);

/// All attendance + holiday API calls (F-10..F-13).
class AttendanceRemoteDataSource {
  AttendanceRemoteDataSource(this._dio);

  final Dio _dio;

  // ── Attendance ──────────────────────────────────────────────────────────────

  /// GET /attendance?year=&month= — admin view of all actuals.
  Future<List<AttendanceRecord>> fetchAll({
    required int year,
    required int month,
  }) async {
    try {
      final response = await _dio.get(
        ApiEndpoints.attendance,
        queryParameters: {'year': year, 'month': month},
      );
      final list = response.data as List<dynamic>;
      return list
          .map((e) =>
              AttendanceRecordModel.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException(
        e.response?.data?['detail']?.toString() ??
            e.message ??
            'attendance_fetch_failed',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// GET /attendance/me?year=&month= — non-admin own records.
  Future<List<AttendanceRecord>> fetchMine({
    required int year,
    required int month,
  }) async {
    try {
      final response = await _dio.get(
        ApiEndpoints.myAttendance,
        queryParameters: {'year': year, 'month': month},
      );
      final list = response.data as List<dynamic>;
      return list
          .map((e) =>
              AttendanceRecordModel.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException(
        e.response?.data?['detail']?.toString() ??
            e.message ??
            'my_attendance_fetch_failed',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// PUT /attendance — admin upsert a record (incl. code "S").
  Future<AttendanceRecord> upsert({
    required int userId,
    required DateTime workDate,
    required String code,
    String? note,
  }) async {
    try {
      final data = <String, dynamic>{
        'user_id': userId,
        'work_date': _formatDate(workDate),
        'code': code,
      };
      if (note != null && note.isNotEmpty) data['note'] = note;
      final response = await _dio.put(ApiEndpoints.attendance, data: data);
      return AttendanceRecordModel.fromJson(
          response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(
        e.response?.data?['detail']?.toString() ??
            e.message ??
            'attendance_upsert_failed',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// POST /attendance/sick-cover — mark sick and auto-assign cover.
  Future<SickCoverResult> sickCover({
    required int userId,
    required DateTime workDate,
  }) async {
    try {
      final response = await _dio.post(
        ApiEndpoints.attendanceSickCover,
        data: {
          'user_id': userId,
          'work_date': _formatDate(workDate),
        },
      );
      return SickCoverResultModel.fromJson(
          response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(
        e.response?.data?['detail']?.toString() ??
            e.message ??
            'sick_cover_failed',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// POST /attendance/seed — seed actuals from published schedule.
  Future<void> seed({required int year, required int month}) async {
    try {
      await _dio.post(
        ApiEndpoints.attendanceSeed,
        data: {'year': year, 'month': month},
      );
    } on DioException catch (e) {
      throw ApiException(
        e.response?.data?['detail']?.toString() ??
            e.message ??
            'attendance_seed_failed',
        statusCode: e.response?.statusCode,
      );
    }
  }

  // ── Holidays ────────────────────────────────────────────────────────────────

  /// GET /holidays?year= — list holidays for a year.
  Future<List<Holiday>> fetchHolidays(int year) async {
    try {
      final response = await _dio.get(
        ApiEndpoints.holidays,
        queryParameters: {'year': year},
      );
      final list = response.data as List<dynamic>;
      return list
          .map((e) => HolidayModel.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException(
        e.response?.data?['detail']?.toString() ??
            e.message ??
            'holidays_fetch_failed',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// PUT /holidays — admin upsert a holiday.
  Future<Holiday> upsertHoliday({
    required DateTime day,
    required String name,
  }) async {
    try {
      final response = await _dio.put(
        ApiEndpoints.holidays,
        data: {'day': _formatDate(day), 'name': name},
      );
      return HolidayModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(
        e.response?.data?['detail']?.toString() ??
            e.message ??
            'holiday_upsert_failed',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// DELETE /holidays/{id}.
  Future<void> deleteHoliday(int id) async {
    try {
      await _dio.delete(ApiEndpoints.holidayById(id));
    } on DioException catch (e) {
      throw ApiException(
        e.response?.data?['detail']?.toString() ??
            e.message ??
            'holiday_delete_failed',
        statusCode: e.response?.statusCode,
      );
    }
  }

  // ── Utilities ───────────────────────────────────────────────────────────────

  String _formatDate(DateTime d) =>
      '${d.year}-${d.month.toString().padLeft(2, '0')}-'
      '${d.day.toString().padLeft(2, '0')}';
}
