// E: a failed month batch must not switch the page to the dialog's month
// while the table still holds the previous month's rows.

import 'package:attendance_scheduler_app/core/network/api_exception.dart';
import 'package:attendance_scheduler_app/features/flights/data/datasources/flights_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/flights/data/models/flight_day_model.dart';
import 'package:attendance_scheduler_app/features/flights/presentation/providers/flights_provider.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

class _Flights extends FlightsRemoteDataSource {
  _Flights() : super(Dio());

  final loaded = <(int, int)>[];
  bool failBatch = true;

  @override
  Future<List<FlightDayModel>> listDays(int year, int month) async {
    loaded.add((year, month));
    return const [];
  }

  @override
  Future<List<FlightDayModel>> applyBatch(
    List<({DateTime day, List<int> presetIds})> items,
  ) async {
    if (failBatch) {
      throw const ApiException('Preset 9 not found', statusCode: 404);
    }
    return const [];
  }
}

void main() {
  test('flights_batch_failure_keeps_previous_month', () async {
    final ds = _Flights();
    final ctrl = FlightsController(ds);
    await Future<void>.delayed(Duration.zero);
    final before = ctrl.state.month;
    final other = DateTime(before.year, before.month + 2);

    await expectLater(
      ctrl.applyMonth(other, [
        (day: DateTime(other.year, other.month, 3), presetIds: [9]),
      ]),
      throwsA(isA<ApiException>()),
    );

    expect(ctrl.state.month, before);
    expect(ds.loaded.last, (before.year, before.month));

    // On success the page follows the dialog's month.
    ds.failBatch = false;
    await ctrl.applyMonth(other, [
      (day: DateTime(other.year, other.month, 3), presetIds: [9]),
    ]);
    expect(ctrl.state.month, DateTime(other.year, other.month));
    expect(ds.loaded.last, (other.year, other.month));
  });
}
