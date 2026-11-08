// Leaves loads race with Refresh and with logout (Task 11 invalidates the
// provider mid-load): the newest load wins, and a load that finishes after
// the controller was disposed stores nothing and throws nothing.

import 'dart:async';

import 'package:attendance_scheduler_app/core/storage/locale_storage.dart';
import 'package:attendance_scheduler_app/features/auth/domain/entities/user.dart';
import 'package:attendance_scheduler_app/features/auth/domain/repositories/auth_repository.dart';
import 'package:attendance_scheduler_app/features/auth/presentation/providers/auth_provider.dart';
import 'package:attendance_scheduler_app/features/leaves/data/datasources/leaves_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/leaves/data/models/leave_model.dart';
import 'package:attendance_scheduler_app/features/leaves/presentation/providers/leaves_provider.dart';
import 'package:attendance_scheduler_app/i18n/locale_provider.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

class _Noop implements AuthRepository {
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class _SignedIn extends AuthController {
  _SignedIn(User user) : super(_Noop(), LocaleController(LocaleStorage())) {
    state = AuthState(user: user);
  }
}

/// Each listOwn() call waits for the test to complete its own completer.
class _GatedLeaves implements LeavesRemoteDataSource {
  final calls = <Completer<List<LeaveModel>>>[];

  @override
  Future<List<LeaveModel>> listOwn() {
    final completer = Completer<List<LeaveModel>>();
    calls.add(completer);
    return completer.future;
  }

  @override
  Future<LeaveWindow> fetchWindow() async => const LeaveWindow(
    monthlyOpen: true,
    monthlyTargetYear: 2026,
    monthlyTargetMonth: 12,
    annualTargetYear: 2027,
    closesOnDay: 20,
    enforced: true,
  );

  @override
  Future<AnnualLeaveBalance> fetchBalance({int? year}) async =>
      const AnnualLeaveBalance(
        year: 2026,
        quota: 30,
        used: 0,
        pending: 0,
        remaining: 30,
      );

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

const _anna = User(
  id: 7,
  username: 'anna',
  fullName: 'Anna',
  role: UserRole.t,
  status: 'active',
  code: 'T3',
);

LeaveModel _leave(int id) => LeaveModel(
  id: id,
  userId: 7,
  startDate: DateTime(2026, 12, id),
  endDate: DateTime(2026, 12, id),
  leaveType: 'monthly',
  status: 'pending',
);

ProviderContainer _container(_GatedLeaves leaves) => ProviderContainer(
  overrides: [
    authControllerProvider.overrideWith((ref) => _SignedIn(_anna)),
    leavesDataSourceProvider.overrideWithValue(leaves),
  ],
);

void main() {
  test('a newer load wins over an older, slower one', () async {
    final leaves = _GatedLeaves();
    final container = _container(leaves);
    addTearDown(container.dispose);
    final ctrl = container.read(leavesControllerProvider.notifier);

    final first = ctrl.load();
    final refresh = ctrl.load();
    await Future<void>.delayed(Duration.zero);
    expect(leaves.calls, hasLength(2));

    leaves.calls[1].complete([_leave(2)]);
    await refresh;
    leaves.calls[0].complete([_leave(1)]);
    await first;

    final ids = container
        .read(leavesControllerProvider)
        .entries
        .requireValue
        .map((e) => e.id);
    expect(ids, [2]);
  });

  test('a load finishing after dispose stores nothing and throws nothing', () async {
    final leaves = _GatedLeaves();
    final container = _container(leaves);
    final ctrl = container.read(leavesControllerProvider.notifier);

    final pending = ctrl.load();
    await Future<void>.delayed(Duration.zero);
    container.dispose();
    leaves.calls.single.complete([_leave(1)]);

    await expectLater(pending, completes);
    expect(ctrl.mounted, isFalse);
  });
}
