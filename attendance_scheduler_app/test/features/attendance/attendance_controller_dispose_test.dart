// Logout invalidates the attendance provider (Task 11), possibly while a
// request is in flight: the late response must store nothing and throw
// nothing ("Tried to use AttendanceController after dispose").

import 'dart:async';

import 'package:attendance_scheduler_app/core/network/api_exception.dart';
import 'package:attendance_scheduler_app/features/attendance/data/datasources/attendance_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/attendance/data/datasources/calculations_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/attendance/domain/entities/attendance_entities.dart';
import 'package:attendance_scheduler_app/features/attendance/presentation/providers/attendance_provider.dart';
import 'package:attendance_scheduler_app/features/users/data/user_management_datasource.dart';
import 'package:flutter_test/flutter_test.dart';

class _Unused implements UserManagementDataSource, CalculationsRemoteDataSource {
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

/// Own records and upserts wait for the test; holidays answer at once.
class _Gated implements AttendanceRemoteDataSource {
  final records = Completer<List<AttendanceRecord>>();
  final upserted = Completer<AttendanceRecord>();

  @override
  Future<List<AttendanceRecord>> fetchMine({
    required int year,
    required int month,
  }) => records.future;

  @override
  Future<List<Holiday>> fetchHolidays(int year) async => const [];

  @override
  Future<AttendanceRecord> upsert({
    required int userId,
    required DateTime workDate,
    required String code,
    String? note,
  }) => upserted.future;

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  test('a load or save finishing after dispose throws nothing', () async {
    final ds = _Gated();
    final ctrl = AttendanceController(ds, _Unused(), _Unused());

    final load = ctrl.load(2026, 11);
    final save = ctrl.upsert(
      userId: 7,
      workDate: DateTime(2026, 11, 3),
      code: 'A',
    );
    ctrl.dispose();
    ds.records.complete(const []);
    ds.upserted.completeError(const ApiException('late', statusCode: 409));

    await expectLater(load, completes);
    expect(await save, isFalse);
  });
}
