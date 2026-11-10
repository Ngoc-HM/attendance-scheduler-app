// The self-arrange draft check mirrors the backend rule (owner 2026-11-10):
// days off may be moved, never added or removed, and the draft must not
// create a run of 7 days with more than 5 working days.

import 'package:attendance_scheduler_app/features/schedule/domain/entities/schedule_entities.dart';
import 'package:attendance_scheduler_app/features/schedule/presentation/providers/self_arrange_provider.dart';
import 'package:flutter_test/flutter_test.dart';

/// A 30-day month, all AD except the given off days.
List<ShiftAssignment> _month(
  Set<int> offDays, {
  Map<int, String> other = const {},
}) => [
  for (var day = 1; day <= 30; day++)
    ShiftAssignment(
      id: day,
      userId: 1,
      workDate: DateTime(2026, 11, day),
      code: other[day] ?? (offDays.contains(day) ? 'X' : 'AD'),
      isManualOverride: false,
    ),
];

DateTime _d(int day) => DateTime(2026, 11, day);

// Fri+Sat off every week (1 Nov 2026 is a Sunday): 5 on, 2 off.
const _friSat = {6, 7, 13, 14, 20, 21, 27, 28};

void main() {
  test('an untouched plan is in order', () {
    final state = SelfArrangeState(myAssignments: _month(_friSat));

    expect(state.monthOffCount(), (8, 8));
    expect(state.draftKeepsQuota, isTrue);
  });

  test('moving a pair of days off keeps the draft valid', () {
    // Thu+Fri instead of Fri+Sat in the last week.
    final state = SelfArrangeState(
      myAssignments: _month(_friSat),
      draft: {_d(26): 'X', _d(28): 'AD'},
    );

    expect(state.monthOffCount(), (8, 8));
    expect(state.draftKeepsQuota, isTrue);
  });

  test('adding or removing a day off is refused', () {
    final added = SelfArrangeState(
      myAssignments: _month(_friSat),
      draft: {_d(10): 'X'},
    );
    final removed = SelfArrangeState(
      myAssignments: _month(_friSat),
      draft: {_d(13): 'AD'},
    );

    expect(added.monthOffCount(), (9, 8));
    expect(added.draftKeepsQuota, isFalse);
    expect(removed.monthOffCount(), (7, 8));
    expect(removed.draftKeepsQuota, isFalse);
  });

  test('a move that leaves more than 5 working days in 7 is refused', () {
    // Day off moved from the 13th to the 29th: 8..12 and 14..19 are worked,
    // so the 7 days 14–20 hold 6 working days.
    final state = SelfArrangeState(
      myAssignments: _month({6, 7, 13, 14, 21, 22, 27, 28}),
      draft: {_d(14): 'AD', _d(29): 'X'},
    );

    expect(state.monthOffCount(), (8, 8));
    expect(state.draftKeepsQuota, isFalse);
  });

  test('leave and sick days count as rest, not as days off to move', () {
    final state = SelfArrangeState(
      myAssignments: _month(
        {6, 7, 20, 21, 27, 28},
        other: {13: 'AL', 14: 'AL'},
      ),
    );

    expect(state.monthOffCount(), (6, 6));
    expect(state.draftKeepsQuota, isTrue);
  });

  test('a problem the plan already had does not block other moves', () {
    // The plan itself has 6 working days in 1–7; the draft touches the
    // last week only.
    final state = SelfArrangeState(
      myAssignments: _month({7, 13, 14, 20, 21, 27, 28, 30}),
      draft: {_d(26): 'X', _d(28): 'AD'},
    );

    expect(state.draftKeepsQuota, isTrue);
  });
}
