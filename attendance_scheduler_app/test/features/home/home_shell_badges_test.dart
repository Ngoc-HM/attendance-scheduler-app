// The admin's shell maps the pending counts onto its tabs (owner
// 2026-11-10): Leaves = leaves, Schedule = shift changes, Users = accounts.
// Employees get no badge and never call the endpoint.

import 'package:attendance_scheduler_app/core/storage/locale_storage.dart';
import 'package:attendance_scheduler_app/design_system/design_system.dart';
import 'package:attendance_scheduler_app/features/auth/domain/entities/user.dart';
import 'package:attendance_scheduler_app/features/auth/domain/repositories/auth_repository.dart';
import 'package:attendance_scheduler_app/features/auth/presentation/providers/auth_provider.dart';
import 'package:attendance_scheduler_app/features/home/data/pending_counts_datasource.dart';
import 'package:attendance_scheduler_app/features/home/presentation/pages/home_shell.dart';
import 'package:attendance_scheduler_app/i18n/locale_provider.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

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

class _FakeCounts extends PendingCountsDataSource {
  _FakeCounts() : super(Dio());

  int calls = 0;

  @override
  Future<PendingCounts> fetch() async {
    calls++;
    return const PendingCounts(leaves: 2, shiftChanges: 5, users: 7);
  }
}

Widget _app(UserRole role, _FakeCounts counts, String location) =>
    ProviderScope(
      overrides: [
        authControllerProvider.overrideWith(
          (ref) => _SignedIn(
            User(
              id: 1, username: 'u', fullName: 'U', role: role,
              status: 'active', code: '${role.apiValue}1',
            ),
          ),
        ),
        pendingCountsDataSourceProvider.overrideWithValue(counts),
      ],
      child: MaterialApp(
        theme: AppTheme.light,
        home: HomeShell(location: location, child: const SizedBox.expand()),
      ),
    );

Future<_FakeCounts> _pumpShell(WidgetTester tester, UserRole role) async {
  await tester.binding.setSurfaceSize(const Size(1280, 720));
  addTearDown(() => tester.binding.setSurfaceSize(null));
  final counts = _FakeCounts();
  await tester.pumpWidget(_app(role, counts, '/schedule'));
  await tester.pumpAndSettle();
  return counts;
}

/// The pill's text inside the rail item whose label is [label].
Finder _pillOf(String label) => find.descendant(
  of: find.ancestor(of: find.text(label), matching: find.byType(Row)).first,
  matching: find.byType(DsNavigationCountPill),
);

void main() {
  testWidgets('admin: counts land on Schedule, Leaves and Users', (
    tester,
  ) async {
    final counts = await _pumpShell(tester, UserRole.m);

    expect(counts.calls, 1, reason: 'loaded when the shell first shows');
    expect(find.byType(DsNavigationCountPill), findsNWidgets(3));
    expect(
      find.descendant(of: _pillOf('Schedule'), matching: find.text('5')),
      findsOneWidget,
    );
    expect(
      find.descendant(of: _pillOf('Leaves'), matching: find.text('2')),
      findsOneWidget,
    );
    expect(
      find.descendant(of: _pillOf('Users'), matching: find.text('7')),
      findsOneWidget,
    );
  });

  testWidgets('admin: switching tab and the timer reload the counts', (
    tester,
  ) async {
    final counts = await _pumpShell(tester, UserRole.m);

    await tester.pumpWidget(_app(UserRole.m, counts, '/leaves'));
    await tester.pumpAndSettle();
    expect(counts.calls, 2, reason: 'tab switch');

    await tester.pump(HomeShell.pendingCountsInterval);
    await tester.pumpAndSettle();
    expect(counts.calls, 3, reason: 'timer tick');
  });

  testWidgets('employee: no badge and no call', (tester) async {
    final counts = await _pumpShell(tester, UserRole.t);

    expect(counts.calls, 0);
    expect(find.byType(DsNavigationCountPill), findsNothing);
  });

  testWidgets('the user card shows the person\'s code, not the role', (
    tester,
  ) async {
    await _pumpShell(tester, UserRole.f);

    expect(find.text('F1'), findsOneWidget);
    expect(find.text('F — Flexible'), findsNothing);
  });
}
