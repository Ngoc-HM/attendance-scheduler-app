// Navigation badges (owner 2026-11-10) in the three shell layouts: the wide
// rail (pill after the label), the collapsed rail and the phone bar (badge
// on the icon). Hidden at 0, "99+" above 99, no overflow, count read aloud.

import 'package:attendance_scheduler_app/design_system/design_system.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

const _longLabel = 'A very long navigation label that cannot fit the rail';

Widget _shell({int? first, int? second, int? third, String label = 'First'}) {
  return MaterialApp(
    theme: AppTheme.light,
    home: DsNavigationShell(
      appTitle: 'Test',
      productName: 'Test',
      destinations: [
        DsNavigationDestination(
          path: '/first',
          label: label,
          icon: Icons.looks_one_outlined,
          badgeCount: first,
        ),
        DsNavigationDestination(
          path: '/second',
          label: 'Second',
          icon: Icons.looks_two_outlined,
          badgeCount: second,
        ),
        DsNavigationDestination(
          path: '/third',
          label: 'Third',
          icon: Icons.looks_3_outlined,
          badgeCount: third,
        ),
      ],
      selectedIndex: 0,
      onSelected: (_) {},
      onLogout: () {},
      logoutLabel: 'Log out',
      languageCode: 'en',
      onLanguageChanged: (_) {},
      child: const SizedBox.expand(),
    ),
  );
}

Future<void> _pumpAt(WidgetTester tester, Size size, Widget app) async {
  await tester.binding.setSurfaceSize(size);
  addTearDown(() => tester.binding.setSurfaceSize(null));
  await tester.pumpWidget(app);
  await tester.pumpAndSettle();
}

void main() {
  test('badge text: none for null/0, the number, then 99+', () {
    expect(dsNavigationBadgeText(null), isNull);
    expect(dsNavigationBadgeText(0), isNull);
    expect(dsNavigationBadgeText(7), '7');
    expect(dsNavigationBadgeText(99), '99');
    expect(dsNavigationBadgeText(100), '99+');
  });

  testWidgets('wide rail: pill after the label, hidden at 0, 99+', (
    tester,
  ) async {
    final semantics = tester.ensureSemantics();
    await _pumpAt(
      tester,
      const Size(1280, 720),
      _shell(first: 3, second: 0, third: 120),
    );

    expect(find.byType(DsNavigationCountPill), findsNWidgets(2));
    expect(find.byType(DsNavigationIconBadge), findsNothing);
    expect(find.text('3'), findsOneWidget);
    expect(find.text('99+'), findsOneWidget);
    expect(find.text('0'), findsNothing);
    // The pill sits to the right of its label.
    expect(
      tester.getCenter(find.text('3')).dx,
      greaterThan(tester.getCenter(find.text('First')).dx),
    );
    expect(find.bySemanticsLabel('First, 3 pending'), findsOneWidget);
    expect(find.bySemanticsLabel('Second'), findsOneWidget);
    expect(find.bySemanticsLabel('Third, 120 pending'), findsOneWidget);
    expect(tester.takeException(), isNull);
    semantics.dispose();
  });

  testWidgets('wide rail: a long label still ellipsizes beside the pill', (
    tester,
  ) async {
    await _pumpAt(
      tester,
      const Size(1280, 720),
      _shell(first: 120, label: _longLabel),
    );

    final text = tester.widget<Text>(find.text(_longLabel));
    expect(text.overflow, TextOverflow.ellipsis);
    expect(find.text('99+'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('collapsed rail: badge on the icon, count in the tooltip', (
    tester,
  ) async {
    final semantics = tester.ensureSemantics();
    await _pumpAt(
      tester,
      const Size(900, 720),
      _shell(first: 3, second: 0, third: 120),
    );

    expect(find.byType(DsNavigationIconBadge), findsNWidgets(2));
    expect(find.byType(DsNavigationCountPill), findsNothing);
    expect(find.text('3'), findsOneWidget);
    expect(find.text('99+'), findsOneWidget);
    expect(find.text('0'), findsNothing);
    expect(find.byTooltip('First, 3 pending'), findsOneWidget);
    expect(find.byTooltip('Second'), findsOneWidget);
    expect(find.bySemanticsLabel('Third, 120 pending'), findsOneWidget);
    // The badge stays inside the 80 px rail.
    final rail = tester.getRect(find.byType(DsLiquidGlassSurface).first);
    expect(
      tester.getRect(find.text('99+')).right,
      lessThanOrEqualTo(rail.right),
    );
    expect(tester.takeException(), isNull);
    semantics.dispose();
  });

  testWidgets('phone bar: badge on the icon, hidden at 0, 99+', (
    tester,
  ) async {
    final semantics = tester.ensureSemantics();
    await _pumpAt(
      tester,
      const Size(600, 800),
      _shell(first: 3, second: 0, third: 120),
    );

    expect(find.byType(DsLiquidNavigationBar), findsOneWidget);
    expect(find.byType(DsNavigationIconBadge), findsNWidgets(2));
    expect(find.text('3'), findsOneWidget);
    expect(find.text('99+'), findsOneWidget);
    expect(find.text('0'), findsNothing);
    expect(find.bySemanticsLabel('3 pending'), findsOneWidget);
    expect(tester.takeException(), isNull);
    semantics.dispose();
  });

  testWidgets('no counts: no badge in any layout', (tester) async {
    for (final size in const [Size(1280, 720), Size(900, 720), Size(600, 800)]) {
      await _pumpAt(tester, size, _shell());
      expect(find.byType(DsNavigationIconBadge), findsNothing);
      expect(find.byType(DsNavigationCountPill), findsNothing);
    }
  });
}
