import '../../domain/entities/self_arrange_entities.dart';

/// JSON parsing for self-arrange batches (mirrors `schemas/self_arrange.py`).
class SelfArrangeBatchModel extends SelfArrangeBatch {
  const SelfArrangeBatchModel({
    required super.id,
    required super.requesterId,
    required super.year,
    required super.month,
    required super.changes,
    required super.status,
    super.note,
    super.decidedAt,
    super.createdAt,
    super.warnings,
  });

  factory SelfArrangeBatchModel.fromJson(Map<String, dynamic> json) {
    return SelfArrangeBatchModel(
      id: json['id'] as int,
      requesterId: json['requester_id'] as int,
      year: json['year'] as int,
      month: json['month'] as int,
      changes: (json['changes'] as List<dynamic>)
          .map(
            (e) => SelfArrangeChange(
              workDate: DateTime.parse(
                (e as Map<String, dynamic>)['work_date'] as String,
              ),
              code: e['code'] as String,
            ),
          )
          .toList(),
      status: json['status'] as String,
      note: json['note'] as String?,
      decidedAt: json['decided_at'] != null
          ? DateTime.parse(json['decided_at'] as String)
          : null,
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'] as String)
          : null,
      warnings: (json['warnings'] as List<dynamic>? ?? const [])
          .map((e) => e.toString())
          .toList(),
    );
  }
}
