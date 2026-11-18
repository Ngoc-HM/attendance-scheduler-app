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
    this.carried = false,
  });

  final int id;
  final int userId;
  final DateTime workDate;
  final String code; // raw backend code, e.g. "A", "D", "A/D", "X"
  final bool isManualOverride;

  /// Planned by the previous month's generation: a month's roster runs to
  /// the Sunday that ends its last week (owner 2026-11-18).
  final bool carried;

  @override
  List<Object?> get props => [
    id,
    userId,
    workDate,
    code,
    isManualOverride,
    carried,
  ];
}

/// The full monthly schedule with all assignments.
class MonthlySchedule extends Equatable {
  const MonthlySchedule({
    required this.id,
    required this.year,
    required this.month,
    required this.status,
    required this.assignments,
    this.carryAssignments = const [],
    this.generatedAt,
    this.note,
  });

  final int id;
  final int year;
  final int month;
  final ScheduleStatus status;
  final List<ShiftAssignment> assignments;

  /// The next month's carried cells this month's generation planned (its
  /// days up to the Sunday that ends this month's last week).
  final List<ShiftAssignment> carryAssignments;
  final DateTime? generatedAt;
  final String? note;

  bool get isPublished => status == ScheduleStatus.published;

  /// Only the carried days of the previous month's run: not generated yet.
  bool get isCarryOnly =>
      assignments.isNotEmpty && assignments.every((a) => a.carried);

  /// The next month's days shown after this month's last day.
  List<DateTime> get carryDays {
    final days = {
      for (final a in carryAssignments)
        if (a.workDate.year != year || a.workDate.month != month)
          DateTime(a.workDate.year, a.workDate.month, a.workDate.day),
    }.toList()..sort();
    return days;
  }

  /// True when [day] is a row of this month's roster: one of its own days or
  /// a carried day after it.
  bool shows(DateTime day) =>
      (day.year == year && day.month == month) ||
      carryDays.any(
        (d) => d.year == day.year && d.month == day.month && d.day == day.day,
      );

  @override
  List<Object?> get props => [
    id,
    year,
    month,
    status,
    assignments,
    carryAssignments,
  ];
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
    this.nextMonthWarnings = const [],
  });

  final bool feasible;
  final MonthlySchedule? schedule;
  final List<ConstraintViolation> violations;

  /// Generate only: rule breaches this roster creates in the following
  /// month, which already has a schedule ("YYYY-MM: message").
  final List<String> nextMonthWarnings;

  @override
  List<Object?> get props => [
    feasible,
    schedule,
    violations,
    nextMonthWarnings,
  ];
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
    this.counterpartStatus,
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

  /// swap_with only: the colleague's own answer ("pending" | "approved" |
  /// "rejected"); the admin decides once it is "approved". Null for a code
  /// change.
  final String? counterpartStatus;

  @override
  List<Object?> get props => [
    id,
    requesterId,
    workDate,
    kind,
    status,
    counterpartStatus,
  ];
}
