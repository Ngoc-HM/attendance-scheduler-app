// Widget tests for the holiday and user create dialog guards (CSV TC-009, TC-013).

import 'package:attendance_scheduler_app/core/network/api_exception.dart';
import 'package:attendance_scheduler_app/features/attendance/data/datasources/attendance_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/attendance/domain/entities/attendance_entities.dart';
import 'package:attendance_scheduler_app/features/attendance/presentation/pages/holidays_page.dart';
import 'package:attendance_scheduler_app/features/auth/data/models/user_model.dart';
import 'package:attendance_scheduler_app/features/auth/domain/entities/user.dart';
import 'package:attendance_scheduler_app/features/users/data/user_management_datasource.dart';
import 'package:attendance_scheduler_app/features/users/presentation/widgets/create_user_dialog.dart';
import 'package:attendance_scheduler_app/i18n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

Widget _wrap(Widget child, {required List<Override> overrides}) {
  return ProviderScope(
    overrides: overrides,
    child: MaterialApp(
      localizationsDelegates: const [
        AppLocalizations.delegate,
        DefaultMaterialLocalizations.delegate,
        DefaultWidgetsLocalizations.delegate,
      ],
      supportedLocales: AppLocalizations.supportedLocales,
      locale: const Locale('en'),
      home: Scaffold(body: child),
    ),
  );
}

class _StubUserDataSource implements UserManagementDataSource {
  _StubUserDataSource({this.createException});

  final Object? createException;

  /// (username, annual leave quota sent with POST /users).
  final created = <(String, int?)>[];

  @override
  Future<UserModel> create({
    required String username,
    required String fullName,
    required String password,
    required String role,
    int? annualLeaveQuota,
  }) async {
    if (createException != null) throw createException!;
    created.add((username, annualLeaveQuota));
    return UserModel(
      id: 41,
      username: username,
      fullName: fullName,
      role: UserRoleX.fromApi(role),
      status: 'active',
      code: 'T1',
    );
  }

  @override
  Future<List<UserModel>> list() async => const [];
  @override
  Future<List<UserDirectoryEntry>> directory() async => const [];
  @override
  Future<UserModel> approve(int id, {required String role}) async =>
      throw UnimplementedError();
  /// Creating a user is a single POST: any PATCH here is a regression.
  @override
  Future<UserUpdateResult> update(int id, Map<String, dynamic> changes) async =>
      throw UnimplementedError();

  @override
  Future<void> delete(int id) async {}
}

/// Fills the create-user form; [quota] goes in the annual leave quota field.
Future<void> _fillCreateForm(WidgetTester tester, {String quota = ''}) async {
  await tester.enterText(find.byType(TextField).at(0), 'long');
  await tester.enterText(find.byType(TextField).at(1), 'Long');
  await tester.enterText(find.byType(TextField).at(2), 'secret1');
  await tester.enterText(
    find.widgetWithText(TextField, 'Annual leave quota'),
    quota,
  );
}

