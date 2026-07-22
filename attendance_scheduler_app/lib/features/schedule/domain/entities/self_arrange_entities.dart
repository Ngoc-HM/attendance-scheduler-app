import 'package:equatable/equatable.dart';

/// One proposed cell change inside a self-arrange batch (owner 2026-07-09).
class SelfArrangeChange extends Equatable {
  const SelfArrangeChange({required this.workDate, required this.code});

  final DateTime workDate;
  final String code; // raw backend code: 'AD' | 'X' for T/F

  @override
  List<Object?> get props => [workDate, code];
}

/// A batch self-arrange request: employee proposes, admin approves once more.
class SelfArrangeBatch extends Equatable {
  const SelfArrangeBatch({
    required this.id,
    required this.requesterId,
    required this.year,
    required this.month,
    required this.changes,
    required this.status,
    this.note,
    this.decidedAt,
    this.createdAt,
    this.warnings = const [],
  });

  final int id;
  final int requesterId;
  final int year;
  final int month;
  final List<SelfArrangeChange> changes;
  final String status; // pending | approved | rejected
  final String? note;
  final DateTime? decidedAt;
  final DateTime? createdAt;
  final List<String> warnings;

  @override
  List<Object?> get props => [id, requesterId, year, month, changes, status];
}
