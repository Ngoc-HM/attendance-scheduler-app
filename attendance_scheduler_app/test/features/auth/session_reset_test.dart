// Session teardown on a shared desktop (review 2026-11-08 D1 + E): whatever
// the previous person loaded must be gone once they log out or their session
// ends, and an account disabled mid-session is signed out on its next 403.

import 'dart:convert';
import 'dart:typed_data';

import 'package:attendance_scheduler_app/core/network/api_client.dart';
import 'package:attendance_scheduler_app/core/storage/token_storage.dart';
import 'package:attendance_scheduler_app/features/attendance/presentation/providers/attendance_provider.dart';
import 'package:attendance_scheduler_app/features/attendance/presentation/providers/time_clock_provider.dart';
import 'package:attendance_scheduler_app/features/auth/data/models/user_model.dart';
import 'package:attendance_scheduler_app/features/auth/data/repositories/auth_repository_impl.dart';
import 'package:attendance_scheduler_app/features/auth/domain/entities/user.dart';
import 'package:attendance_scheduler_app/features/auth/domain/repositories/auth_repository.dart';
import 'package:attendance_scheduler_app/features/auth/presentation/providers/auth_provider.dart';
import 'package:attendance_scheduler_app/features/flights/presentation/providers/flights_provider.dart';
import 'package:attendance_scheduler_app/features/home/presentation/providers/pending_counts_provider.dart';
import 'package:attendance_scheduler_app/features/leaves/data/datasources/leaves_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/leaves/data/models/leave_model.dart';
import 'package:attendance_scheduler_app/features/leaves/presentation/pages/leaves_page.dart';
import 'package:attendance_scheduler_app/features/leaves/presentation/providers/leaves_provider.dart';
import 'package:attendance_scheduler_app/features/reports/presentation/providers/reports_provider.dart';
import 'package:attendance_scheduler_app/features/schedule/presentation/providers/schedule_provider.dart';
import 'package:attendance_scheduler_app/features/schedule/presentation/providers/shift_change_provider.dart';
import 'package:attendance_scheduler_app/features/users/data/user_management_datasource.dart';
import 'package:attendance_scheduler_app/features/users/presentation/providers/users_provider.dart';
import 'package:attendance_scheduler_app/i18n/app_localizations.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

const _admin = UserModel(id: 1, username: 'admin', fullName: 'Admin', role: UserRole.m, status: 'active', code: 'M1');
const _anna = UserModel(id: 7, username: 'anna', fullName: 'Anna', role: UserRole.t, status: 'active', code: 'T3');
const _bob = UserModel(id: 9, username: 'bob', fullName: 'Bob', role: UserRole.a, status: 'active', code: 'A4');

class _MemoryTokenStorage extends TokenStorage {
  String? token;

  @override
  Future<void> save(String value) async => token = value;

  @override
  Future<String?> read() async => token;

  @override
  Future<void> clear() async => token = null;
}

/// Signs in `admin` as the admin and anyone else as Anna.
class _Repo implements AuthRepository {
  @override
  Future<User> login(String u, String p) async => u == 'admin' ? _admin : _anna;

  @override
  Future<void> logout() async {}

  @override
  dynamic noSuchMethod(Invocation i) => super.noSuchMethod(i);
}

/// Admin sees Bob's (A4) request; an employee's own list is empty.
class _Leaves implements LeavesRemoteDataSource {
  int listAllCalls = 0;
  int listOwnCalls = 0;

  @override
  Future<List<LeaveModel>> listAll() async {
    listAllCalls++;
    return [
      LeaveModel(id: 1, userId: 9, startDate: DateTime(2026, 12, 3), endDate: DateTime(2026, 12, 4), leaveType: 'monthly', status: 'pending', note: 'medical'),
    ];
  }

  @override
  Future<List<LeaveModel>> listOwn() async {
    listOwnCalls++;
    return const [];
  }

  @override
  Future<LeaveWindow> fetchWindow() async => const LeaveWindow(monthlyOpen: true, monthlyTargetYear: 2026, monthlyTargetMonth: 12, annualTargetYear: 2027, closesOnDay: 20, enforced: true);

  @override
  Future<AnnualLeaveBalance> fetchBalance({int? year}) async => const AnnualLeaveBalance(year: 2026, quota: 30, used: 0, pending: 0, remaining: 30);

  @override
  dynamic noSuchMethod(Invocation i) => super.noSuchMethod(i);
}

