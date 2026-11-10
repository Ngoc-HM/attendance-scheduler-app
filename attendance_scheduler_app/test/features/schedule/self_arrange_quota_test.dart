// The self-arrange draft check mirrors the backend rule
// (`self_arrange_service._validate_weekly_off`): a full 7-day block keeps
// exactly 2 X; the month's leftover days (29–31) have no quota, the draft
// only may not change how many X they hold (owner 2026-11-10).

import 'package:attendance_scheduler_app/features/schedule/domain/entities/schedule_entities.dart';
import 'package:attendance_scheduler_app/features/schedule/presentation/providers/self_arrange_provider.dart';
import 'package:flutter_test/flutter_test.dart';

/// A 30-day month, all AD except the given off days.
List<ShiftAssignment> _month(Set<int> offDays) => [
  for (var day = 1; day <= 30; day++)
    ShiftAssignment(
      id: day,
      userId: 1,
      workDate: DateTime(2026, 11, day),
      code: offDays.contains(day) ? 'X' : 'AD',
      isManualOverride: false,
    ),
];

// Two X in each full block, none in the leftover days.
const _fullBlocksOnly = {1, 2, 8, 9, 15, 16, 22, 23};

void main() {
  test('leftover days need no day off', () {
    final state = SelfArrangeState(myAssignments: _month(_fullBlocksOnly));

    expect(state.blockOffCounts()[4], (0, 0));
    expect(state.draftKeepsQuota, isTrue);
  });

  test('a plan with a day off in the leftover days is in order too', () {
    final state = SelfArrangeState(
      myAssignments: _month({..._fullBlocksOnly, 29}),
    );

    expect(state.blockOffCounts()[4], (1, 1));
    expect(state.draftKeepsQuota, isTrue);
  });

  test('moving a day off within the leftover days keeps the draft valid', () {
    final state = SelfArrangeState(
      myAssignments: _month({..._fullBlocksOnly, 29}),
      draft: {DateTime(2026, 11, 29): 'AD', DateTime(2026, 11, 30): 'X'},
    );

    expect(state.draftKeepsQuota, isTrue);
  });

  test('adding or removing a day off in the leftover days is refused', () {
    final added = SelfArrangeState(
      myAssignments: _month(_fullBlocksOnly),
      draft: {DateTime(2026, 11, 30): 'X'},
    );
    final removed = SelfArrangeState(
      myAssignments: _month({..._fullBlocksOnly, 29}),
      draft: {DateTime(2026, 11, 29): 'AD'},
    );

    expect(added.blockOffCounts()[4], (1, 0));
    expect(added.draftKeepsQuota, isFalse);
    expect(removed.blockOffCounts()[4], (0, 1));
    expect(removed.draftKeepsQuota, isFalse);
  });

  test('a full block still needs exactly two days off', () {
    final state = SelfArrangeState(
      myAssignments: _month(_fullBlocksOnly),
      draft: {DateTime(2026, 11, 3): 'X'},
    );

    expect(state.blockOffCounts()[0], (3, 2));
    expect(state.draftKeepsQuota, isFalse);
  });
}
