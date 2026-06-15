/// Data model: maps backend [LeaveRead] JSON → domain data used by the UI.
///
/// Backend shape:
///   { "id": int, "user_id": int, "start_date": "YYYY-MM-DD",
///     "end_date": "YYYY-MM-DD", "leave_type": "monthly"|"annual",
///     "status": "pending"|"approved"|"rejected", "note": str|null }
class LeaveModel {
  const LeaveModel({
    required this.id,
    required this.userId,
    required this.startDate,
    required this.endDate,
    required this.leaveType,
    required this.status,
    this.note,
  });

  final int id;
  final int userId;
  final DateTime startDate;
  final DateTime endDate;
  final String leaveType; // "monthly" | "annual"
  final String status;    // "pending" | "approved" | "rejected"
  final String? note;

  factory LeaveModel.fromJson(Map<String, dynamic> json) => LeaveModel(
    id: json['id'] as int,
    userId: json['user_id'] as int,
    startDate: DateTime.parse(json['start_date'] as String),
    endDate: DateTime.parse(json['end_date'] as String),
    leaveType: json['leave_type'] as String? ?? 'monthly',
    status: json['status'] as String? ?? 'pending',
    note: json['note'] as String?,
  );

  /// Number of calendar days (inclusive both ends).
  int get days =>
      endDate.difference(startDate).inDays + 1;

  /// Human-readable date range: "DD/MM–DD/MM/YYYY".
  String get dateRange {
    String two(int v) => v.toString().padLeft(2, '0');
    if (startDate.year == endDate.year && startDate.month == endDate.month) {
      return '${two(startDate.day)}–${two(endDate.day)}/${two(endDate.month)}/${endDate.year}';
    }
    return '${two(startDate.day)}/${two(startDate.month)}–'
        '${two(endDate.day)}/${two(endDate.month)}/${endDate.year}';
  }

  /// Display label for [leaveType].
  String get typeLabel => switch (leaveType) {
    'monthly' => 'Monthly leave',
    'annual' => 'Annual leave',
    _ => leaveType,
  };

  /// Capitalised status for [DsLeaveRowData].
  String get statusDisplay => switch (status) {
    'pending' => 'Pending',
    'approved' => 'Approved',
    'rejected' => 'Rejected',
    _ => status,
  };
}
