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
    this.checkInLocal,
    this.checkOutLocal,
  });

  final int id;
  final int userId;
  final DateTime workDate;
  final DateTime? checkInAt;
  final DateTime? checkOutAt;

  /// The punches as "HH:MM" on the business clock (Frankfurt), as the server
  /// reports them: what the screens show, whatever the device's zone.
  final String? checkInLocal;
  final String? checkOutLocal;

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
        checkInLocal: json['check_in_local'] as String?,
        checkOutLocal: json['check_out_local'] as String?,
      );

  @override
  List<Object?> get props =>
      [id, userId, workDate, checkInAt, checkOutAt, checkInLocal, checkOutLocal];
}

/// The business clock right now (`GET /attendance/clock/now`): the app asks
/// the server instead of trusting the device clock.
class ClockNow {
  const ClockNow({required this.date, required this.time});

  /// Today on the business clock (date only).
  final DateTime date;

  /// "HH:MM" on the business clock.
  final String time;

  factory ClockNow.fromJson(Map<String, dynamic> json) => ClockNow(
        date: DateTime.parse(json['date'] as String),
        time: json['time'] as String,
      );
}

/// An entry in the admin's month list. Times are HH:MM in the business
/// timezone (Frankfurt), as the server reports them, so an admin abroad
/// reads and corrects the same clock the staff punched on.
class StaffClockEntry extends Equatable {
  const StaffClockEntry({
    required this.userId,
    required this.workDate,
    required this.fullName,
    required this.code,
    this.checkIn,
    this.checkOut,
    this.corrected = false,
  });

  final int userId;
  final DateTime workDate;
  final String fullName;
  final String code;
  final String? checkIn;
  final String? checkOut;

  /// Set by the admin rather than punched.
  final bool corrected;

  factory StaffClockEntry.fromJson(Map<String, dynamic> json) =>
      StaffClockEntry(
        userId: json['user_id'] as int,
        workDate: DateTime.parse(json['work_date'] as String),
        fullName: json['full_name'] as String,
        code: json['code'] as String,
        checkIn: json['check_in_local'] as String?,
        checkOut: json['check_out_local'] as String?,
        corrected: json['corrected'] as bool? ?? false,
      );

  @override
  List<Object?> get props =>
      [userId, workDate, fullName, code, checkIn, checkOut, corrected];
}

/// One (person, day) of the admin's attendance board: the punches read
/// against the day's code (`GET /attendance/clock/board`). [status] is
/// `working`, `missed_out`, `absent`, `off_day` or `ok`.
class ClockBoardCell extends Equatable {
  const ClockBoardCell({
    required this.userId,
    required this.workDate,
    this.status,
    this.checkIn,
    this.checkOut,
    this.corrected = false,
    this.tint,
  });

  final int userId;
  final DateTime workDate;

  /// null for an adjusted day with no punch and no duty.
  final String? status;

  /// `missing` (light red) or `adjusted` (light yellow); null = no tint.
  final String? tint;
  final String? checkIn;
  final String? checkOut;
  final bool corrected;

  factory ClockBoardCell.fromJson(Map<String, dynamic> json) => ClockBoardCell(
        userId: json['user_id'] as int,
        workDate: DateTime.parse(json['work_date'] as String),
        status: json['status'] as String?,
        tint: json['tint'] as String?,
        checkIn: json['check_in_local'] as String?,
        checkOut: json['check_out_local'] as String?,
        corrected: json['corrected'] as bool? ?? false,
      );

  @override
  List<Object?> get props =>
      [userId, workDate, status, checkIn, checkOut, corrected, tint];
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

  /// The business clock right now (any signed-in user).
  Future<ClockNow> now() async {
    try {
      final response = await _dio.get(ApiEndpoints.clockNow);
      return ClockNow.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDio(e, 'clock_now_failed');
    }
  }

  /// Admin: everyone's entries of the month.
  Future<List<StaffClockEntry>> staffMonth(int year, int month) async {
    try {
      final response = await _dio.get(
        ApiEndpoints.clockStaff,
        queryParameters: {'year': year, 'month': month},
      );
      return (response.data as List<dynamic>)
          .map((e) => StaffClockEntry.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException.fromDio(e, 'clock_staff_failed');
    }
  }

  /// Admin: set a person's punches for a day ("HH:MM", Frankfurt time);
  /// a null [checkOut] leaves the day open.
  Future<void> correct({
    required int userId,
    required DateTime workDate,
    required String checkIn,
    String? checkOut,
  }) async {
    try {
      await _dio.put(ApiEndpoints.clockStaff, data: {
        'user_id': userId,
        'work_date': '${workDate.year.toString().padLeft(4, '0')}-'
            '${workDate.month.toString().padLeft(2, '0')}-'
            '${workDate.day.toString().padLeft(2, '0')}',
        'check_in': checkIn,
        'check_out': ?checkOut,
      });
    } on DioException catch (e) {
      throw ApiException.fromDio(e, 'clock_correct_failed');
    }
  }

  /// Admin: the month's punches read against the attendance codes.
  Future<List<ClockBoardCell>> board(int year, int month) async {
    try {
      final response = await _dio.get(
        ApiEndpoints.clockBoard,
        queryParameters: {'year': year, 'month': month},
      );
      return (response.data as List<dynamic>)
          .map((e) => ClockBoardCell.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException.fromDio(e, 'clock_board_failed');
    }
  }
}

/// Admin: the clock board of a month, keyed (year, month).
final clockBoardProvider = FutureProvider.autoDispose
    .family<List<ClockBoardCell>, (int, int)>(
  (ref, ym) => ref.watch(timeClockRemoteDataSourceProvider).board(ym.$1, ym.$2),
);
