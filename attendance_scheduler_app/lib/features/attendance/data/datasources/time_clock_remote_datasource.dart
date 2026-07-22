import 'package:dio/dio.dart';
import 'package:equatable/equatable.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/api_endpoints.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/network/api_exception.dart';

/// One check-in/out row (mirrors `schemas/time_clock.py`). Small enough to
/// live beside its datasource — the admin attendance grid never uses it.
class TimeClockEntry extends Equatable {
  const TimeClockEntry({
    required this.id,
    required this.userId,
    required this.workDate,
    this.checkInAt,
    this.checkOutAt,
  });

  final int id;
  final int userId;
  final DateTime workDate;
  final DateTime? checkInAt;
  final DateTime? checkOutAt;

  factory TimeClockEntry.fromJson(Map<String, dynamic> json) => TimeClockEntry(
        id: json['id'] as int,
        userId: json['user_id'] as int,
        workDate: DateTime.parse(json['work_date'] as String),
        checkInAt: json['check_in_at'] != null
            ? DateTime.parse(json['check_in_at'] as String).toLocal()
            : null,
        checkOutAt: json['check_out_at'] != null
            ? DateTime.parse(json['check_out_at'] as String).toLocal()
            : null,
      );

  @override
  List<Object?> get props => [id, userId, workDate, checkInAt, checkOutAt];
}

final timeClockRemoteDataSourceProvider = Provider<TimeClockRemoteDataSource>(
  (ref) => TimeClockRemoteDataSource(ref.watch(dioProvider)),
);

/// Time-clock API calls — own data only (owner 2026-07-09).
class TimeClockRemoteDataSource {
  TimeClockRemoteDataSource(this._dio);

  final Dio _dio;

  Future<TimeClockEntry> checkIn() async {
    try {
      final response = await _dio.post(ApiEndpoints.clockCheckIn);
      return TimeClockEntry.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDio(e, 'clock_check_in_failed');
    }
  }

  Future<TimeClockEntry> checkOut() async {
    try {
      final response = await _dio.post(ApiEndpoints.clockCheckOut);
      return TimeClockEntry.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDio(e, 'clock_check_out_failed');
    }
  }

  /// Today's own entry, or null when not clocked in yet.
  Future<TimeClockEntry?> today() async {
    try {
      final response = await _dio.get(ApiEndpoints.clockToday);
      final data = response.data;
      if (data == null) return null;
      return TimeClockEntry.fromJson(data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDio(e, 'clock_today_failed');
    }
  }

  Future<List<TimeClockEntry>> month(int year, int month) async {
    try {
      final response = await _dio.get(
        ApiEndpoints.clockMe,
        queryParameters: {'year': year, 'month': month},
      );
      final list = response.data as List<dynamic>;
      return list
          .map((e) => TimeClockEntry.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException.fromDio(e, 'clock_month_failed');
    }
  }
}
