// Widget tests for approving a pending account on the Users page (F-03):
// the admin picks the role in a dialog, defaulting to the account's role.

import 'package:attendance_scheduler_app/features/auth/data/models/user_model.dart';
import 'package:attendance_scheduler_app/features/auth/domain/entities/user.dart';
import 'package:attendance_scheduler_app/features/users/data/user_management_datasource.dart';
import 'package:attendance_scheduler_app/features/users/presentation/pages/users_page.dart';
import 'package:attendance_scheduler_app/i18n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

/// One pending account whose role is F, so the test can tell "defaults to
/// the account's role" apart from "defaults to T".
class _RecordingUserDataSource implements UserManagementDataSource {
  final approvals = <(int, String)>[];

  static const _pending = UserModel(
    id: 7,
    username: 'longg',
    fullName: 'Long',
    role: UserRole.f,
    status: 'pending',
    code: 'F4',
  );

  @override
  Future<List<UserModel>> list() async => const [_pending];

  @override
  Future<UserModel> approve(int id, {required String role}) async {
    approvals.add((id, role));
    return _pending;
  }

  @override
  Future<UserModel> create({
    required String username,
    required String fullName,
    required String password,
    required String role,
  }) async => throw UnimplementedError();

  @override
  Future<UserUpdateResult> update(int id, Map<String, dynamic> changes) async =>
      throw UnimplementedError();

  @override
  Future<void> delete(int id) async {}
}

Future<void> _pumpUsersPage(
  WidgetTester tester,
  _RecordingUserDataSource ds,
) async {
  await tester.binding.setSurfaceSize(const Size(1400, 1000));
  addTearDown(() => tester.binding.setSurfaceSize(null));
  await tester.pumpWidget(
    ProviderScope(
      overrides: [userManagementDataSourceProvider.overrideWithValue(ds)],
      child: MaterialApp(
        localizationsDelegates: const [
          AppLocalizations.delegate,
          DefaultMaterialLocalizations.delegate,
          DefaultWidgetsLocalizations.delegate,
        ],
        supportedLocales: AppLocalizations.supportedLocales,
        locale: const Locale('en'),
        home: const Scaffold(body: UsersPage()),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

Finder _inDialog(Finder finder) =>
    find.descendant(of: find.byType(AlertDialog), matching: finder);

Future<void> _openApproveDialog(WidgetTester tester) async {
  await tester.tap(find.text('Approve'));
  await tester.pumpAndSettle();
  expect(find.byType(AlertDialog), findsOneWidget);
}

void main() {
  testWidgets('approve defaults to the pending account role', (tester) async {
    final ds = _RecordingUserDataSource();
    await _pumpUsersPage(tester, ds);

    await _openApproveDialog(tester);
    expect(_inDialog(find.text('F — Flexible')), findsOneWidget);

    await tester.tap(_inDialog(find.text('Approve')));
    await tester.pumpAndSettle();

    expect(ds.approvals, [(7, 'F')]);
  });

  testWidgets('approve sends the role the admin picks', (tester) async {
    final ds = _RecordingUserDataSource();
    await _pumpUsersPage(tester, ds);

    await _openApproveDialog(tester);
    await tester.tap(_inDialog(find.text('F — Flexible')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('A — Fixed').last);
    await tester.pumpAndSettle();
    await tester.tap(_inDialog(find.text('Approve')));
    await tester.pumpAndSettle();

    expect(ds.approvals, [(7, 'A')]);
  });

  testWidgets('cancelling the approve dialog approves nothing', (tester) async {
    final ds = _RecordingUserDataSource();
    await _pumpUsersPage(tester, ds);

    await _openApproveDialog(tester);
    await tester.tap(_inDialog(find.text('Cancel')));
    await tester.pumpAndSettle();

    expect(find.byType(AlertDialog), findsNothing);
    expect(ds.approvals, isEmpty);
  });
}
