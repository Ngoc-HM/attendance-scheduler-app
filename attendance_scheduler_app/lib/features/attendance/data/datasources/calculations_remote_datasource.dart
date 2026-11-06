import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/api_endpoints.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/network/api_exception.dart';
import '../../domain/entities/calculations_entities.dart';
import '../models/calculations_model.dart';

final calculationsRemoteDataSourceProvider =
    Provider<CalculationsRemoteDataSource>(
  (ref) => CalculationsRemoteDataSource(ref.watch(dioProvider)),
);

/// Month-close and carry-over API calls (F-14). Admin only — the API re-checks.
class CalculationsRemoteDataSource {
  CalculationsRemoteDataSource(this._dio);

  final Dio _dio;

  /// POST /calculations/{year}/{month}/close — compute and persist every
  /// user's carry-over balances from that month's attendance.
  Future<MonthCloseResult> closeMonth(int year, int month) async {
    try {
      final response = await _dio.post(ApiEndpoints.closeMonth(year, month));
      return MonthCloseResultModel.fromJson(
        response.data as Map<String, dynamic>,
      );
    } on DioException catch (e) {
      throw ApiException.fromDio(e, 'close_month_failed');
    }
  }

  /// GET /calculations/summary — the carry-over balances currently stored for
  /// every user (whatever the last closed month produced).
  Future<List<CarryBalance>> carrySummary() async {
    try {
      final response = await _dio.get(ApiEndpoints.carrySummary);
      return CarryBalanceModel.listFromUserMap(
        response.data as Map<String, dynamic>,
      );
    } on DioException catch (e) {
      throw ApiException.fromDio(e, 'carry_summary_failed');
    }
  }
}
