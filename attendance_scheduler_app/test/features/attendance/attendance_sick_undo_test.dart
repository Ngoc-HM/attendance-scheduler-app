// Taking an S back restores the colleague's A/D cover on the server
// (2026-11-13), so the admin's grid reloads the month instead of patching
// only the edited cell.

import 'package:attendance_scheduler_app/features/attendance/data/datasources/attendance_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/auth/data/models/user_model.dart';
import 'package:attendance_scheduler_app/features/attendance/data/datasources/calculations_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/attendance/domain/entities/attendance_entities.dart';
import 'package:attendance_scheduler_app/features/attendance/presentation/providers/attendance_provider.dart';
import 'package:attendance_scheduler_app/features/users/data/user_management_datasource.dart';
import 'package:flutter_test/flutter_test.dart';

class _Users implements UserManagementDataSource, CalculationsRemoteDataSource {
  @override
  Future<List<UserModel>> list() async => const [];

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

AttendanceRecord _rec(int id, int userId, String code) => AttendanceRecord(
  id: id,
  userId: userId,
  workDate: DateTime(2093, 4, 7),
  code: code,
);

class _Server implements AttendanceRemoteDataSource {
  List<AttendanceRecord> month = [_rec(1, 1, 'S'), _rec(2, 2, 'A/D')];
  int fetches = 0;

  @override
  Future<List<AttendanceRecord>> fetchAll({
    required int year,
    required int month,
  }) async {
    fetches++;
    return this.month;
  }

  @override
  Future<List<Holiday>> fetchHolidays(int year) async => const [];

  @override
  Future<AttendanceRecord> upsert({
    required int userId,
    required DateTime workDate,
    required String code,
    String? note,
  }) async {
    // What the backend does: the S goes, the cover gets its D back.
    month = [_rec(1, 1, code), _rec(2, 2, 'D')];
    return month.first;
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  test('taking an S back reloads the cover cell too', () async {
    final server = _Server();
    final ctrl = AttendanceController(server, _Users(), _Users());
    await ctrl.load(2093, 4, isAdmin: true);

    final ok = await ctrl.upsert(
      userId: 1,
      workDate: DateTime(2093, 4, 7),
      code: 'A',
    );

    expect(ok, isTrue);
    expect(server.fetches, 2);
    expect(
      ctrl.state.records.map((r) => (r.userId, r.code)),
      [(1, 'A'), (2, 'D')],
    );
  });

  test('an ordinary edit patches only its cell', () async {
    final server = _Server()..month = [_rec(1, 1, 'A'), _rec(2, 2, 'D')];
    final ctrl = AttendanceController(server, _Users(), _Users());
    await ctrl.load(2093, 4, isAdmin: true);

    await ctrl.upsert(userId: 1, workDate: DateTime(2093, 4, 7), code: 'T');

    expect(server.fetches, 1);
  });
}
