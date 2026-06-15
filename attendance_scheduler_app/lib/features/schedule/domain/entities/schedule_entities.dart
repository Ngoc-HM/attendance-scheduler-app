import 'package:equatable/equatable.dart';

/// Schedule status values from the backend ScheduleStatus enum.
enum ScheduleStatus { draft, published }

/// A single day/user assignment inside a monthly schedule.
class ShiftAssignment extends Equatable {
  const ShiftAssignment({
    required this.id,
    required this.userId,
    required this.workDate,
    required this.code,
    required this.isManualOverride,
  });

  final int id;
  final int userId;
  final DateTime workDate;
  final String code; // raw backend code, e.g. "A", "D", "A/D", "X"
  final bool isManualOverride;

  @override
  List<Object?> get props => [id, userId, workDate, code, isManualOverride];
}

/// The full monthly schedule with all assignments.
class MonthlySchedule extends Equatable {
  const MonthlySchedule({
    required this.id,
    required this.year,
    required this.month,
    required this.status,
    required this.assignments,
    this.generatedAt,
    this.note,
  });

  final int id;
  final int year;
  final int month;
  final ScheduleStatus status;
  final List<ShiftAssignment> assignments;
  final DateTime? generatedAt;
  final String? note;

  bool get isPublished => status == ScheduleStatus.published;

  @override
  List<Object?> get props => [id, year, month, status, assignments];
}

/// A hard-constraint violation reported by the solver.
class ConstraintViolation extends Equatable {
  const ConstraintViolation({
    required this.rule,
    required this.message,
    this.day,
    this.userId,
  });

  final DateTime? day;
  final int? userId;
  final String rule;
  final String message;

  @override
  List<Object?> get props => [day, userId, rule, message];
}

/// Result of a schedule generation run.
class ScheduleResult extends Equatable {
  const ScheduleResult({
    required this.feasible,
    required this.violations,
    this.schedule,
  });

  final bool feasible;
  final MonthlySchedule? schedule;
  final List<ConstraintViolation> violations;

  @override
  List<Object?> get props => [feasible, schedule, violations];
}

/// A shift-change request (decision #8).
class ShiftChangeRequest extends Equatable {
  const ShiftChangeRequest({
    required this.id,
    required this.requesterId,
    required this.workDate,
    required this.kind,
    required this.status,
    required this.strictReview,
    required this.warnings,
    this.requestedCode,
    this.counterpartUserId,
    this.note,
    this.decidedById,
    this.decidedAt,
  });

  final int id;
  final int requesterId;
  final DateTime workDate;
  final String kind; // "change_code" | "swap_with"
  final String status; // "pending" | "approved" | "rejected"
  final bool strictReview;
  final List<String> warnings;
  final String? requestedCode;
  final int? counterpartUserId;
  final String? note;
  final int? decidedById;
  final DateTime? decidedAt;

  @override
  List<Object?> get props => [id, requesterId, workDate, kind, status];
}
