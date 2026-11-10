// Admin navigation badges (owner 2026-11-10): only an admin loads the
// counts, a failed load shows no badges, and a decision refreshes them.

import 'package:attendance_scheduler_app/core/network/api_exception.dart';
import 'package:attendance_scheduler_app/core/storage/locale_storage.dart';
import 'package:attendance_scheduler_app/features/auth/data/models/user_model.dart';
import 'package:attendance_scheduler_app/features/auth/domain/entities/user.dart';
import 'package:attendance_scheduler_app/features/auth/domain/repositories/auth_repository.dart';
import 'package:attendance_scheduler_app/features/auth/presentation/providers/auth_provider.dart';
import 'package:attendance_scheduler_app/features/home/data/pending_counts_datasource.dart';
import 'package:attendance_scheduler_app/features/home/presentation/providers/pending_counts_provider.dart';
import 'package:attendance_scheduler_app/features/schedule/data/datasources/schedule_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/schedule/domain/entities/schedule_entities.dart';
import 'package:attendance_scheduler_app/features/schedule/presentation/providers/shift_change_provider.dart';
import 'package:attendance_scheduler_app/features/users/data/user_management_datasource.dart';
import 'package:attendance_scheduler_app/features/users/presentation/providers/users_provider.dart';
import 'package:attendance_scheduler_app/i18n/locale_provider.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

const _admin = User(
  id: 1, username: 'boss', fullName: 'Boss', role: UserRole.m,
  status: 'active', code: 'M1',
);
const _employee = User(
  id: 7, username: 'tuan', fullName: 'Tuan', role: UserRole.t,
  status: 'active', code: 'T1',
);

class _NoopAuthRepository implements AuthRepository {
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class _SignedIn extends AuthController {
  _SignedIn(User user)
    : super(_NoopAuthRepository(), LocaleController(LocaleStorage())) {
    state = AuthState(user: user);
  }
}

/// Answers with [next] (or throws [error]) and counts the calls.
class _FakeCounts extends PendingCountsDataSource {
  _FakeCounts() : super(Dio());

  PendingCounts next = const PendingCounts(leaves: 2, shiftChanges: 1, users: 3);
  Object? error;
  int calls = 0;

  @override
  Future<PendingCounts> fetch() async {
    calls++;
    if (error != null) throw error!;
    return next;
  }
}

class _FakeSchedule extends ScheduleRemoteDataSource {
  _FakeSchedule() : super(Dio());

  @override
  Future<ShiftChangeRequest> decideShiftChange({
    required int id,
    required String status,
  }) async => ShiftChangeRequest(
    id: id, requesterId: 7, workDate: DateTime(2026, 11, 2),
    kind: 'change_code', status: status, strictReview: false,
    warnings: const [],
  );
}

class _FakeUsers extends UserManagementDataSource {
  _FakeUsers() : super(Dio());

  @override
  Future<List<UserModel>> list() async => const [];

  @override
  Future<UserModel> approve(int id, {required String role}) async =>
      UserModel(
        id: id, username: 'new', fullName: 'New', role: UserRole.t,
        status: 'active', code: 'T9',
      );
}

ProviderContainer _container(User user, _FakeCounts counts) {
  final c = ProviderContainer(overrides: [
    authControllerProvider.overrideWith((ref) => _SignedIn(user)),
    pendingCountsDataSourceProvider.overrideWithValue(counts),
    scheduleRemoteDataSourceProvider.overrideWithValue(_FakeSchedule()),
    userManagementDataSourceProvider.overrideWithValue(_FakeUsers()),
  ]);
  addTearDown(c.dispose);
  return c;
}

void main() {
  test('an admin loads the counts', () async {
    final counts = _FakeCounts();
    final c = _container(_admin, counts);

    expect(c.read(pendingCountsProvider), isNull, reason: 'nothing before a load');
    await c.read(pendingCountsProvider.notifier).refresh();

    final state = c.read(pendingCountsProvider)!;
    expect((state.leaves, state.shiftChanges, state.users), (2, 1, 3));
  });

  test('an employee never calls the endpoint and has no counts', () async {
    final counts = _FakeCounts();
    final c = _container(_employee, counts);

    await c.read(pendingCountsProvider.notifier).refresh();

    expect(counts.calls, 0);
    expect(c.read(pendingCountsProvider), isNull);
  });

  test('a failed load clears the counts instead of keeping old numbers',
      () async {
    final counts = _FakeCounts();
    final c = _container(_admin, counts);
    await c.read(pendingCountsProvider.notifier).refresh();
    expect(c.read(pendingCountsProvider), isNotNull);

    counts.error = const ApiException('down', statusCode: 503);
    await c.read(pendingCountsProvider.notifier).refresh();

    expect(c.read(pendingCountsProvider), isNull);
  });

  test('deciding a shift change refreshes the counts', () async {
    final counts = _FakeCounts();
    final c = _container(_admin, counts);
    await c.read(pendingCountsProvider.notifier).refresh();

    counts.next = const PendingCounts(leaves: 2, shiftChanges: 0, users: 3);
    await c.read(shiftChangeControllerProvider.notifier).decide(5, 'approved');
    await pumpEventQueue();

    expect(counts.calls, 2);
    expect(c.read(pendingCountsProvider)!.shiftChanges, 0);
  });

  test('approving a pending account refreshes the counts', () async {
    final counts = _FakeCounts();
    final c = _container(_admin, counts);
    await c.read(pendingCountsProvider.notifier).refresh();
    final sub = c.listen(usersControllerProvider, (_, _) {});
    addTearDown(sub.close);

    counts.next = const PendingCounts(leaves: 2, shiftChanges: 1, users: 2);
    await c.read(usersControllerProvider.notifier).approve(9, UserRole.t);
    await pumpEventQueue();

    expect(counts.calls, 2);
    expect(c.read(pendingCountsProvider)!.users, 2);
  });
}
