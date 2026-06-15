import '../../domain/entities/schedule_entities.dart';

/// Converts backend JSON → domain entities for schedule feature.
class ShiftAssignmentModel extends ShiftAssignment {
  const ShiftAssignmentModel({
    required super.id,
    required super.userId,
    required super.workDate,
    required super.code,
    required super.isManualOverride,
  });

  factory ShiftAssignmentModel.fromJson(Map<String, dynamic> json) =>
      ShiftAssignmentModel(
        id: json['id'] as int,
        userId: json['user_id'] as int,
        workDate: DateTime.parse(json['work_date'] as String),
        code: json['code'] as String,
        isManualOverride: json['is_manual_override'] as bool? ?? false,
      );
}

class MonthlyScheduleModel extends MonthlySchedule {
  const MonthlyScheduleModel({
    required super.id,
    required super.year,
    required super.month,
    required super.status,
    required super.assignments,
    super.generatedAt,
    super.note,
  });

  factory MonthlyScheduleModel.fromJson(Map<String, dynamic> json) {
    final statusStr = json['status'] as String? ?? 'draft';
    final status = statusStr == 'published'
        ? ScheduleStatus.published
        : ScheduleStatus.draft;

    final rawAssignments = json['assignments'] as List<dynamic>? ?? [];
    final assignments = rawAssignments
        .map((e) => ShiftAssignmentModel.fromJson(e as Map<String, dynamic>))
        .toList();

    final generatedAtStr = json['generated_at'] as String?;

    return MonthlyScheduleModel(
      id: json['id'] as int,
      year: json['year'] as int,
      month: json['month'] as int,
      status: status,
      assignments: assignments,
      generatedAt: generatedAtStr != null ? DateTime.parse(generatedAtStr) : null,
      note: json['note'] as String?,
    );
  }
}

class ConstraintViolationModel extends ConstraintViolation {
  const ConstraintViolationModel({
    required super.rule,
    required super.message,
    super.day,
    super.userId,
  });

  factory ConstraintViolationModel.fromJson(Map<String, dynamic> json) {
    final dayStr = json['day'] as String?;
    return ConstraintViolationModel(
      day: dayStr != null ? DateTime.parse(dayStr) : null,
      userId: json['user_id'] as int?,
      rule: json['rule'] as String,
      message: json['message'] as String,
    );
  }
}

class ScheduleResultModel extends ScheduleResult {
  const ScheduleResultModel({
    required super.feasible,
    required super.violations,
    super.schedule,
  });

  factory ScheduleResultModel.fromJson(Map<String, dynamic> json) {
    final rawViolations = json['violations'] as List<dynamic>? ?? [];
    final violations = rawViolations
        .map((e) => ConstraintViolationModel.fromJson(e as Map<String, dynamic>))
        .toList();

    final scheduleJson = json['schedule'] as Map<String, dynamic>?;

    return ScheduleResultModel(
      feasible: json['feasible'] as bool,
      schedule: scheduleJson != null
          ? MonthlyScheduleModel.fromJson(scheduleJson)
          : null,
      violations: violations,
    );
  }
}

class ShiftChangeRequestModel extends ShiftChangeRequest {
  const ShiftChangeRequestModel({
    required super.id,
    required super.requesterId,
    required super.workDate,
    required super.kind,
    required super.status,
    required super.strictReview,
    required super.warnings,
    super.requestedCode,
    super.counterpartUserId,
    super.note,
    super.decidedById,
    super.decidedAt,
  });

  factory ShiftChangeRequestModel.fromJson(Map<String, dynamic> json) {
    final rawWarnings = json['warnings'] as List<dynamic>? ?? [];
    final warnings = rawWarnings.map((e) => e as String).toList();

    final decidedAtStr = json['decided_at'] as String?;

    return ShiftChangeRequestModel(
      id: json['id'] as int,
      requesterId: json['requester_id'] as int,
      workDate: DateTime.parse(json['work_date'] as String),
      kind: json['kind'] as String,
      status: json['status'] as String,
      strictReview: json['strict_review'] as bool? ?? false,
      warnings: warnings,
      requestedCode: json['requested_code'] as String?,
      counterpartUserId: json['counterpart_user_id'] as int?,
      note: json['note'] as String?,
      decidedById: json['decided_by_id'] as int?,
      decidedAt: decidedAtStr != null ? DateTime.parse(decidedAtStr) : null,
    );
  }
}