class _Users implements UserManagementDataSource {
  @override
  Future<List<UserModel>> list() async => const [_admin, _anna, _bob];

  @override
  Future<List<UserDirectoryEntry>> directory() async => const [
        UserDirectoryEntry(id: 1, code: 'M1', role: UserRole.m),
        UserDirectoryEntry(id: 7, code: 'T3', role: UserRole.t),
        UserDirectoryEntry(id: 9, code: 'A4', role: UserRole.a),
      ];

  @override
  dynamic noSuchMethod(Invocation i) => super.noSuchMethod(i);
}

/// No backend in these tests: anything not faked above fails fast.
class _OfflineAdapter implements HttpClientAdapter {
  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<Uint8List>? s, Future<void>? c) async =>
      ResponseBody.fromString('{"detail":"offline"}', 503,
          headers: {Headers.contentTypeHeader: [Headers.jsonContentType]});

  @override
  void close({bool force = false}) {}
}

ProviderContainer _container(_Leaves leaves) {
  final c = ProviderContainer(overrides: [
    authRepositoryProvider.overrideWithValue(_Repo()),
    tokenStorageProvider.overrideWithValue(_MemoryTokenStorage()),
    dioProvider.overrideWithValue(Dio()..httpClientAdapter = _OfflineAdapter()),
    leavesDataSourceProvider.overrideWithValue(leaves),
    userManagementDataSourceProvider.overrideWithValue(_Users()),
  ]);
  addTearDown(c.dispose);
  return c;
}

/// Every controller that caches what the signed-in person loaded.
Map<String, ProviderListenable<Object>> get _userScoped => {
      'leaves': leavesControllerProvider.notifier,
      'attendance': attendanceControllerProvider.notifier,
      'timeClock': timeClockControllerProvider.notifier,
      'schedule': scheduleControllerProvider.notifier,
      'shiftChange': shiftChangeControllerProvider.notifier,
      'reports': reportsControllerProvider.notifier,
      'flights': flightsControllerProvider.notifier,
      'users': usersControllerProvider.notifier,
      'pendingCounts': pendingCountsProvider.notifier,
    };

/// Reads every controller, then lets their first loads finish (a controller
/// disposed mid-load is a separate concern of each controller).
Future<Map<String, Object>> _snapshot(ProviderContainer c) async {
  final controllers = {
    for (final entry in _userScoped.entries) entry.key: c.read(entry.value),
  };
  await pumpEventQueue();
  return controllers;
}

Future<void> _expectAllRebuilt(ProviderContainer c, Map<String, Object> before) async {
  final after = await _snapshot(c);
  for (final name in before.keys) {
    expect(identical(before[name], after[name]), isFalse,
        reason: '$name still holds the previous user\'s controller');
  }
}

Widget _app(ProviderContainer c, Widget home) => UncontrolledProviderScope(
      container: c,
      child: MaterialApp(
        localizationsDelegates: const [AppLocalizations.delegate, DefaultMaterialLocalizations.delegate, DefaultWidgetsLocalizations.delegate],
        supportedLocales: AppLocalizations.supportedLocales,
        locale: const Locale('en'),
        home: Scaffold(body: home),
      ),
    );

// --- 403 on a disabled account -------------------------------------------

/// Backend stand-in for the 403 tests: login, `/users/me`, one admin route
/// and one employee route. [inactive] flips the account to disabled.
class _SessionAdapter implements HttpClientAdapter {
  bool inactive = false;
  int meCalls = 0;

  static const _annaJson = {
    'id': 7, 'username': 'anna', 'full_name': 'Anna', 'role': 'T', 'status': 'active',
    'code': 'T3', 'carry_comp': 0, 'carry_streak': 0, 'annual_leave_quota': 30,
  };

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<Uint8List>? s, Future<void>? c) async {
    ResponseBody json(Object body, int code) => ResponseBody.fromString(jsonEncode(body), code,
        headers: {Headers.contentTypeHeader: [Headers.jsonContentType]});
    final path = o.uri.path;
    if (path.endsWith('/auth/login')) return json({'access_token': 'jwt', 'token_type': 'bearer'}, 200);
    if (path.endsWith('/users/me')) {
      meCalls++;
      return inactive ? json({'detail': 'User account is not active.'}, 403) : json(_annaJson, 200);
    }
    if (path.endsWith('/users')) return json({'detail': 'Admin privileges required.'}, 403);
    if (path.endsWith('/leaves')) {
      return inactive ? json({'detail': 'User account is not active.'}, 403) : json(<Object>[], 200);
    }
    return json({'detail': 'nope'}, 404);
  }

  @override
  void close({bool force = false}) {}
}