class _NoopAttendanceDataSource implements AttendanceRemoteDataSource {
  @override
  noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  group('HolidaysPage', () {
    testWidgets('lists the year and enables Add once date and name are set', (
      tester,
    ) async {
      await tester.binding.setSurfaceSize(const Size(1100, 800));
      addTearDown(() => tester.binding.setSurfaceSize(null));
      await tester.pumpWidget(
        _wrap(
          const HolidaysPage(),
          overrides: [
            holidaysProvider.overrideWith(
              (ref, year) async =>
                  [Holiday(id: 1, day: DateTime(year, 1, 1), name: 'New Year')],
            ),
            attendanceRemoteDataSourceProvider.overrideWithValue(
              _NoopAttendanceDataSource(),
            ),
          ],
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('New Year'), findsOneWidget);
      FilledButton button() =>
          tester.widgetList<FilledButton>(find.byType(FilledButton)).first;
      expect(button().onPressed, isNull);

      await tester.tap(find.text('Pick a date'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('OK'));
      await tester.pumpAndSettle();
      expect(button().onPressed, isNull); // still no name

      await tester.enterText(find.byType(TextField).first, 'Reichstag');
      await tester.pump();
      expect(button().onPressed, isNotNull);
    });
  });

  group('CreateUserDialog', () {
    setUp(() {
      // The dialog uses an inline alert that adds vertical space; bump the
      // surface so the column doesn't overflow in the default test viewport.
    });

    testWidgets('shows the backend detail on 409', (tester) async {
      await tester.binding.setSurfaceSize(const Size(800, 900));
      addTearDown(() => tester.binding.setSurfaceSize(null));
      final ds = _StubUserDataSource(
        createException: const ApiException(
          'Backend says: username "long" is taken.',
          statusCode: 409,
        ),
      );

      await tester.pumpWidget(
        _wrap(
          const CreateUserDialog(),
          overrides: [userManagementDataSourceProvider.overrideWithValue(ds)],
        ),
      );
      await tester.pumpAndSettle();

      await tester.enterText(find.byType(TextField).at(0), 'long');
      await tester.enterText(find.byType(TextField).at(1), 'Long');
      await tester.enterText(find.byType(TextField).at(2), 'secret1');
      await tester.tap(find.text('Create'));
      await tester.pumpAndSettle();

      expect(find.text('Backend says: username "long" is taken.'), findsOneWidget);
    });

    testWidgets('falls back to generic failure for non-409 errors', (
      tester,
    ) async {
      await tester.binding.setSurfaceSize(const Size(800, 900));
      addTearDown(() => tester.binding.setSurfaceSize(null));
      final ds = _StubUserDataSource(
        createException: const ApiException('Server boom', statusCode: 500),
      );

      await tester.pumpWidget(
        _wrap(
          const CreateUserDialog(),
          overrides: [userManagementDataSourceProvider.overrideWithValue(ds)],
        ),
      );
      await tester.pumpAndSettle();

      await tester.enterText(find.byType(TextField).at(0), 'long');
      await tester.enterText(find.byType(TextField).at(1), 'Long');
      await tester.enterText(find.byType(TextField).at(2), 'secret1');
      await tester.tap(find.text('Create'));
      await tester.pumpAndSettle();

      expect(find.text('Could not create the user.'), findsOneWidget);
    });

    Future<_StubUserDataSource> pumpDialog(WidgetTester tester) async {
      await tester.binding.setSurfaceSize(const Size(800, 900));
      addTearDown(() => tester.binding.setSurfaceSize(null));
      final ds = _StubUserDataSource();
      await tester.pumpWidget(
        _wrap(
          const CreateUserDialog(),
          overrides: [userManagementDataSourceProvider.overrideWithValue(ds)],
        ),
      );
      await tester.pumpAndSettle();
      return ds;
    }

    testWidgets('sends the annual leave quota in the create request', (
      tester,
    ) async {
      final ds = await pumpDialog(tester);

      await _fillCreateForm(tester, quota: '25');
      await tester.tap(find.text('Create'));
      await tester.pumpAndSettle();

      expect(ds.created, [('long', 25)]);
    });

    testWidgets('an empty quota keeps the server default', (tester) async {
      final ds = await pumpDialog(tester);

      await _fillCreateForm(tester);
      await tester.tap(find.text('Create'));
      await tester.pumpAndSettle();

      expect(ds.created, [('long', null)]);
    });

    testWidgets('a quota above 365 is rejected before any request', (
      tester,
    ) async {
      final ds = await pumpDialog(tester);

      await _fillCreateForm(tester, quota: '366');
      await tester.tap(find.text('Create'));
      await tester.pumpAndSettle();

      expect(find.text('Enter a whole number from 0 to 365.'), findsOneWidget);
      expect(ds.created, isEmpty);
    });
  });
}
