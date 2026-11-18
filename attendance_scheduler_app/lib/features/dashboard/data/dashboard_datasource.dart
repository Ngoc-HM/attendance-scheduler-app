import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants/api_endpoints.dart';
import '../../../core/constants/shift_codes.dart';
import '../../../core/network/api_client.dart';
import '../../../core/network/api_exception.dart';

final dashboardDataSourceProvider = Provider<DashboardDataSource>(
  (ref) => DashboardDataSource(ref.watch(dioProvider)),
);

ShiftCode? _shift(Object? value) {
  for (final code in ShiftCode.values) {
    if (code.code == value) return code;
  }
  return null;
}

/// One person's roster cell of today with today's punches.
class DashboardDuty {
  const DashboardDuty({
    required this.code,
    required this.shift,
    this.checkIn,
    this.checkOut,
  });

  factory DashboardDuty.fromJson(Map<String, dynamic> json) => DashboardDuty(
    code: json['code'] as String,
    shift: _shift(json['shift']),
    checkIn: json['check_in_local'] as String?,
    checkOut: json['check_out_local'] as String?,
  );

  /// The person's code (A3, F1, …).
  final String code;

  /// Null for a symbol this app version does not know.
  final ShiftCode? shift;
  final String? checkIn;
  final String? checkOut;
}

/// A past working day of this month without check-in or check-out.
class DashboardMissing {
  const DashboardMissing({
    required this.code,
    required this.workDate,
    required this.status,
  });

  factory DashboardMissing.fromJson(Map<String, dynamic> json) =>
      DashboardMissing(
        code: json['code'] as String,
        workDate: DateTime.parse(json['work_date'] as String),
        status: json['status'] as String,
      );

  final String code;
  final DateTime workDate;

  /// `absent` (no check-in) or `missed_out` (no check-out).
  final String status;
}

class DashboardSchedule {
  const DashboardSchedule({
    required this.year,
    required this.month,
    required this.status,
    required this.violations,
  });

  factory DashboardSchedule.fromJson(Map<String, dynamic> json) =>
      DashboardSchedule(
        year: json['year'] as int,
        month: json['month'] as int,
        status: json['status'] as String?,
        violations: [
          for (final line in json['violations'] as List<dynamic>? ?? const [])
            line.toString(),
        ],
      );

  final int year;
  final int month;

  /// `draft`, `published`, or null when the month has no schedule yet.
  final String? status;
  final List<String> violations;
}

class DashboardLeave {
  const DashboardLeave({
    required this.code,
    required this.role,
    required this.quota,
    required this.used,
    required this.pending,
    required this.available,
    required this.nextRegistered,
    required this.nextAvailable,
    required this.carryComp,
  });

  factory DashboardLeave.fromJson(Map<String, dynamic> json) => DashboardLeave(
    code: json['code'] as String,
    role: json['role'] as String,
    quota: json['quota'] as int,
    used: json['used'] as int,
    pending: json['pending'] as int,
    available: json['available'] as int,
    nextRegistered: (json['next_used'] as int) + (json['next_pending'] as int),
    nextAvailable: json['next_available'] as int,
    carryComp: json['carry_comp'] as int,
  );

  final String code;
  final String role;
  final int quota;
  final int used;
  final int pending;

  /// What the person can still register: quota − approved − pending.
  final int available;

  /// The same for the year after, which is the one being registered now.
  final int nextRegistered;
  final int nextAvailable;
  final int carryComp;

  /// Days registered this year, approved or still waiting: a filed request
  /// counts at once.
  int get registered => used + pending;
}

/// The admin dashboard (GET /dashboard, customer 2026-11-18).
class DashboardData {
  const DashboardData({
    required this.today,
    required this.working,
    required this.off,
    required this.missingClock,
    required this.pendingTotal,
    required this.thisMonth,
    required this.nextMonth,
    required this.leaveYear,
    required this.leave,
  });

  factory DashboardData.fromJson(Map<String, dynamic> json) {
    List<T> list<T>(String key, T Function(Map<String, dynamic>) parse) => [
      for (final item in json[key] as List<dynamic>? ?? const [])
        parse(item as Map<String, dynamic>),
    ];
    final pending = json['pending'] as Map<String, dynamic>;
    return DashboardData(
      today: DateTime.parse(json['today'] as String),
      working: list('working', DashboardDuty.fromJson),
      off: list('off', DashboardDuty.fromJson),
      missingClock: list('missing_clock', DashboardMissing.fromJson),
      pendingTotal:
          (pending['leaves'] as int) +
          (pending['shift_changes'] as int) +
          (pending['users'] as int),
      thisMonth: DashboardSchedule.fromJson(
        json['this_month'] as Map<String, dynamic>,
      ),
      nextMonth: DashboardSchedule.fromJson(
        json['next_month'] as Map<String, dynamic>,
      ),
      leaveYear: json['leave_year'] as int,
      leave: list('leave', DashboardLeave.fromJson),
    );
  }

  final DateTime today;
  final List<DashboardDuty> working;
  final List<DashboardDuty> off;
  final List<DashboardMissing> missingClock;

  /// Leave requests + shift changes + sign-ups waiting for a decision.
  final int pendingTotal;
  final DashboardSchedule thisMonth;
  final DashboardSchedule nextMonth;
  final int leaveYear;
  final List<DashboardLeave> leave;
}

class DashboardDataSource {
  DashboardDataSource(this._dio);

  final Dio _dio;

  /// GET /dashboard — admin only.
  Future<DashboardData> fetch() async {
    try {
      final response = await _dio.get(ApiEndpoints.dashboard);
      return DashboardData.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDio(e, 'Failed to load the dashboard');
    }
  }
}