({ProviderContainer c, _SessionAdapter backend, _MemoryTokenStorage tokens}) _realSession() {
  final tokens = _MemoryTokenStorage();
  final c = ProviderContainer(overrides: [tokenStorageProvider.overrideWithValue(tokens)]);
  addTearDown(c.dispose);
  final backend = _SessionAdapter();
  c.read(dioProvider).httpClientAdapter = backend;
  return (c: c, backend: backend, tokens: tokens);
}

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  test('logout_then_login_other_user_refetches_every_user_scoped_provider', () async {
    final c = _container(_Leaves());
    // Keep the autoDispose users list alive like an open Users page would.
    c.listen(usersControllerProvider, (_, _) {});
    final auth = c.read(authControllerProvider.notifier);

    await auth.login('admin', 'x');
    final adminControllers = await _snapshot(c);
    await auth.logout();
    await auth.login('anna', 'x');

    await _expectAllRebuilt(c, adminControllers);
  });

  test('session expiry also drops every user-scoped provider', () async {
    final c = _container(_Leaves());
    final auth = c.read(authControllerProvider.notifier);

    await auth.login('admin', 'x');
    final adminControllers = await _snapshot(c);
    c.read(sessionExpiredSignalProvider.notifier).fire();
    await pumpEventQueue();

    expect(c.read(authControllerProvider).user, isNull);
    await _expectAllRebuilt(c, adminControllers);
  });

  testWidgets('employee signing in after an admin logout only sees their own leaves', (tester) async {
    await tester.binding.setSurfaceSize(const Size(2200, 1400));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final leaves = _Leaves();
    final c = _container(leaves);
    final auth = c.read(authControllerProvider.notifier);

    await auth.login('admin', 'x');
    await tester.pumpWidget(_app(c, const LeavesPage()));
    await tester.pumpAndSettle();
    expect(find.text('A4'), findsOneWidget); // the admin sees Bob's request

    // Same app instance, as HomeShell does it: leave the page, log out.
    await tester.pumpWidget(_app(c, const SizedBox()));
    await auth.logout();
    await auth.login('anna', 'x');
    await tester.pumpWidget(_app(c, const LeavesPage()));
    await tester.pumpAndSettle();

    expect(find.text('A4'), findsNothing, reason: 'the admin\'s list leaked to the employee');
    expect(leaves.listOwnCalls, 1, reason: 'the new user\'s own list was never fetched');
  });

  test('inactive_403_ends_session', () async {
    final (:c, :backend, :tokens) = _realSession();
    final auth = c.read(authControllerProvider.notifier);
    expect(await auth.login('anna', 'x'), isTrue);
    expect(backend.meCalls, 1);

    // An admin disables Anna; her next request comes back 403.
    backend.inactive = true;
    await expectLater(c.read(dioProvider).get('/leaves'), throwsA(isA<DioException>()));
    await pumpEventQueue();

    expect(backend.meCalls, 2, reason: 'a 403 is confirmed with GET /users/me');
    final state = c.read(authControllerProvider);
    expect(state.user, isNull);
    expect(state.error, 'account_inactive');
    expect(tokens.token, isNull);
    expect(const AppLocalizations(Locale('en')).authError(state.error), isNot('account_inactive'));
    expect(const AppLocalizations(Locale('vi')).authError(state.error), isNot('account_inactive'));
  });

  test('a 403 for a still-active account keeps the session', () async {
    final (:c, :backend, :tokens) = _realSession();
    final auth = c.read(authControllerProvider.notifier);
    await auth.login('anna', 'x');
    // Every auth state change rebuilds HomeShell and pings the router.
    var authNotifications = 0;
    c.listen(authControllerProvider, (_, _) => authNotifications++);

    // An employee hitting an admin route: forbidden, but still active.
    await expectLater(c.read(dioProvider).get('/users'), throwsA(isA<DioException>()));
    await pumpEventQueue();

    expect(backend.meCalls, 2);
    expect(authNotifications, 0, reason: 'an unchanged user must not emit a new auth state');
    expect(c.read(authControllerProvider).user?.id, _anna.id);
    expect(tokens.token, 'jwt');
  });
}
