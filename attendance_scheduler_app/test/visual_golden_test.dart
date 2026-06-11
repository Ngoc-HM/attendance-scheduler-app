import 'package:attendance_scheduler_app/design_system/design_system.dart';
import 'package:attendance_scheduler_app/features/auth/presentation/pages/login_page.dart';
import 'package:attendance_scheduler_app/features/home/presentation/pages/home_shell.dart';
import 'package:attendance_scheduler_app/features/schedule/presentation/pages/schedule_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

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
