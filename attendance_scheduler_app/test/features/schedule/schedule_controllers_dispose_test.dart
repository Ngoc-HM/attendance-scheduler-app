// Logout invalidates the schedule-side providers (review 2026-11-08, final
// wave), possibly while a request is in flight: the late response — success
// or failure — must store nothing and throw nothing ("Tried to use
// ScheduleController after dispose").

import 'dart:async';
// The datasource has a method named `override`, which shadows the annotation
// inside the fake below.
import 'dart:core';
import 'dart:core' as core;

import 'package:attendance_scheduler_app/core/network/api_exception.dart';
import 'package:attendance_scheduler_app/features/schedule/data/datasources/schedule_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/schedule/domain/entities/schedule_entities.dart';
import 'package:attendance_scheduler_app/features/schedule/presentation/providers/schedule_provider.dart';
import 'package:attendance_scheduler_app/features/schedule/presentation/providers/shift_change_provider.dart';
import 'package:attendance_scheduler_app/features/users/data/user_management_datasource.dart';
import 'package:flutter_test/flutter_test.dart';

const _late = ApiException('late', statusCode: 500);

final _schedule = MonthlySchedule(
  id: 3,
  year: 2026,
  month: 11,
  status: ScheduleStatus.draft,
  assignments: [
    ShiftAssignment(
      id: 1,
      userId: 7,
      workDate: DateTime(2026, 11, 2),
      code: 'X',
      isManualOverride: false,
    ),
  ],
);

final _request = ShiftChangeRequest(
  id: 1,
  requesterId: 7,
  workDate: DateTime(2026, 11, 2),
  kind: 'change_code',
  status: 'approved',
  strictReview: false,
  warnings: const [],
);

/// Every call is parked until the test completes [pending].
class _Gate {
  final pending = <Completer<Object?>>[];

  Future<T> next<T>() {
    final c = Completer<Object?>();
    pending.add(c);
    return c.future.then((v) => v as T);
  }

  /// Answers the oldest parked call with [value].
  void answer(Object? value) => pending.removeAt(0).complete(value);

  /// Fails the oldest parked call.
  void fail() => pending.removeAt(0).completeError(_late);

  /// Fails every parked call (and the ones they start meanwhile).
  Future<void> failAll() async {
    for (var i = 0; i < 5; i++) {
      final now = List.of(pending);
      pending.clear();
      for (final c in now) {
        c.completeError(_late);
      }
      await pumpEventQueue();
    }
  }
}

class _ScheduleDs implements ScheduleRemoteDataSource {
  _ScheduleDs(this.gate);

  final _Gate gate;

  /// When set, fetchSchedule answers at once (to reach a loaded state).
  MonthlySchedule? ready;

  @core.override
  Future<MonthlySchedule> fetchSchedule(int year, int month) =>
      ready != null ? Future.value(ready) : gate.next();

  @core.override
  Future<List<ConstraintViolation>> fetchViolations(int scheduleId) =>
      ready != null ? Future.value(const []) : gate.next();

  @core.override
  Future<ScheduleResult> generate({
    required int year,
    required int month,
    bool force = false,
  }) => gate.next();

  @core.override
  Future<ScheduleResult> override({
    required int scheduleId,
    required int userId,
    required DateTime workDate,
    required String code,
  }) => gate.next();

  @core.override
  Future<MonthlySchedule> publish(int scheduleId) => gate.next();

  @core.override
  Future<List<ShiftChangeRequest>> fetchShiftChanges({bool all = false}) =>
      gate.next();

  @core.override
  Future<ShiftChangeRequest> createShiftChange({
    required DateTime workDate,
    required String kind,
    String? requestedCode,
    int? counterpartUserId,
    String? note,
  }) => gate.next();

  @core.override
  Future<ShiftChangeRequest> decideShiftChange({
    required int id,
    required String status,
  }) => gate.next();

  @core.override
  dynamic noSuchMethod(Invocation i) => super.noSuchMethod(i);
}

class _Users implements UserManagementDataSource {
  @override
  Future<List<UserDirectoryEntry>> directory() async => const [];

  @override
  dynamic noSuchMethod(Invocation i) => super.noSuchMethod(i);
}

void main() {
  test('ScheduleController: load/generate/override/publish/refreshViolations '
      'failing after dispose throw nothing', () async {
    final gate = _Gate();
    final ds = _ScheduleDs(gate)..ready = _schedule;
    final ctrl = ScheduleController(ds, _Users());
    await ctrl.load(2026, 11); // a loaded month, so edits and publish run
    ds.ready = null;

    // load last: it clears the month the others act on.
    final calls = <Future<Object?>>[
      ctrl.refreshViolations(),
      ctrl.overrideCell(userId: 7, workDate: DateTime(2026, 11, 2), code: 'A'),
      ctrl.publish(year: 2026, month: 11),
      ctrl.generate(2026, 11),
      ctrl.load(2026, 11),
    ];
    expect(gate.pending, hasLength(5), reason: 'every call reached the server');
    ctrl.dispose();
    await gate.failAll();

    for (final call in calls) {
      await expectLater(call, completes);
    }
  });

  test('ScheduleController: a successful load after dispose throws nothing',
      () async {
    final gate = _Gate();
    final ctrl = ScheduleController(_ScheduleDs(gate), _Users());

    final load = ctrl.load(2026, 11);
    ctrl.dispose();
    gate.answer(_schedule);

    await expectLater(load, completes);
  });

  test('ShiftChangeController: load/submit/decide after dispose throw nothing',
      () async {
    final gate = _Gate();
    final ctrl = ShiftChangeController(_ScheduleDs(gate));

    final load = ctrl.load();
    final submit = ctrl.submit(workDate: DateTime(2026, 11, 2), kind: 'change_code');
    final decide = ctrl.decide(1, 'approved');
    ctrl.dispose();
    gate
      ..answer([_request])
      ..answer(_request)
      ..fail();

    await expectLater(load, completes);
    await expectLater(submit, completes);
    await expectLater(decide, completes);
  });
}
