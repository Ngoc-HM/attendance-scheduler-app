import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants/api_endpoints.dart';
import '../../../core/network/api_client.dart';
import '../../../core/network/api_exception.dart';

final pendingCountsDataSourceProvider = Provider<PendingCountsDataSource>(
  (ref) => PendingCountsDataSource(ref.watch(dioProvider)),
);

/// How many items wait for an admin decision (owner 2026-11-10): the numbers
/// next to the admin's navigation tabs.
class PendingCounts {
  const PendingCounts({
    required this.leaves,
    required this.shiftChanges,
    required this.users,
  });

  factory PendingCounts.fromJson(Map<String, dynamic> json) => PendingCounts(
    leaves: json['leaves'] as int,
    shiftChanges: json['shift_changes'] as int,
    users: json['users'] as int,
  );

  final int leaves;
  final int shiftChanges;
  final int users;
}

class PendingCountsDataSource {
  PendingCountsDataSource(this._dio);

  final Dio _dio;

  /// GET /pending-counts — admin only.
  Future<PendingCounts> fetch() async {
    try {
      final response = await _dio.get(ApiEndpoints.pendingCounts);
      return PendingCounts.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDio(e, 'Failed to load pending counts');
    }
  }
}
