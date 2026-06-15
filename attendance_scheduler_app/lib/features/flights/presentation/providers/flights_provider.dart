import 'package:file_picker/file_picker.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../design_system/view_models.dart';
import '../../data/datasources/flights_remote_datasource.dart';
import '../../data/models/flight_day_model.dart';

/// State for the flights page: selected month + async list of rows.
class FlightsState {
  const FlightsState({
    required this.month,
    required this.rows,
  });

  final DateTime month;
  final AsyncValue<List<DsFlightRowData>> rows;

  FlightsState copyWith({
    DateTime? month,
    AsyncValue<List<DsFlightRowData>>? rows,
  }) =>
      FlightsState(
        month: month ?? this.month,
        rows: rows ?? this.rows,
      );
}

class FlightsController extends StateNotifier<FlightsState> {
  FlightsController(this._ds)
      : super(
          FlightsState(
            month: DateTime(DateTime.now().year, DateTime.now().month),
            rows: const AsyncValue.loading(),
          ),
        ) {
    load();
  }

  final FlightsRemoteDataSource _ds;

  Future<void> load() async {
    state = state.copyWith(rows: const AsyncValue.loading());
    state = state.copyWith(
      rows: await AsyncValue.guard(
        () => _ds.listDays(state.month.year, state.month.month).then(_toRows),
      ),
    );
  }

  void previousMonth() {
    state = state.copyWith(
      month: DateTime(state.month.year, state.month.month - 1),
    );
    load();
  }

  void nextMonth() {
    state = state.copyWith(
      month: DateTime(state.month.year, state.month.month + 1),
    );
    load();
  }

  /// Admin: upsert flight-pair count for [day] then reload.
  Future<void> upsertDay(DateTime day, int flightPairs) async {
    await _ds.upsertDay(day, flightPairs);
    await load();
  }

  /// Admin: import from an .xlsx [file] then reload.
  Future<void> importExcel(PlatformFile file) async {
    await _ds.importExcel(file);
    await load();
  }

  // ---------------------------------------------------------------------------
  // Mapping helpers
  // ---------------------------------------------------------------------------

  /// Convert a list of [FlightDayModel] into [DsFlightRowData] rows.
  ///
  /// The design system view needs STA/STD strings — these come from the
  /// detailed [FlightModel] list (GET /flights) which is not yet wired;
  /// for now we populate them from the FlightDay data only.
  static List<DsFlightRowData> _toRows(List<FlightDayModel> days) {
    return days.map((d) {
      final pairsLabel = switch (d.flightPairs) {
        2 => 'VN37/VN36 · VN31/VN30',
        1 => 'VN37/VN36',
        _ => '—',
      };
      return DsFlightRowData(
        date: d.day,
        flightPairs: d.flightPairs,
        flights: pairsLabel,
        arrival: '—',
        departure: '—',
        status: 'Complete',
      );
    }).toList();
  }
}

final flightsControllerProvider =
    StateNotifierProvider<FlightsController, FlightsState>(
  (ref) => FlightsController(ref.watch(flightsDataSourceProvider)),
);
