// Violations panel lines (review 2026-11-08, Task 7): the date is shown once
// even when the backend message already starts with it.

import 'package:attendance_scheduler_app/features/schedule/domain/entities/schedule_entities.dart';
import 'package:attendance_scheduler_app/features/schedule/presentation/widgets/violation_line.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('message that starts with the ISO day shows the date once', () {
    final line = violationLine(
      ConstraintViolation(
        rule: 'disabled_user_duty',
        message: '2052-03-10: Disabled account still has a working shift (A/D)',
        day: DateTime(2052, 3, 10),
        userId: 7,
      ),
      userLabel: 'A1',
    );
    expect(
      line,
      'A1 — 2052-03-10: Disabled account still has a working shift (A/D)',
    );
    expect('2052-03-10'.allMatches(line).length, 1);
  });

  test('message without the date keeps the date prefix', () {
    final line = violationLine(
      ConstraintViolation(
        rule: 'min_a_days',
        message: 'User 7: only 1 A-duty day(s) in the month (minimum 2)',
        day: DateTime(2052, 3, 10),
        userId: 7,
      ),
      userLabel: 'A1',
    );
    expect(
      line,
      '2052-03-10 · A1 — User 7: only 1 A-duty day(s) in the month (minimum 2)',
    );
  });

  test('no day and no user: just the message', () {
    expect(
      violationLine(const ConstraintViolation(rule: 'r', message: 'm')),
      'm',
    );
  });
}
