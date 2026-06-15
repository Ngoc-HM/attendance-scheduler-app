import 'package:equatable/equatable.dart';

/// A single recorded attendance entry.
class AttendanceRecord extends Equatable {
  const AttendanceRecord({
    required this.id,
    required this.userId,
    required this.workDate,
    required this.code,
    this.recordedBy,
    this.note,
  });

  final int id;
  final int userId;
  final DateTime workDate;
  final String code; // raw backend code string
  final int? recordedBy;
  final String? note;

  @override
  List<Object?> get props => [id, userId, workDate, code];
}

/// Result of POST /attendance/sick-cover.
class SickCoverResult extends Equatable {
  const SickCoverResult({
    required this.sick,
    required this.forced,
    this.cover,
    this.message,
  });

  final AttendanceRecord sick;
  final AttendanceRecord? cover;
  final bool forced;
  final String? message;

  @override
  List<Object?> get props => [sick, cover, forced, message];
}

/// A public holiday entry (F-13).
class Holiday extends Equatable {
  const Holiday({
    required this.id,
    required this.day,
    required this.name,
  });

  final int id;
  final DateTime day;
  final String name;

  @override
  List<Object?> get props => [id, day, name];
}
