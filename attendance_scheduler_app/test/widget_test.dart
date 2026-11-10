// Smoke test: the app boots and lands on the login screen.

import 'package:attendance_scheduler_app/app.dart';
import 'package:attendance_scheduler_app/core/storage/token_storage.dart';
import 'package:attendance_scheduler_app/design_system/design_system.dart';
import 'package:attendance_scheduler_app/i18n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

/// No stored session. The app reads the secure store at boot (session
/// restore); its platform channel never answers inside a widget test.
class _EmptyTokenStorage extends TokenStorage {
  @override
  Future<String?> read() async => null;
}

Widget _signedOutApp() => ProviderScope(
  overrides: [tokenStorageProvider.overrideWithValue(_EmptyTokenStorage())],
  child: const AttendanceSchedulerApp(),
);

void main() {
  test('English and Vietnamese contain the same localization keys', () {
    expect(AppLocalizations.translationsAreComplete, isTrue);
  });

  testWidgets('App boots to the login screen', (WidgetTester tester) async {
    await tester.pumpWidget(_signedOutApp());
    await tester.pumpAndSettle();

    expect(find.text('Log in'), findsNWidgets(2));
    expect(find.text('Username'), findsOneWidget);
  });

  // Login shows the customer's logo; the aircraft photo fills the context
  // panel, which only wide windows have, and carries no text.
  for (final (width, hasPanel) in [(1280.0, true), (800.0, false)]) {
    testWidgets('login shows the logo at width $width', (tester) async {
      await tester.binding.setSurfaceSize(Size(width, 800));
      addTearDown(() => tester.binding.setSurfaceSize(null));

      await tester.pumpWidget(_signedOutApp());
      await tester.pumpAndSettle();

      expect(find.byType(DsBrandLogo), findsOneWidget);
      expect(
        find.byKey(const Key('login-photo')),
        hasPanel ? findsOneWidget : findsNothing,
      );
      expect(find.text('Roster FRA'), findsNothing);
      expect(find.text('Automatic monthly roster'), findsNothing);
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets('English is default and Vietnamese can be selected', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(_signedOutApp());
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

  testWidgets('tab content updates on navigation', (tester) async {
    await tester.binding.setSurfaceSize(const Size(1280, 800));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await tester.pumpWidget(const _NavigationHarness(index: 0, label: 'First'));
    await tester.pumpAndSettle();
    expect(_contentLabel(tester), 'First');

    await tester.pumpWidget(const _NavigationHarness(index: 2, label: 'Third'));
    await tester.pumpAndSettle();
    expect(_contentLabel(tester), 'Third');

    await tester.pumpWidget(
      const _NavigationHarness(index: 1, label: 'Second'),
    );
    await tester.pumpAndSettle();
    expect(_contentLabel(tester), 'Second');
  });

  // The shell header shows the customer's logo instead of the product name:
  // the wordmark on a wide rail and in the phone app bar, the lotus alone on
  // the collapsed rail.
  for (final (width, asset) in [
    (1280.0, DsBrandLogo.logoAsset),
    (900.0, DsBrandLogo.markAsset),
    (600.0, DsBrandLogo.logoAsset),
  ]) {
    testWidgets('shell header shows the logo at width $width', (tester) async {
      await tester.binding.setSurfaceSize(Size(width, 800));
      addTearDown(() => tester.binding.setSurfaceSize(null));

      await tester.pumpWidget(
        const _NavigationHarness(index: 0, label: 'First'),
      );
      await tester.pumpAndSettle();

      final logo = tester.widget<Image>(
        find.descendant(
          of: find.byType(DsBrandLogo),
          matching: find.byType(Image),
        ),
      );
      expect((logo.image as AssetImage).assetName, asset);
      expect(find.text('Test'), findsNothing);
      expect(tester.takeException(), isNull);
    });
  }
}

String _contentLabel(WidgetTester tester) {
  return tester.widget<Text>(find.byKey(const Key('page-content'))).data!;
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
