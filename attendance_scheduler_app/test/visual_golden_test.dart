import 'package:attendance_scheduler_app/design_system/design_system.dart';
import 'package:attendance_scheduler_app/features/auth/presentation/pages/login_page.dart';
import 'package:attendance_scheduler_app/features/home/presentation/pages/home_shell.dart';
import 'package:attendance_scheduler_app/features/schedule/data/datasources/schedule_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/schedule/presentation/pages/schedule_page.dart';
import 'package:attendance_scheduler_app/features/schedule/presentation/providers/schedule_provider.dart';
import 'package:attendance_scheduler_app/features/schedule/presentation/providers/shift_change_provider.dart';
import 'package:attendance_scheduler_app/features/users/data/user_management_datasource.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

/// The wired SchedulePage fires a network load() on first frame; in a widget
/// test there is no backend, so we override its controllers with no-op fakes
/// that hold a deterministic settled (empty) state. The golden then captures
/// the data-driven page's empty state — its valid visual baseline.
class _FakeScheduleController extends ScheduleController {
  _FakeScheduleController()
      : super(ScheduleRemoteDataSource(Dio()), UserManagementDataSource(Dio()));
  @override
  Future<void> load(int year, int month, {bool isAdmin = false}) async {}
}

class _FakeShiftChangeController extends ShiftChangeController {
  _FakeShiftChangeController() : super(ScheduleRemoteDataSource(Dio()));
  @override
  Future<void> load({bool all = false}) async {}
}

List<Override> _scheduleOverrides() => [
      scheduleControllerProvider.overrideWith((ref) => _FakeScheduleController()),
      shiftChangeControllerProvider
          .overrideWith((ref) => _FakeShiftChangeController()),
    ];

void main() {
  testWidgets('login desktop visual', (tester) async {
    await tester.binding.setSurfaceSize(const Size(1280, 800));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await tester.pumpWidget(
      ProviderScope(
        child: MaterialApp(
          theme: AppTheme.light,
          home: const RepaintBoundary(
            key: Key('login-golden'),
            child: LoginPage(),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    await expectLater(
      find.byKey(const Key('login-golden')),
      matchesGoldenFile('goldens/login_desktop.png'),
    );
  });

  testWidgets('schedule desktop visual', (tester) async {
    await tester.binding.setSurfaceSize(const Size(1440, 1000));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await tester.pumpWidget(
      ProviderScope(
        overrides: _scheduleOverrides(),
        child: MaterialApp(
          theme: AppTheme.light,
          home: const RepaintBoundary(
            key: Key('schedule-golden'),
            child: HomeShell(location: '/schedule', child: SchedulePage()),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    await expectLater(
      find.byKey(const Key('schedule-golden')),
      matchesGoldenFile('goldens/schedule_desktop.png'),
    );
  });

  testWidgets('schedule compact liquid navigation visual', (tester) async {
    await tester.binding.setSurfaceSize(const Size(700, 900));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await tester.pumpWidget(
      ProviderScope(
        overrides: _scheduleOverrides(),
        child: MaterialApp(
          theme: AppTheme.light,
          home: const RepaintBoundary(
            key: Key('schedule-compact-golden'),
            child: HomeShell(location: '/schedule', child: SchedulePage()),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    await expectLater(
      find.byKey(const Key('schedule-compact-golden')),
      matchesGoldenFile('goldens/schedule_compact.png'),
    );
  });
}
