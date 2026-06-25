import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/api_endpoints.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/network/api_exception.dart';
import '../models/flight_day_model.dart';
import '../models/flight_preset_model.dart';

final flightsDataSourceProvider = Provider<FlightsRemoteDataSource>(
  (ref) => FlightsRemoteDataSource(ref.watch(dioProvider)),
);

/// Remote calls for Flights (F-04).
///
/// Mirrors [UserManagementDataSource] style: takes a [Dio] instance, surfaces
/// [ApiException] on failures.
class FlightsRemoteDataSource {
  FlightsRemoteDataSource(this._dio);

  final Dio _dio;

  /// GET /flights/days?year=&month= — list [FlightDayModel] for the month.
  Future<List<FlightDayModel>> listDays(int year, int month) async {
    try {
      final response = await _dio.get(
        ApiEndpoints.flightDays,
        queryParameters: {'year': year, 'month': month},
      );
      return (response.data as List<dynamic>)
          .map((e) => FlightDayModel.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException(
        e.message ?? 'Failed to load flight days',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// PUT /flights/days — manual upsert of flight-pair count for a day.
  Future<FlightDayModel> upsertDay(DateTime day, int flightPairs) async {
    try {
      final response = await _dio.put(
        ApiEndpoints.flightDays,
        data: {
          'day': _formatDate(day),
          'flight_pairs': flightPairs,
        },
      );
      return FlightDayModel.fromJson(
        response.data as Map<String, dynamic>,
      );
    } on DioException catch (e) {
      throw ApiException(
        e.message ?? 'Failed to save flight day',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// POST /flights/import — multipart upload of an .xlsx file.
  ///
  /// Uses [MultipartFile.fromBytes] because [file_picker] on desktop returns
  /// bytes rather than a file path.
  Future<List<FlightModel>> importExcel(PlatformFile file) async {
    try {
      final bytes = file.bytes;
      if (bytes == null) {
        throw const ApiException('File bytes unavailable — re-pick the file');
      }
      final formData = FormData.fromMap({
        'file': MultipartFile.fromBytes(
          bytes,
          filename: file.name,
          contentType: DioMediaType('application', 'vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
        ),
      });
      final response = await _dio.post(ApiEndpoints.flightsImport, data: formData);
      return (response.data as List<dynamic>)
          .map((e) => FlightModel.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException(
        e.message ?? 'Excel import failed',
        statusCode: e.response?.statusCode,
      );
    }
  }

  // ---------------------------------------------------------------------------
  // Preset CRUD
  // ---------------------------------------------------------------------------

  /// GET /flights/presets — list all presets (any active user).
  Future<List<FlightPresetModel>> listPresets() async {
    try {
      final response = await _dio.get(ApiEndpoints.flightPresets);
      return (response.data as List<dynamic>)
          .map((e) => FlightPresetModel.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException(
        e.message ?? 'Failed to load flight presets',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// POST /flights/presets — create a preset (admin only).
  Future<FlightPresetModel> createPreset(FlightPresetModel preset) async {
    try {
      final response = await _dio.post(
        ApiEndpoints.flightPresets,
        data: preset.toJson(),
      );
      return FlightPresetModel.fromJson(
        response.data as Map<String, dynamic>,
      );
    } on DioException catch (e) {
      throw ApiException(
        e.message ?? 'Failed to create flight preset',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// PUT /flights/presets/{id} — update a preset (admin only).
  Future<FlightPresetModel> updatePreset(
    int id,
    FlightPresetModel preset,
  ) async {
    try {
      final response = await _dio.put(
        ApiEndpoints.flightPresetById(id),
        data: preset.toJson(),
      );
      return FlightPresetModel.fromJson(
        response.data as Map<String, dynamic>,
      );
    } on DioException catch (e) {
      throw ApiException(
        e.message ?? 'Failed to update flight preset',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// DELETE /flights/presets/{id} — delete a preset (admin only); returns 204.
  Future<void> deletePreset(int id) async {
    try {
      await _dio.delete(ApiEndpoints.flightPresetById(id));
    } on DioException catch (e) {
      throw ApiException(
        e.message ?? 'Failed to delete flight preset',
        statusCode: e.response?.statusCode,
      );
    }
  }

  // ---------------------------------------------------------------------------
  // Apply presets to a day
  // ---------------------------------------------------------------------------

  /// PUT /flights/days/apply — replace a day's flights with chosen preset ids.
  ///
  /// [presetIds] may be empty (clears the day) or hold 1-2 ids.
  Future<FlightDayModel> applyDay(DateTime day, List<int> presetIds) async {
    try {
      final response = await _dio.put(
        ApiEndpoints.flightsApply,
        data: {
          'day': _formatDate(day),
          'preset_ids': presetIds,
        },
      );
      return FlightDayModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(
        e.message ?? 'Failed to apply flight presets',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// PUT /flights/days/apply-batch — replace multiple days' flights in one call.
  ///
  /// Each item replaces that day's flights with the chosen preset ids; an empty
  /// [presetIds] clears the day.  Returns the updated [FlightDayModel] list.
  Future<List<FlightDayModel>> applyBatch(
    List<({DateTime day, List<int> presetIds})> items,
  ) async {
    try {
      final response = await _dio.put(
        ApiEndpoints.flightsApplyBatch,
        data: {
          'items': items
              .map(
                (e) => {
                  'day': _formatDate(e.day),
                  'preset_ids': e.presetIds,
                },
              )
              .toList(),
        },
      );
      return (response.data as List<dynamic>)
          .map((e) => FlightDayModel.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException(
        e.message ?? 'Failed to apply flight presets (batch)',
        statusCode: e.response?.statusCode,
      );
    }
  }

  static String _formatDate(DateTime d) =>
      '${d.year}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
}
