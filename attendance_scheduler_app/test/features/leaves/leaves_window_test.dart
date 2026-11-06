// Leave page shows the live registration window (C5) and the real carried
// comp days from /users/me or /users (C9).

import 'package:attendance_scheduler_app/core/storage/locale_storage.dart';
import 'package:attendance_scheduler_app/design_system/design_system.dart';
import 'package:attendance_scheduler_app/features/auth/data/models/user_model.dart';
import 'package:attendance_scheduler_app/features/auth/domain/entities/user.dart';
import 'package:attendance_scheduler_app/features/auth/domain/repositories/auth_repository.dart';
import 'package:attendance_scheduler_app/features/auth/presentation/providers/auth_provider.dart';
import 'package:attendance_scheduler_app/features/leaves/data/datasources/leaves_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/leaves/data/models/leave_model.dart';
import 'package:attendance_scheduler_app/features/leaves/presentation/pages/leaves_page.dart';
import 'package:attendance_scheduler_app/features/users/data/user_management_datasource.dart';
import 'package:attendance_scheduler_app/i18n/app_localizations.dart';
import 'package:attendance_scheduler_app/i18n/locale_provider.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
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
  _FakeLeaves(this.window, this.leaves);

  final LeaveWindow window;
  final List<LeaveModel> leaves;

  @override
  Future<LeaveWindow> fetchWindow() async => window;

  @override
  Future<List<LeaveModel>> listOwn() async => leaves;

  @override
  Future<List<LeaveModel>> listAll() async => leaves;

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

/// GET /users for the admin: [users] only.
class _FakeUsers implements UserManagementDataSource {
  _FakeUsers(this.users);

  final List<UserModel> users;

  @override
  Future<List<UserModel>> list() async => users;

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

const _admin = User(
  id: 1,
  username: 'admin',
  fullName: 'Admin',
  role: UserRole.m,
  status: 'active',
  code: 'M1',
);

UserModel _member(int id, int carryComp, {String status = 'active'}) =>
    UserModel(
      id: id,
      username: 'u$id',
      fullName: 'U$id',
      role: UserRole.t,
      status: status,
      code: 'T$id',
      carryComp: carryComp,
    );

List<LeaveModel> _twoPendingOf(int userId) => [
  for (final id in [1, 2])
    LeaveModel(
      id: id,
      userId: userId,
      startDate: DateTime(2026, 12, id),
      endDate: DateTime(2026, 12, id),
      leaveType: 'monthly',
      status: 'pending',
    ),
];

LeaveWindow _window({required bool open}) => LeaveWindow(
  monthlyOpen: open,
  monthlyTargetYear: 2026,
  monthlyTargetMonth: 12,
  annualTargetYear: 2027,
  closesOnDay: 18,
  enforced: true,
);

const _enSubtitle =
    'Monthly leave: register by day 18 of the previous month. '
    'Annual leave: register the year before.';

Future<void> _pump(
  WidgetTester tester, {
  required LeaveWindow window,
  User user = _employee,
  List<LeaveModel>? leaves,
  List<UserModel> users = const [],
  String language = 'en',
}) async {
  // Wide enough for the admin Approve/Reject column in the test font.
  await tester.binding.setSurfaceSize(const Size(2000, 1000));
  addTearDown(() => tester.binding.setSurfaceSize(null));
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        authControllerProvider.overrideWith((ref) => _SignedIn(user)),
        leavesDataSourceProvider.overrideWithValue(
          _FakeLeaves(window, leaves ?? _twoPendingOf(user.id)),
        ),
        userManagementDataSourceProvider.overrideWithValue(_FakeUsers(users)),
      ],
      child: MaterialApp(
        theme: AppTheme.light,
        localizationsDelegates: const [
          AppLocalizations.delegate,
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: AppLocalizations.supportedLocales,
        locale: Locale(language),
        home: const Scaffold(body: LeavesPage()),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

/// The value shown on the "Comp days" metric card.
String _compDaysMetric(WidgetTester tester) {
  final card = find.ancestor(
    of: find.text('Comp days'),
    matching: find.byType(DsMetricCard),
  );
  return tester.widget<DsMetricCard>(card).value;
}

void main() {
  testWidgets('closed window from the API drives banner and subtitle', (
    tester,
  ) async {
    await _pump(tester, window: _window(open: false));

    expect(find.text('Monthly registration closed'), findsOneWidget);
    expect(find.text(_enSubtitle), findsOneWidget);
    expect(find.textContaining('unrestricted'), findsNothing);
  });

  testWidgets('Vietnamese subtitle includes the closing day itself', (
    tester,
  ) async {
    await _pump(tester, window: _window(open: true), language: 'vi');

    expect(
      find.text(
        'Nghỉ tháng: đăng ký chậm nhất đến hết ngày 18 của tháng trước. '
        'Nghỉ phép năm: đăng ký từ năm trước.',
      ),
      findsOneWidget,
    );
  });

  testWidgets('open window shows the open banner', (tester) async {
    await _pump(tester, window: _window(open: true));

    expect(find.text('Registration open'), findsOneWidget);
    expect(find.text('Monthly registration closed'), findsNothing);
  });

  testWidgets('request dialog states the live rule, not dev-mode copy', (
    tester,
  ) async {
    await _pump(tester, window: _window(open: true));

    await tester.tap(find.text('Request monthly leave'));
    await tester.pumpAndSettle();

    expect(
      find.descendant(
        of: find.byType(DsFormDialog),
        matching: find.text(_enSubtitle),
      ),
      findsOneWidget,
    );
    expect(find.textContaining('Development mode'), findsNothing);
  });

  testWidgets('employee comp days come from /users/me, once per person', (
    tester,
  ) async {
    await _pump(tester, window: _window(open: true));

    expect(_compDaysMetric(tester), '3');
  });

  testWidgets('employee without leave requests still sees comp days', (
    tester,
  ) async {
    await _pump(tester, window: _window(open: true), leaves: const []);

    expect(_compDaysMetric(tester), '3');
  });

  testWidgets('admin comp days sum every active user, requests or not', (
    tester,
  ) async {
    await _pump(
      tester,
      window: _window(open: true),
      user: _admin,
      leaves: _twoPendingOf(2),
      users: [
        _member(2, 2),
        _member(3, 4),
        _member(4, 5, status: 'disabled'),
      ],
    );

    expect(_compDaysMetric(tester), '6');
  });
}
