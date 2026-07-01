import 'package:file_picker/file_picker.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../design_system/view_models.dart';
import '../../data/datasources/flights_remote_datasource.dart';
import '../../data/models/flight_day_model.dart';
import '../../data/models/flight_preset_model.dart';

/// State for the flights page: selected month + async list of rows.
class FlightsState {
  const FlightsState({
    required this.month,
    required this.rows,
    this.dayModels = const [],
  });

  final DateTime month;
  final AsyncValue<List<DsFlightRowData>> rows;

  /// Raw [FlightDayModel] list — kept in sync with [rows] so the month-batch
  /// dialog can read preset-state without a second network call.
  final List<FlightDayModel> dayModels;

  FlightsState copyWith({
    DateTime? month,
    AsyncValue<List<DsFlightRowData>>? rows,
    List<FlightDayModel>? dayModels,
  }) =>
      FlightsState(
        month: month ?? this.month,
        rows: rows ?? this.rows,
        dayModels: dayModels ?? this.dayModels,
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
    final result = await AsyncValue.guard(
      () => _ds.listDays(state.month.year, state.month.month),
    );
    state = state.copyWith(
      dayModels: result.valueOrNull ?? const [],
      rows: result.whenData(_toRows),
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

  /// Admin: apply preset ids to [day] then reload.
  Future<void> applyDay(DateTime day, List<int> presetIds) async {
    await _ds.applyDay(day, presetIds);
    await load();
  }

  /// Admin: import from an .xlsx [file] then reload.
  Future<void> importExcel(PlatformFile file) async {
    await _ds.importExcel(file);
    await load();
  }

  /// Admin: apply a batch of day→presets changes (which may span several
  /// months), then show [month] in the page.
  ///
  /// [items] should contain only days whose selection CHANGED vs. the initial
  /// state — the dialog is responsible for diffing.
  Future<void> applyMonth(
    DateTime month,
    List<({DateTime day, List<int> presetIds})> items,
  ) async {
    state = state.copyWith(month: DateTime(month.year, month.month));
    if (items.isNotEmpty) {
      await _ds.applyBatch(items);
    }
    await load();
  }

  // ---------------------------------------------------------------------------
  // Mapping helpers
  // ---------------------------------------------------------------------------

  /// Convert a list of [FlightDayModel] into [DsFlightRowData] rows.
  ///
  /// Builds labels from real [FlightModel] legs:
  ///   - flights: flt numbers joined as "ARR/DEP · ARR/DEP" per pair.
  ///   - arrival: sta values of legs that HAVE sta, joined with " / ".
  ///   - departure: std values of legs that HAVE std, joined with " / ".
  static List<DsFlightRowData> _toRows(List<FlightDayModel> days) {
    return days.map((d) {
      final arrLegs = d.flights.where((f) => f.sta != null).toList();
      final depLegs = d.flights.where((f) => f.std != null).toList();

      // Build flight label by pairing arrival + departure legs by index.
      final String flightsLabel;
      if (d.flights.isEmpty) {
        flightsLabel = '—';
      } else {
        final pairCount = d.flightPairs > 0 ? d.flightPairs : 1;
        final labels = <String>[];
        for (var i = 0; i < pairCount; i++) {
          final arr = i < arrLegs.length ? '${arrLegs[i].fltNumber}' : '?';
          final dep = i < depLegs.length ? '${depLegs[i].fltNumber}' : '?';
          labels.add('$arr/$dep');
        }
        flightsLabel = labels.join(' · ');
      }

      final arrival = arrLegs.isEmpty
          ? '—'
          : arrLegs.map((f) => f.sta!).join(' / ');

      final departure = depLegs.isEmpty
          ? '—'
          : depLegs.map((f) => f.std!).join(' / ');

      return DsFlightRowData(
        date: d.day,
        flightPairs: d.flightPairs,
        flights: flightsLabel,
        arrival: arrival,
        departure: departure,
        status: 'Complete',
      );
    }).toList();
  }
}

final flightsControllerProvider =
    StateNotifierProvider<FlightsController, FlightsState>(
  (ref) => FlightsController(ref.watch(flightsDataSourceProvider)),
);

// ---------------------------------------------------------------------------
// Presets provider
// ---------------------------------------------------------------------------

/// Holds the flight presets list as an [AsyncValue]; exposes CRUD that
/// refreshes the list. Mirrors [UsersController] structure.
class FlightPresetsController
    extends StateNotifier<AsyncValue<List<FlightPresetModel>>> {
  FlightPresetsController(this._ds) : super(const AsyncValue.loading()) {
    load();
  }

  final FlightsRemoteDataSource _ds;

  Future<void> load() async {
    if (!mounted) return;
    state = const AsyncValue.loading();
    final result = await AsyncValue.guard(() => _ds.listPresets());
    if (mounted) state = result;
  }

  Future<void> create(FlightPresetModel preset) async {
    await _ds.createPreset(preset);
    await load();
  }

  Future<void> update(int id, FlightPresetModel preset) async {
    await _ds.updatePreset(id, preset);
    await load();
  }

  Future<void> delete(int id) async {
    await _ds.deletePreset(id);
    await load();
  }
}

final flightPresetsControllerProvider = StateNotifierProvider.autoDispose<
    FlightPresetsController, AsyncValue<List<FlightPresetModel>>>(
  (ref) => FlightPresetsController(ref.watch(flightsDataSourceProvider)),
);
