// Pixel goldens rendered on macOS. Font rasterisation differs on Linux and
// Windows, so CI runs these only on the macOS job (`flutter test --tags golden`)
// and every other job runs `flutter test --exclude-tags golden`.
@Tags(['golden'])
library;

import 'package:attendance_scheduler_app/design_system/design_system.dart';
import 'package:attendance_scheduler_app/features/auth/presentation/pages/login_page.dart';
import 'package:attendance_scheduler_app/features/home/presentation/pages/home_shell.dart';
import 'package:attendance_scheduler_app/features/schedule/data/datasources/schedule_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/flights/data/datasources/flights_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/flights/data/models/flight_day_model.dart';
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

class _FakeFlightsDataSource extends FlightsRemoteDataSource {
  _FakeFlightsDataSource() : super(Dio());
  @override
  Future<List<FlightDayModel>> listDays(int year, int month) async => [];
}

/// The schedule goldens show a fixed month (a 30-day June) so they do not
/// change with the clock: the roster's day columns and the month title would
/// otherwise follow DateTime.now().
final _goldenMonth = DateTime(2026, 6);

List<Override> _scheduleOverrides() => [
      scheduleControllerProvider.overrideWith((ref) => _FakeScheduleController()),
      shiftChangeControllerProvider
          .overrideWith((ref) => _FakeShiftChangeController()),
      flightsDataSourceProvider
          .overrideWith((ref) => _FakeFlightsDataSource()),
    ];

/// Asset images (the shell logo) decode outside the fake clock: without this
/// the first test to show one captures an empty box.
Future<void> _decodeImages(WidgetTester tester) async {
  await tester.runAsync(() async {
    for (final element in find.byType(Image).evaluate()) {
      await precacheImage((element.widget as Image).image, element);
    }
  });
  await tester.pumpAndSettle();
}

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
          home: RepaintBoundary(
            key: const Key('schedule-golden'),
            child: HomeShell(
              location: '/schedule',
              child: SchedulePage(initialMonth: _goldenMonth),
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    await _decodeImages(tester);

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
          home: RepaintBoundary(
            key: const Key('schedule-compact-golden'),
            child: HomeShell(
              location: '/schedule',
              child: SchedulePage(initialMonth: _goldenMonth),
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    await _decodeImages(tester);

    await expectLater(
      find.byKey(const Key('schedule-compact-golden')),
      matchesGoldenFile('goldens/schedule_compact.png'),
    );
  });
}
