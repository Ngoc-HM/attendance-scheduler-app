import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/api_endpoints.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/network/api_exception.dart';
import '../../domain/entities/self_arrange_entities.dart';
import '../models/self_arrange_model.dart';

final selfArrangeRemoteDataSourceProvider =
    Provider<SelfArrangeRemoteDataSource>(
  (ref) => SelfArrangeRemoteDataSource(ref.watch(dioProvider)),
);

/// Self-arrange batch API calls (owner 2026-07-09).
class SelfArrangeRemoteDataSource {
  SelfArrangeRemoteDataSource(this._dio);

  final Dio _dio;

  static String _iso(DateTime d) =>
      '${d.year}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

  /// POST /self-arrange — submit the current user's batch proposal.
  Future<SelfArrangeBatch> create({
    required int year,
    required int month,
    required List<SelfArrangeChange> changes,
    String? note,
  }) async {
    try {
      final response = await _dio.post(
        ApiEndpoints.selfArrange,
        data: {
          'year': year,
          'month': month,
          'changes': [
            for (final c in changes)
              {'work_date': _iso(c.workDate), 'code': c.code},
          ],
          if (note != null && note.isNotEmpty) 'note': note,
        },
      );
      return SelfArrangeBatchModel.fromJson(
          response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDio(e, 'self_arrange_create_failed');
    }
  }

  /// GET /self-arrange — own list; `all`/`pending` for the admin view.
  Future<List<SelfArrangeBatch>> list({
    bool all = false,
    bool pendingOnly = false,
  }) async {
    try {
      final response = await _dio.get(
        ApiEndpoints.selfArrange,
        queryParameters: {
          if (all) 'all': true,
          if (all && pendingOnly) 'pending': true,
        },
      );
      final list = response.data as List<dynamic>;
      return list
          .map((e) =>
              SelfArrangeBatchModel.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException.fromDio(e, 'self_arrange_fetch_failed');
    }
  }

  /// POST /self-arrange/{id}/decide — admin approves or rejects.
  Future<SelfArrangeBatch> decide({
    required int id,
    required String status, // "approved" | "rejected"
  }) async {
    try {
      final response = await _dio.post(
        ApiEndpoints.selfArrangeDecide(id),
        data: {'status': status},
      );
      return SelfArrangeBatchModel.fromJson(
          response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDio(e, 'self_arrange_decide_failed');
    }
  }
}
