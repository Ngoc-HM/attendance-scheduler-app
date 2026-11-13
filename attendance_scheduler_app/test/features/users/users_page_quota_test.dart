// Widget tests for editing a person's annual leave quota from the Users page
// (owner decision D4): every existing user starts at the migration default,
// so the admin must be able to change it per row.

import 'package:attendance_scheduler_app/core/network/api_exception.dart';
import 'package:attendance_scheduler_app/features/auth/data/models/user_model.dart';
import 'package:attendance_scheduler_app/features/auth/domain/entities/user.dart';
import 'package:attendance_scheduler_app/features/users/data/user_management_datasource.dart';
import 'package:attendance_scheduler_app/features/users/presentation/pages/users_page.dart';
import 'package:attendance_scheduler_app/i18n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

/// One active user with a quota of 22 days; records every PATCH.
class _RecordingUserDataSource implements UserManagementDataSource {
  _RecordingUserDataSource({this.updateError});

  /// Thrown by [update] when set.
  final Object? updateError;
  final updates = <(int, Map<String, dynamic>)>[];

  static const _anna = UserModel(
    id: 9,
    username: 'anna',
    fullName: 'Anna',
    role: UserRole.t,
    status: 'active',
    code: 'T4',
    annualLeaveQuota: 22,
  );

  @override
  Future<List<UserModel>> list() async => const [_anna];

  @override
  Future<UserUpdateResult> update(int id, Map<String, dynamic> changes) async {
    if (updateError != null) throw updateError!;
    updates.add((id, changes));
    return const UserUpdateResult(user: _anna, warnings: []);
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
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

/// Opens the row's quota dialog and returns its numeric field.
Future<Finder> _openQuotaDialog(WidgetTester tester) async {
  await tester.tap(find.byTooltip('Actions').first);
  await tester.pumpAndSettle();
  await tester.tap(find.text('Edit leave quota'));
  await tester.pumpAndSettle();
  expect(find.byType(AlertDialog), findsOneWidget);
  return _inDialog(find.byType(TextField));
}

/// Lets the feedback toast's dismiss timer run out before the test ends.
Future<void> _clearToast(WidgetTester tester) =>
    tester.pump(const Duration(seconds: 10));

void main() {
  testWidgets('dialog is prefilled with the current quota and PATCHes the new '
      'one', (tester) async {
    final ds = _RecordingUserDataSource();
    await _pumpUsersPage(tester, ds);

    final field = await _openQuotaDialog(tester);
    expect(tester.widget<TextField>(field).controller!.text, '22');

    await tester.enterText(field, '25');
    await tester.tap(_inDialog(find.text('Save')));
    await tester.pumpAndSettle();

    expect(find.byType(AlertDialog), findsNothing);
    final (id, changes) = ds.updates.single;
    expect(id, 9);
    expect(changes, {'annual_leave_quota': 25});
    expect(find.text('Annual leave quota updated.'), findsOneWidget);
    await _clearToast(tester);
  });

  testWidgets('an empty or out-of-range quota is not sent', (tester) async {
    final ds = _RecordingUserDataSource();
    await _pumpUsersPage(tester, ds);

    final field = await _openQuotaDialog(tester);
    for (final invalid in ['', '366']) {
      await tester.enterText(field, invalid);
      await tester.tap(_inDialog(find.text('Save')));
      await tester.pumpAndSettle();
      expect(find.text('Enter a whole number from 0 to 365.'), findsOneWidget);
    }

    expect(find.byType(AlertDialog), findsOneWidget);
    expect(ds.updates, isEmpty);
  });

  testWidgets('a failed PATCH shows the server message', (tester) async {
    final ds = _RecordingUserDataSource(
      updateError: const ApiException('Quota rejected', statusCode: 422),
    );
    await _pumpUsersPage(tester, ds);

    final field = await _openQuotaDialog(tester);
    await tester.enterText(field, '25');
    await tester.tap(_inDialog(find.text('Save')));
    await tester.pumpAndSettle();

    expect(find.text('Quota rejected'), findsOneWidget);
    expect(find.text('Annual leave quota updated.'), findsNothing);
    await _clearToast(tester);
  });
}
