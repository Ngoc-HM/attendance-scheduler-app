import '../../domain/entities/attendance_entities.dart';

/// JSON → domain entity converters for attendance feature.
class AttendanceRecordModel extends AttendanceRecord {
  const AttendanceRecordModel({
    required super.id,
    required super.userId,
    required super.workDate,
    required super.code,
    super.recordedBy,
    super.note,
  });

  factory AttendanceRecordModel.fromJson(Map<String, dynamic> json) =>
      AttendanceRecordModel(
        id: json['id'] as int,
        userId: json['user_id'] as int,
        workDate: DateTime.parse(json['work_date'] as String),
        code: json['code'] as String,
        recordedBy: json['recorded_by'] as int?,
        note: json['note'] as String?,
      );
}

class SickCoverResultModel extends SickCoverResult {
  const SickCoverResultModel({
    required super.sick,
    required super.forced,
    super.cover,
    super.message,
  });

  factory SickCoverResultModel.fromJson(Map<String, dynamic> json) {
    final sickJson = json['sick'] as Map<String, dynamic>;
    final coverJson = json['cover'] as Map<String, dynamic>?;
    return SickCoverResultModel(
      sick: AttendanceRecordModel.fromJson(sickJson),
      cover: coverJson != null
          ? AttendanceRecordModel.fromJson(coverJson)
          : null,
      forced: json['forced'] as bool? ?? false,
      message: json['message'] as String?,
    );
  }
}

class HolidayModel extends Holiday {
  const HolidayModel({
    required super.id,
    required super.day,
    required super.name,
  });

  factory HolidayModel.fromJson(Map<String, dynamic> json) => HolidayModel(
        id: json['id'] as int,
        day: DateTime.parse(json['day'] as String),
        name: json['name'] as String,
      );
}
