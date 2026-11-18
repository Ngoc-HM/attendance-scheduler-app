import 'package:dio/dio.dart';
import 'package:equatable/equatable.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/api_endpoints.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/network/api_exception.dart';

/// One shift's working-time frame, "HH:MM" on the business clock (decision
/// #71). [derived] marks the double shift (A/D), computed by the server from
/// A and D and never editable.
class ShiftFrame extends Equatable {
  const ShiftFrame({
    required this.code,
    required this.start,
    required this.end,
    this.derived = false,
  });

  final String code;
  final String start;
  final String end;
  final bool derived;

  factory ShiftFrame.fromJson(Map<String, dynamic> json) => ShiftFrame(
    code: json['code'] as String,
    start: json['start'] as String,
    end: json['end'] as String,
    derived: json['derived'] as bool? ?? false,
  );

  @override
  List<Object?> get props => [code, start, end, derived];
}

/// The signed-in person's code today and its frame; [start] and [end] are
/// null for a code without a shift frame (or no code at all).
class ShiftToday {
  const ShiftToday({this.code, this.start, this.end});

  final String? code;
  final String? start;
  final String? end;

  factory ShiftToday.fromJson(Map<String, dynamic> json) => ShiftToday(
    code: json['code'] as String?,
    start: json['start'] as String?,
    end: json['end'] as String?,
  );
}

final shiftTimesRemoteDataSourceProvider = Provider<ShiftTimesRemoteDataSource>(
  (ref) => ShiftTimesRemoteDataSource(ref.watch(dioProvider)),
);

/// Shift time frames: everyone reads, the admin sets A and D.
class ShiftTimesRemoteDataSource {
  ShiftTimesRemoteDataSource(this._dio);

  final Dio _dio;

  Future<List<ShiftFrame>> fetch() async {
    try {
      final res = await _dio.get(ApiEndpoints.shiftTimes);
      return [
        for (final e in res.data as List)
          ShiftFrame.fromJson(e as Map<String, dynamic>),
      ];
    } on DioException catch (e) {
      throw ApiException.fromDio(e, 'Failed to load shift times');
    }
  }

  /// Saves A and D; returns every frame, the derived A/D included.
  Future<List<ShiftFrame>> save(List<ShiftFrame> frames) async {
    try {
      final res = await _dio.put(
        ApiEndpoints.shiftTimes,
        data: {
          'frames': [
            for (final f in frames)
              {'code': f.code, 'start': f.start, 'end': f.end},
          ],
        },
      );
      return [
        for (final e in res.data as List)
          ShiftFrame.fromJson(e as Map<String, dynamic>),
      ];
    } on DioException catch (e) {
      throw ApiException.fromDio(e, 'Failed to save shift times');
    }
  }

  Future<ShiftToday> today() async {
    try {
      final res = await _dio.get(ApiEndpoints.shiftToday);
      return ShiftToday.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDio(e, "Failed to load today's shift");
    }
  }
}
