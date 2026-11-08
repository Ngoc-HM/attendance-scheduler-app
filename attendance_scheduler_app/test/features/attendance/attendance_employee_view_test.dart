// Employees get a read-only view of their own attendance (C2, C8): the page
// loads GET /attendance/me and shows none of the admin actions.

import 'package:attendance_scheduler_app/core/storage/locale_storage.dart';
import 'package:attendance_scheduler_app/design_system/design_system.dart';
import 'package:attendance_scheduler_app/features/attendance/data/datasources/attendance_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/attendance/data/datasources/calculations_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/attendance/domain/entities/attendance_entities.dart';
import 'package:attendance_scheduler_app/features/attendance/presentation/pages/attendance_page.dart';
import 'package:attendance_scheduler_app/features/attendance/presentation/providers/attendance_provider.dart';
import 'package:attendance_scheduler_app/features/auth/domain/entities/user.dart';
import 'package:attendance_scheduler_app/features/auth/domain/repositories/auth_repository.dart';
import 'package:attendance_scheduler_app/features/auth/presentation/providers/auth_provider.dart';
import 'package:attendance_scheduler_app/features/users/data/user_management_datasource.dart';
import 'package:attendance_scheduler_app/i18n/app_localizations.dart';
import 'package:attendance_scheduler_app/i18n/locale_provider.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

class _Unused implements AuthRepository, AttendanceRemoteDataSource,
    UserManagementDataSource, CalculationsRemoteDataSource {
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class _SignedIn extends AuthController {
  _SignedIn(User user) : super(_Unused(), LocaleController(LocaleStorage())) {
    state = AuthState(user: user);
  }
}

/// Records which endpoint the page asked for and serves one day of [userId].
class _RecordingAttendance extends AttendanceController {
  _RecordingAttendance(this.userId) : super(_Unused(), _Unused(), _Unused());

  final int userId;
  bool? loadedAsAdmin;

  @override
  Future<void> load(int year, int month, {bool isAdmin = false}) async {
    loadedAsAdmin = isAdmin;
    state = state.copyWith(
      records: [
        AttendanceRecord(
          id: 1,
          userId: userId,
          workDate: DateTime(year, month, 1),
          code: 'A',
        ),
      ],
    );
  }
}

User _user(UserRole role) => User(
  id: 7,
  username: 'anna',
  fullName: 'Anna',
  role: role,
  status: 'active',
  code: 'T3',
);

Future<_RecordingAttendance> _pump(WidgetTester tester, User user) async {
  await tester.binding.setSurfaceSize(const Size(1600, 1000));
  addTearDown(() => tester.binding.setSurfaceSize(null));
  final attendance = _RecordingAttendance(user.id);
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        authControllerProvider.overrideWith((ref) => _SignedIn(user)),
        attendanceControllerProvider.overrideWith((ref) => attendance),
      ],
      child: MaterialApp(
        theme: AppTheme.light,
        localizationsDelegates: const [
          AppLocalizations.delegate,
          DefaultMaterialLocalizations.delegate,
          DefaultWidgetsLocalizations.delegate,
        ],
        supportedLocales: AppLocalizations.supportedLocales,
        locale: const Locale('en'),
        // The test font is taller than the app font; shrink it so the
        // fixed-height day header of the attendance grid does not overflow.
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(
            context,
          ).copyWith(textScaler: const TextScaler.linear(0.8)),
          child: child!,
        ),
        home: const Scaffold(body: AttendancePage()),
      ),
    ),
  );
  await tester.pumpAndSettle();
  return attendance;
}

void main() {
  testWidgets('employee sees own month read-only', (tester) async {
    final attendance = await _pump(tester, _user(UserRole.t));

    expect(attendance.loadedAsAdmin, isFalse);
    // Own row is named after the signed-in user, not "User 7".
    expect(find.text('Anna'), findsOneWidget);
    expect(find.text('Public holidays'), findsNothing);
    expect(find.text('Update attendance'), findsNothing);
    expect(find.text('Close month'), findsNothing);
  });

  testWidgets('admin keeps the attendance actions', (tester) async {
    final attendance = await _pump(tester, _user(UserRole.m));

    expect(attendance.loadedAsAdmin, isTrue);
    expect(find.text('Public holidays'), findsOneWidget);
    expect(find.text('Update attendance'), findsOneWidget);
    expect(find.text('Close month'), findsOneWidget);
  });
}
