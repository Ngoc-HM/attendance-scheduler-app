// Leave page shows the live registration window (C5) and the requester's
// real carried comp days from /users/me (C9).

import 'package:attendance_scheduler_app/core/storage/locale_storage.dart';
import 'package:attendance_scheduler_app/design_system/design_system.dart';
import 'package:attendance_scheduler_app/features/auth/domain/entities/user.dart';
import 'package:attendance_scheduler_app/features/auth/domain/repositories/auth_repository.dart';
import 'package:attendance_scheduler_app/features/auth/presentation/providers/auth_provider.dart';
import 'package:attendance_scheduler_app/features/leaves/data/datasources/leaves_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/leaves/data/models/leave_model.dart';
import 'package:attendance_scheduler_app/features/leaves/presentation/pages/leaves_page.dart';
import 'package:attendance_scheduler_app/i18n/app_localizations.dart';
import 'package:attendance_scheduler_app/i18n/locale_provider.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

class _UnusedAuthRepository implements AuthRepository {
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class _SignedIn extends AuthController {
  _SignedIn(User user)
    : super(_UnusedAuthRepository(), LocaleController(LocaleStorage())) {
    state = AuthState(user: user);
  }
}

class _FakeLeaves implements LeavesRemoteDataSource {
  _FakeLeaves(this.window);

  final LeaveWindow window;

  @override
  Future<LeaveWindow> fetchWindow() async => window;

  @override
  Future<List<LeaveModel>> listOwn() async => [
    for (final id in [1, 2])
      LeaveModel(
        id: id,
        userId: 7,
        startDate: DateTime(2026, 12, id),
        endDate: DateTime(2026, 12, id),
        leaveType: 'monthly',
        status: 'pending',
      ),
  ];

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

const _employee = User(
  id: 7,
  username: 'anna',
  fullName: 'Anna',
  role: UserRole.t,
  status: 'active',
  code: 'T3',
  carryComp: 3,
);

LeaveWindow _window({required bool open}) => LeaveWindow(
  monthlyOpen: open,
  monthlyTargetYear: 2026,
  monthlyTargetMonth: 12,
  annualTargetYear: 2027,
  closesOnDay: 18,
  enforced: true,
);

Future<void> _pump(WidgetTester tester, LeaveWindow window) async {
  await tester.binding.setSurfaceSize(const Size(1400, 1000));
  addTearDown(() => tester.binding.setSurfaceSize(null));
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        authControllerProvider.overrideWith((ref) => _SignedIn(_employee)),
        leavesDataSourceProvider.overrideWithValue(_FakeLeaves(window)),
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
        home: const Scaffold(body: LeavesPage()),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('closed window from the API drives banner and subtitle', (
    tester,
  ) async {
    await _pump(tester, _window(open: false));

    expect(find.text('Monthly registration closed'), findsOneWidget);
    expect(
      find.text(
        'Monthly leave: register by day 18 of the previous month. '
        'Annual leave: register the year before.',
      ),
      findsOneWidget,
    );
    expect(find.textContaining('unrestricted'), findsNothing);
  });

  testWidgets('open window shows the open banner', (tester) async {
    await _pump(tester, _window(open: true));

    expect(find.text('Registration open'), findsOneWidget);
    expect(find.text('Monthly registration closed'), findsNothing);
  });

  testWidgets('comp days come from the user, counted once per person', (
    tester,
  ) async {
    await _pump(tester, _window(open: true));

    // Both rows carry the requester's 3 comp days...
    expect(find.text('3'), findsNWidgets(3));
    // ...and the metric counts the person once (not 3 + 3).
    expect(find.text('6'), findsNothing);
  });
}
