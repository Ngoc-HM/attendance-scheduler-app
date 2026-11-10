import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/api_endpoints.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/network/api_exception.dart';
import '../../../../core/utils/file_download.dart';
import '../models/flight_day_model.dart';
import '../models/flight_preset_model.dart';

final flightsDataSourceProvider = Provider<FlightsRemoteDataSource>(
  (ref) => FlightsRemoteDataSource(ref.watch(dioProvider)),
);

/// Remote calls for Flights (F-04).
///
/// Mirrors [UserManagementDataSource] style: takes a [Dio] instance, surfaces
/// [ApiException] on failures carrying the backend's (localized) `detail`.
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
      throw ApiException.fromDio(e, 'Failed to load flight days');
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
      throw ApiException.fromDio(e, 'Failed to save flight day');
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
        // Not an API error: the page shows its translated import failure.
        throw StateError('file bytes unavailable');
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
      // `fromDio` keeps the backend's (localized) `detail` — e.g. "file too
      // large" or a bad sheet layout — instead of Dio's generic message.
      throw ApiException.fromDio(e, 'Excel import failed');
    }
  }

  /// GET /flights/template?year=&month= — the month's blank flight plan
  /// (.xlsx) for staff to fill in and upload through [importExcel]. Admin only;
  /// 422 with a translated detail when no active flight preset exists.
  Future<FileDownload> downloadTemplate(int year, int month) async {
    try {
      final response = await _dio.get(
        ApiEndpoints.flightsTemplate,
        queryParameters: {'year': year, 'month': month},
        options: Options(responseType: ResponseType.bytes),
      );
      return FileDownload(
        bytes: response.data as List<int>,
        filename: filenameFromContentDisposition(
          response,
          'flight-plan-$year-${month.toString().padLeft(2, '0')}.xlsx',
        ),
      );
    } on DioException catch (e) {
      // The error body arrives as bytes (responseType.bytes); fromDio
      // decodes it so the user sees the backend's detail.
      throw ApiException.fromDio(e, 'Failed to download the flight template');
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
      throw ApiException.fromDio(e, 'Failed to load flight presets');
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
      throw ApiException.fromDio(e, 'Failed to create flight preset');
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
      throw ApiException.fromDio(e, 'Failed to update flight preset');
    }
  }

  /// DELETE /flights/presets/{id} — delete a preset (admin only); returns 204.
  Future<void> deletePreset(int id) async {
    try {
      await _dio.delete(ApiEndpoints.flightPresetById(id));
    } on DioException catch (e) {
      throw ApiException.fromDio(e, 'Failed to delete flight preset');
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
      throw ApiException.fromDio(e, 'Failed to apply flight presets');
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
      throw ApiException.fromDio(e, 'Failed to apply flight presets (batch)');
    }
  }

  static String _formatDate(DateTime d) =>
      '${d.year}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
}
