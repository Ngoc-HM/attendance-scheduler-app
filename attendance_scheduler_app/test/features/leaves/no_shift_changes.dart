// Shared fake: the Leaves page also lists shift-change requests (owner
// 2026-11-20). Tests about leave alone override the schedule data source
// with this one, which has none.

import 'package:attendance_scheduler_app/features/schedule/data/datasources/schedule_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/schedule/domain/entities/schedule_entities.dart';
import 'package:dio/dio.dart';

class NoShiftChanges extends ScheduleRemoteDataSource {
  NoShiftChanges() : super(Dio());

  @override
  Future<List<ShiftChangeRequest>> fetchShiftChanges({bool all = false}) async =>
      const [];
}
