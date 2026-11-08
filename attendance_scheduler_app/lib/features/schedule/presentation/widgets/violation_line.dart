import '../../domain/entities/schedule_entities.dart';

/// One line of the admin's violations panel: "{day} · {user} — {message}".
///
/// The date part is skipped when the backend message already starts with
/// that ISO date (e.g. disabled-duty or flight-staffing lines), so the day
/// is never shown twice. [userLabel] is the person's code (or a fallback).
String violationLine(ConstraintViolation v, {String? userLabel}) {
  final day = v.day;
  final iso = day == null
      ? null
      : '${day.year}-${day.month.toString().padLeft(2, '0')}-'
          '${day.day.toString().padLeft(2, '0')}';
  final parts = [
    if (iso != null && !v.message.startsWith(iso)) iso,
    ?userLabel,
  ];
  return parts.isEmpty ? v.message : '${parts.join(' · ')} — ${v.message}';
}
