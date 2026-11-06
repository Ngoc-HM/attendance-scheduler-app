// Widget tests for the holiday and user create dialog guards (CSV TC-009, TC-013).

import 'package:attendance_scheduler_app/core/network/api_exception.dart';
import 'package:attendance_scheduler_app/features/attendance/data/datasources/attendance_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/attendance/data/datasources/calculations_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/attendance/domain/entities/attendance_entities.dart';
import 'package:attendance_scheduler_app/features/attendance/presentation/providers/attendance_provider.dart';
import 'package:attendance_scheduler_app/features/attendance/presentation/widgets/holidays_dialog.dart';
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

  @override
  Future<UserModel> create({
    required String username,
    required String fullName,
    required String password,
    required String role,
  }) async {
    if (createException != null) throw createException!;
    return UserModel(
      id: 1,
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
  Future<UserModel> approve(int id) async => throw UnimplementedError();
  @override
  Future<UserUpdateResult> update(int id, Map<String, dynamic> changes) async =>
      throw UnimplementedError();
  @override
  Future<void> delete(int id) async {}
}

class _NoopAttendanceDataSource implements AttendanceRemoteDataSource {
  @override
  noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class _NoopCalculationsDataSource implements CalculationsRemoteDataSource {
  @override
  noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class _SeededAttendanceController extends AttendanceController {
  _SeededAttendanceController(super.ds, super.userDs, super.calculationsDs)
    : super() {
    state = state.copyWith(
      holidays: [Holiday(id: 1, day: DateTime(2027, 1, 1), name: 'New Year')],
    );
  }
}

void main() {
  group('HolidaysDialog', () {
    testWidgets('Add button enables once both date and name are set', (
      tester,
    ) async {
      final attendanceDs = _NoopAttendanceDataSource();
      final userDs = _StubUserDataSource();
      final controller = _SeededAttendanceController(
        attendanceDs,
        userDs,
        _NoopCalculationsDataSource(),
      );

      await tester.pumpWidget(
        _wrap(
          const HolidaysDialog(year: 2027),
          overrides: [
            attendanceControllerProvider.overrideWith((ref) => controller),
          ],
        ),
      );
      await tester.pumpAndSettle();

      // No date, no name → button is disabled.
      FilledButton button() => tester.widgetList<FilledButton>(
            find.descendant(
              of: find.byType(HolidaysDialog),
              matching: find.byType(FilledButton),
            ),
          ).first;
      expect(button().onPressed, isNull);

      // Tap the date picker → choose the first date and confirm.
      await tester.tap(find.text('Pick a date'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('OK'));
      await tester.pumpAndSettle();

      // Date is set but name still empty → still disabled.
      expect(button().onPressed, isNull);

      // Typing the name triggers the listener → rebuild → enabled.
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

    testWidgets('shows usernameTaken on 409 from the backend', (tester) async {
      await tester.binding.setSurfaceSize(const Size(800, 900));
      addTearDown(() => tester.binding.setSurfaceSize(null));
      final ds = _StubUserDataSource(
        createException: const ApiException(
          'That username is already taken.',
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

      expect(find.text('That username is already taken.'), findsOneWidget);
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
  });
}
