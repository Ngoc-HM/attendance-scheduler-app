// Smoke test: the app boots and lands on the login screen.

import 'package:animations/animations.dart';
import 'package:attendance_scheduler_app/app.dart';
import 'package:attendance_scheduler_app/design_system/design_system.dart';
import 'package:attendance_scheduler_app/i18n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('English and Vietnamese contain the same localization keys', () {
    expect(AppLocalizations.translationsAreComplete, isTrue);
  });

  testWidgets('App boots to the login screen', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(child: AttendanceSchedulerApp()),
    );
    await tester.pumpAndSettle();

    expect(find.text('Log in'), findsNWidgets(2));
    expect(find.text('Username'), findsOneWidget);
  });

  testWidgets('English is default and Vietnamese can be selected', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      const ProviderScope(child: AttendanceSchedulerApp()),
    );
    await tester.pumpAndSettle();

    expect(find.text('Use your approved account to continue.'), findsOneWidget);
    expect(find.text('Đăng nhập'), findsNothing);

    await tester.tap(find.byKey(const Key('language-selector')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Vietnamese'));
    await tester.pumpAndSettle();

    expect(find.text('Đăng nhập'), findsNWidgets(2));
    expect(
      find.text('Sử dụng tài khoản đã được phê duyệt để tiếp tục.'),
      findsOneWidget,
    );
    expect(find.text('Use your approved account to continue.'), findsNothing);
  });

  testWidgets('tab content follows the navigation direction', (tester) async {
    await tester.binding.setSurfaceSize(const Size(1280, 800));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await tester.pumpWidget(const _NavigationHarness(index: 0, label: 'First'));
    await tester.pumpAndSettle();

    // Selecting a LOWER tab → forward shared-axis (right→left): reverse=false.
    await tester.pumpWidget(const _NavigationHarness(index: 2, label: 'Third'));
    await tester.pump();
    expect(_switcherReverse(tester), isFalse);
    await tester.pumpAndSettle();

    // Selecting a HIGHER tab → reverse shared-axis (left→right): reverse=true.
    await tester.pumpWidget(
      const _NavigationHarness(index: 1, label: 'Second'),
    );
    await tester.pump();
    expect(_switcherReverse(tester), isTrue);
  });
}

/// Direction flag of the tab-transition switcher (all instances agree).
bool _switcherReverse(WidgetTester tester) {
  return tester
      .widgetList<PageTransitionSwitcher>(find.byType(PageTransitionSwitcher))
      .first
      .reverse;
}

class _NavigationHarness extends StatelessWidget {
  const _NavigationHarness({required this.index, required this.label});

  final int index;
  final String label;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      theme: AppTheme.light,
      home: DsNavigationShell(
        appTitle: 'Test',
        productName: 'Test',
        destinations: const [
          DsNavigationDestination(
            path: '/first',
            label: 'First',
            icon: Icons.looks_one_outlined,
          ),
          DsNavigationDestination(
            path: '/second',
            label: 'Second',
            icon: Icons.looks_two_outlined,
          ),
          DsNavigationDestination(
            path: '/third',
            label: 'Third',
            icon: Icons.looks_3_outlined,
          ),
        ],
        selectedIndex: index,
        onSelected: (_) {},
        onLogout: () {},
        logoutLabel: 'Log out',
        languageCode: 'en',
        onLanguageChanged: (_) {},
        child: ColoredBox(
          color: DsColors.background,
          child: Center(child: Text(label, key: const Key('page-content'))),
        ),
      ),
    );
  }
}
