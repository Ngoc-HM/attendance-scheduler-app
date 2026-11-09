// Review 2026-11-08 fixes on the schedule screen (A3, D3, C2 client side,
// swap picker and schedule toasts): the grid always belongs to the month on
// screen, Publish targets that month and shows the rule violations first,
// the admin shift-change panel names requester and counterpart, approving
// shows the backend warnings and reloads the grid, and the swap picker
// offers same-role colleagues only.

import 'dart:async';
import 'dart:core';
import 'dart:core' as core;

import 'package:attendance_scheduler_app/core/constants/shift_codes.dart';
import 'package:attendance_scheduler_app/core/network/api_exception.dart';
import 'package:attendance_scheduler_app/core/storage/locale_storage.dart';
import 'package:attendance_scheduler_app/design_system/design_system.dart';
import 'package:attendance_scheduler_app/features/auth/data/models/user_model.dart';
import 'package:attendance_scheduler_app/features/auth/domain/entities/user.dart';
import 'package:attendance_scheduler_app/features/auth/domain/repositories/auth_repository.dart';
import 'package:attendance_scheduler_app/features/auth/presentation/providers/auth_provider.dart';
import 'package:attendance_scheduler_app/features/flights/data/datasources/flights_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/flights/data/models/flight_day_model.dart';
import 'package:attendance_scheduler_app/features/schedule/data/datasources/schedule_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/schedule/data/datasources/self_arrange_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/schedule/domain/entities/schedule_entities.dart';
import 'package:attendance_scheduler_app/features/schedule/domain/entities/self_arrange_entities.dart';
import 'package:attendance_scheduler_app/features/schedule/presentation/pages/schedule_page.dart';
import 'package:attendance_scheduler_app/features/schedule/presentation/providers/schedule_provider.dart';
import 'package:attendance_scheduler_app/features/schedule/presentation/widgets/shift_change_dialog.dart';
import 'package:attendance_scheduler_app/features/users/data/user_management_datasource.dart';
import 'package:attendance_scheduler_app/i18n/app_localizations.dart';
import 'package:attendance_scheduler_app/i18n/locale_provider.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

const _admin = User(
  id: 1,
  username: 'boss',
  fullName: 'Boss',
  role: UserRole.m,
  status: 'active',
  code: 'M1',
);

const _employee = User(
  id: 7,
  username: 'tuan',
  fullName: 'Tuan Nguyen',
  role: UserRole.t,
  status: 'active',
  code: 'T1',
);

const _a1 = 8;
const _t2 = 9;

const _june = 6;
const _july = 7;

final _serverError =
    const AppLocalizations(Locale('en')).text('requestServerError');

const _generateHint =
    'No schedule for this month. Tap "Generate schedule" to build one.';

class _NoopAuthRepository implements AuthRepository {
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class _SignedInAuthController extends AuthController {
  _SignedInAuthController(User user)
    : super(_NoopAuthRepository(), LocaleController(LocaleStorage())) {
    state = AuthState(user: user);
  }
}

class _FakeScheduleDataSource extends ScheduleRemoteDataSource {
  _FakeScheduleDataSource({
    this.julyExists = false,
    this.violations = const [],
    this.requests = const [],
    this.decideWarnings = const [],
    this.publishError,
    this.fetchError,
    this.violationsError,
    this.generateError,
    this.generateResult,
  }) : super(Dio());

  final bool julyExists;
  final List<ConstraintViolation> violations;
  final List<ShiftChangeRequest> requests;
  final List<String> decideWarnings;
  final Object? publishError;

  /// Thrown by [fetchViolations] (endpoint missing, 5xx, network).
  final Object? violationsError;

  /// Thrown by [generate].
  final Object? generateError;

  /// Returned by [generate] when [generateError] is null.
  final ScheduleResult? generateResult;

  /// Holds the [override] response until completed.
  Completer<void>? overrideGate;

  /// Holds the [decideShiftChange] response until completed, so frames run
  /// while the request is in flight (as with a real server).
  Completer<void>? decideGate;

  /// Thrown by every [fetchSchedule] call (instead of the 404 for July).
  final Object? fetchError;

  /// Month → completer that holds that month's response until completed.
  final held = <int, Completer<void>>{};

  final fetchedMonths = <int>[];
  final published = <int>[];
  final violationCalls = <int>[];
  final decided = <(int, String)>[];

  static int idFor(int month) => 600 + month;

  @core.override
  Future<MonthlySchedule> fetchSchedule(int year, int month) async {
    fetchedMonths.add(month);
    final gate = held[month];
    if (gate != null) await gate.future;
    if (fetchError != null) throw fetchError!;
    if (month == _july && !julyExists) {
      throw const ApiException('Schedule not found.', statusCode: 404);
    }
    final days = DateTime(year, month + 1, 0).day;
    return MonthlySchedule(
      id: idFor(month),
      year: year,
      month: month,
      status: ScheduleStatus.draft,
      assignments: [
        for (var d = 1; d <= days; d++)
          ShiftAssignment(
            id: d,
            // June rosters A1, July rosters T2: each month has its own column.
            userId: month == _june ? _a1 : _t2,
            workDate: DateTime(year, month, d),
            code: month == _june ? 'A' : 'AD',
            isManualOverride: false,
          ),
      ],
    );
  }

  @core.override
  Future<List<ConstraintViolation>> fetchViolations(int scheduleId) async {
    violationCalls.add(scheduleId);
    if (violationsError != null) throw violationsError!;
    return violations;
  }

  @core.override
  Future<ScheduleResult> generate({
    required int year,
    required int month,
    bool force = false,
  }) async {
    if (generateError == null && generateResult != null) return generateResult!;
    throw generateError ?? StateError('generate not stubbed');
  }

  @core.override
  Future<ScheduleResult> override({
    required int scheduleId,
    required int userId,
    required DateTime workDate,
    required String code,
  }) async {
    final gate = overrideGate;
    if (gate != null) await gate.future;
    return ScheduleResult(
      feasible: true,
      violations: const [
        ConstraintViolation(rule: 'cover', message: 'cover below minimum'),
      ],
      schedule: MonthlySchedule(
        id: scheduleId,
        year: workDate.year,
        month: workDate.month,
        status: ScheduleStatus.draft,
        assignments: const [],
      ),
    );
  }

  @core.override
  Future<MonthlySchedule> publish(int scheduleId) async {
    if (publishError != null) throw publishError!;
    published.add(scheduleId);
    final month = scheduleId - 600;
    return MonthlySchedule(
      id: scheduleId,
      year: 2026,
      month: month,
      status: ScheduleStatus.published,
      assignments: const [],
    );
  }

  @core.override
  Future<List<ShiftChangeRequest>> fetchShiftChanges({bool all = false}) async =>
      [
        // A reload after a decision lists that request as decided.
        for (final r in requests)
          if (decided.where((d) => d.$1 == r.id).firstOrNull case final d?)
            ShiftChangeRequest(
              id: r.id,
              requesterId: r.requesterId,
              workDate: r.workDate,
              kind: r.kind,
              status: d.$2,
              strictReview: r.strictReview,
              warnings: r.warnings,
              requestedCode: r.requestedCode,
              counterpartUserId: r.counterpartUserId,
            )
          else
            r,
      ];

  @core.override
  Future<ShiftChangeRequest> decideShiftChange({
    required int id,
    required String status,
  }) async {
    final gate = decideGate;
    if (gate != null) await gate.future;
    decided.add((id, status));
    final r = requests.firstWhere((r) => r.id == id);
    return ShiftChangeRequest(
      id: r.id,
      requesterId: r.requesterId,
      workDate: r.workDate,
      kind: r.kind,
      status: status,
      strictReview: r.strictReview,
      warnings: decideWarnings,
      requestedCode: r.requestedCode,
      counterpartUserId: r.counterpartUserId,
    );
  }
}

class _FakeUserDataSource implements UserManagementDataSource {
  @override
  Future<List<UserModel>> list() async => const [
    UserModel(
      id: _a1,
      username: 'anh',
      fullName: 'Anh',
      role: UserRole.a,
      status: 'active',
      code: 'A1',
    ),
    UserModel(
      id: 7,
      username: 'tuan',
      fullName: 'Tuan',
      role: UserRole.t,
      status: 'active',
      code: 'T1',
    ),
    UserModel(
      id: _t2,
      username: 'thu',
      fullName: 'Thu',
      role: UserRole.t,
      status: 'active',
      code: 'T2',
    ),
  ];

  /// GET /users/directory: active users only (backend filter), code + role.
  @override
  Future<List<UserDirectoryEntry>> directory() async => const [
    UserDirectoryEntry(id: _a1, code: 'A1', role: UserRole.a),
    UserDirectoryEntry(id: 1, code: 'M1', role: UserRole.m),
    UserDirectoryEntry(id: 7, code: 'T1', role: UserRole.t),
    UserDirectoryEntry(id: 12, code: 'T10', role: UserRole.t),
    UserDirectoryEntry(id: _t2, code: 'T2', role: UserRole.t),
    UserDirectoryEntry(id: 11, code: 'F1', role: UserRole.f),
  ];

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

/// GET /users fails (admin view); the directory still works.
class _FailingUserDataSource extends _FakeUserDataSource {
  @override
  Future<List<UserModel>> list() async =>
      throw const ApiException('Database unavailable', statusCode: 503);
}

class _FakeFlightsDataSource extends FlightsRemoteDataSource {
  _FakeFlightsDataSource() : super(Dio());

  @override
  Future<List<FlightDayModel>> listDays(int year, int month) async => [];
}

class _FakeSelfArrangeDataSource extends SelfArrangeRemoteDataSource {
  _FakeSelfArrangeDataSource({
    this.batches = const [],
    this.decideWarnings = const [],
  }) : super(Dio());

  final List<SelfArrangeBatch> batches;
  final List<String> decideWarnings;
  final decided = <(int, String)>[];

  /// Holds the [decide] response until completed.
  Completer<void>? decideGate;

  @override
  Future<List<SelfArrangeBatch>> list({
    bool all = false,
    bool pendingOnly = false,
  }) async => [
    // The backend no longer lists a batch once it is decided.
    for (final b in batches)
      if (!decided.any((d) => d.$1 == b.id)) b,
  ];

  @override
  Future<SelfArrangeBatch> decide({
    required int id,
    required String status,
  }) async {
    final gate = decideGate;
    if (gate != null) await gate.future;
    decided.add((id, status));
    final b = batches.firstWhere((b) => b.id == id);
    return SelfArrangeBatch(
      id: b.id,
      requesterId: b.requesterId,
      year: b.year,
      month: b.month,
      changes: b.changes,
      status: status,
      warnings: decideWarnings,
    );
  }
}

Future<void> _pump(
  WidgetTester tester, {
  required User user,
  required _FakeScheduleDataSource ds,
  _FakeSelfArrangeDataSource? selfArrange,
  UserManagementDataSource? users,
  int initialMonth = _june,
}) async {
  await tester.binding.setSurfaceSize(const Size(1400, 1800));
  addTearDown(() => tester.binding.setSurfaceSize(null));
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        authControllerProvider.overrideWith(
          (ref) => _SignedInAuthController(user),
        ),
        scheduleRemoteDataSourceProvider.overrideWithValue(ds),
        userManagementDataSourceProvider.overrideWithValue(
          users ?? _FakeUserDataSource(),
        ),
        flightsDataSourceProvider.overrideWithValue(_FakeFlightsDataSource()),
        selfArrangeRemoteDataSourceProvider.overrideWithValue(
          selfArrange ?? _FakeSelfArrangeDataSource(),
        ),
      ],
      child: MaterialApp(
        localizationsDelegates: const [
          AppLocalizations.delegate,
          DefaultMaterialLocalizations.delegate,
          DefaultWidgetsLocalizations.delegate,
        ],
        supportedLocales: AppLocalizations.supportedLocales,
        locale: const Locale('en'),
        home: Scaffold(
          body: SchedulePage(initialMonth: DateTime(2026, initialMonth)),
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

Future<void> _nextMonth(WidgetTester tester) async {
  await tester.tap(find.byIcon(Icons.chevron_right));
  await tester.pumpAndSettle();
}

/// The Publish button is either absent or rendered disabled.
bool _publishEnabled(WidgetTester tester) {
  final button = find.ancestor(
    of: find.text('Publish schedule'),
    matching: find.byWidgetPredicate((w) => w is ButtonStyleButton),
  );
  if (button.evaluate().isEmpty) return false;
  return tester.widget<ButtonStyleButton>(button.first).onPressed != null;
}

/// Let the auto-dismiss timer of a DsFeedback toast run out.
Future<void> _drainToast(WidgetTester tester) async {
  await tester.pump(const Duration(seconds: 9));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('switching_to_ungenerated_month_clears_grid', (tester) async {
    final ds = _FakeScheduleDataSource();
    await _pump(tester, user: _admin, ds: ds);

    expect(find.text('A1'), findsOneWidget, reason: 'June roster column');
    expect(_publishEnabled(tester), isTrue);

    await _nextMonth(tester);

    expect(ds.fetchedMonths, [_june, _july]);
    expect(find.textContaining('July 2026'), findsWidgets);
    expect(find.text('A1'), findsNothing, reason: 'no stale June column');
    expect(find.text(_generateHint), findsOneWidget);
    expect(_publishEnabled(tester), isFalse);
  });

  testWidgets('admin_load_failure_shows_error_instead_of_generate_hint', (
    tester,
  ) async {
    final ds = _FakeScheduleDataSource(
      fetchError: const ApiException('Database unavailable', statusCode: 503),
    );
    await _pump(tester, user: _admin, ds: ds);

    expect(find.text(_generateHint), findsNothing);
    // A 5xx reads as the translated server error, never its body.
    expect(find.textContaining(_serverError), findsOneWidget);
    expect(find.textContaining('Database unavailable'), findsNothing);
    expect(find.textContaining('ApiException'), findsNothing);
    expect(_publishEnabled(tester), isFalse);
  });

  testWidgets('publish_targets_month_on_screen', (tester) async {
    final ds = _FakeScheduleDataSource(julyExists: true);
    await _pump(tester, user: _admin, ds: ds);

    await _nextMonth(tester);
    expect(find.text('T2'), findsOneWidget, reason: 'July roster column');
    await tester.tap(find.text('Publish schedule'));
    await tester.pumpAndSettle();
    expect(ds.published, [_FakeScheduleDataSource.idFor(_july)]);
    await _drainToast(tester);
  });

  testWidgets('publish_never_targets_a_month_that_is_not_on_screen', (
    tester,
  ) async {
    // The A3 reproduction: July has no schedule, June was loaded before.
    final ds = _FakeScheduleDataSource();
    await _pump(tester, user: _admin, ds: ds);
    await _nextMonth(tester);

    final publish = find.text('Publish schedule');
    if (publish.evaluate().isNotEmpty) {
      await tester.tap(publish, warnIfMissed: false);
      await tester.pumpAndSettle();
    }
    // Even a direct call for the month on screen has nothing to publish.
    final container = ProviderScope.containerOf(
      tester.element(find.byType(SchedulePage)),
    );
    final ok = await container
        .read(scheduleControllerProvider.notifier)
        .publish(year: 2026, month: _july);

    expect(ok, isFalse);
    expect(ds.published, isEmpty, reason: 'June must not be published');
    await _drainToast(tester);
  });

  test('late_response_for_previous_month_is_ignored', () async {
    final ds = _FakeScheduleDataSource(julyExists: true)
      ..held[_june] = Completer<void>();
    final container = ProviderContainer(
      overrides: [
        scheduleRemoteDataSourceProvider.overrideWithValue(ds),
        userManagementDataSourceProvider.overrideWithValue(
          _FakeUserDataSource(),
        ),
      ],
    );
    addTearDown(container.dispose);
    final controller = container.read(scheduleControllerProvider.notifier);

    final june = controller.load(2026, _june, isAdmin: true);
    await controller.load(2026, _july, isAdmin: true);
    ds.held[_june]!.complete();
    await june;

    final state = container.read(scheduleControllerProvider);
    expect(state.schedule?.month, _july);
    expect(state.isLoading, isFalse);
  });

  test('late_override_response_does_not_replace_the_visible_month', () async {
    final ds = _FakeScheduleDataSource(julyExists: true);
    final container = ProviderContainer(
      overrides: [
        scheduleRemoteDataSourceProvider.overrideWithValue(ds),
        userManagementDataSourceProvider.overrideWithValue(
          _FakeUserDataSource(),
        ),
      ],
    );
    addTearDown(container.dispose);
    final controller = container.read(scheduleControllerProvider.notifier);
    await controller.load(2026, _june, isAdmin: true);

    // The June edit is in flight when the admin moves to July.
    ds.overrideGate = Completer<void>();
    final edit = controller.overrideCell(
      userId: _a1,
      workDate: DateTime(2026, _june, 3),
      code: 'X',
    );
    await controller.load(2026, _july, isAdmin: true);
    final violationCallsBefore = ds.violationCalls.length;
    ds.overrideGate!.complete();
    final warnings = await edit;

    expect(warnings, ['cover below minimum'], reason: 'still reported');
    final state = container.read(scheduleControllerProvider);
    expect(state.schedule?.id, _FakeScheduleDataSource.idFor(_july));
    expect(state.schedule?.assignments, isNotEmpty);
    expect(state.isMutating, isFalse);
    expect(ds.violationCalls.length, violationCallsBefore,
        reason: 'no re-check written for a month that is not on screen');
  });

  testWidgets('publish_shows_violations_before_confirm', (tester) async {
    final ds = _FakeScheduleDataSource(
      violations: [
        ConstraintViolation(
          day: DateTime(2026, 6, 3),
          userId: _a1,
          rule: 'arrival_cover',
          message: 'Arrival cover missing',
        ),
        const ConstraintViolation(
          rule: 'off_chain',
          message: 'Off chain too long',
        ),
      ],
    );
    await _pump(tester, user: _admin, ds: ds);

    // Loaded with the month: the admin sees the count before publishing.
    expect(ds.violationCalls, [_FakeScheduleDataSource.idFor(_june)]);
    expect(find.textContaining('2 rule violation(s)'), findsOneWidget);

    await tester.tap(find.text('Publish schedule'));
    await tester.pumpAndSettle();

    expect(find.byType(AlertDialog), findsOneWidget);
    expect(find.text('2026-06-03 · A1 — Arrival cover missing'), findsOneWidget);
    expect(find.text('Off chain too long'), findsOneWidget);
    expect(ds.published, isEmpty, reason: 'nothing published before confirm');

    await tester.tap(find.text('Cancel'));
    await tester.pumpAndSettle();
    expect(ds.published, isEmpty);

    await tester.tap(find.text('Publish schedule'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Publish anyway'));
    await tester.pumpAndSettle();

    expect(ds.published, [_FakeScheduleDataSource.idFor(_june)]);
    expect(find.text('Schedule published.'), findsOneWidget);
    await _drainToast(tester);
  });

  testWidgets('publish_when_rules_check_fails_says_rules_not_checked', (
    tester,
  ) async {
    final ds = _FakeScheduleDataSource(
      violationsError: const ApiException('Not Found', statusCode: 404),
    );
    await _pump(tester, user: _admin, ds: ds);

    await tester.tap(find.text('Publish schedule'));
    await tester.pumpAndSettle();

    expect(find.byType(AlertDialog), findsOneWidget);
    expect(find.text('Rules not checked'), findsOneWidget);
    expect(find.text('Publish with rule violations?'), findsNothing);
    expect(
      find.text('The rules could not be checked right now. Publish anyway?'),
      findsOneWidget,
    );

    await tester.tap(find.text('Publish anyway'));
    await tester.pumpAndSettle();
    expect(ds.published, [_FakeScheduleDataSource.idFor(_june)]);
    await _drainToast(tester);
  });

  testWidgets('failed_generate_does_not_read_as_load_failure', (tester) async {
    final ds = _FakeScheduleDataSource(
      generateError: const ApiException('Solver crashed', statusCode: 500),
    );
    await _pump(tester, user: _admin, ds: ds);
    await _nextMonth(tester); // July: no schedule yet (404)

    await tester.tap(find.text('Generate schedule'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Generate anyway')); // no flights this month
    await tester.pumpAndSettle();

    expect(find.text(_serverError), findsOneWidget, reason: 'toast');
    expect(find.text('Solver crashed'), findsNothing);
    expect(find.textContaining('Could not load the schedule'), findsNothing);
    expect(find.text(_generateHint), findsOneWidget);
    await _drainToast(tester);
  });

  testWidgets('publish_error_toast_shows_backend_message', (tester) async {
    final ds = _FakeScheduleDataSource(
      publishError: const ApiException(
        'This month is already published.',
        statusCode: 409,
      ),
    );
    await _pump(tester, user: _admin, ds: ds);

    await tester.tap(find.text('Publish schedule'));
    await tester.pumpAndSettle();

    expect(find.text('This month is already published.'), findsOneWidget);
    expect(find.textContaining('ApiException'), findsNothing);
    await _drainToast(tester);
  });

  group('admin shift-change panel', () {
    final requests = [
      ShiftChangeRequest(
        id: 31,
        requesterId: 7,
        workDate: DateTime(2026, 6, 5),
        kind: 'swap_with',
        status: 'pending',
        strictReview: false,
        warnings: const [],
        counterpartUserId: _t2,
      ),
      ShiftChangeRequest(
        id: 32,
        requesterId: _a1,
        workDate: DateTime(2026, 6, 9),
        kind: 'change_code',
        status: 'pending',
        strictReview: true,
        warnings: const [],
        requestedCode: 'X',
      ),
    ];

    Future<void> openPanel(WidgetTester tester) async {
      await tester.tap(find.text('Shift-change requests'));
      await tester.pumpAndSettle();
    }

    testWidgets('pending_panel_shows_requester_and_counterpart_codes', (
      tester,
    ) async {
      final ds = _FakeScheduleDataSource(requests: requests);
      await _pump(tester, user: _admin, ds: ds);
      await openPanel(tester);

      expect(
        find.text('T1 · Swap with colleague · 2026-06-05'),
        findsOneWidget,
      );
      expect(find.text('Swap partner: T2'), findsOneWidget);
      expect(find.text('A1 · Change code · 2026-06-09'), findsOneWidget);
      expect(find.text('New shift code: X'), findsOneWidget);
      expect(find.textContaining('swap_with'), findsNothing);
    });

    testWidgets('approve_shows_warnings_and_reloads_grid', (tester) async {
      final ds = _FakeScheduleDataSource(
        requests: requests,
        decideWarnings: const ['2026-06-05: arrival cover below minimum'],
      );
      await _pump(tester, user: _admin, ds: ds);
      await openPanel(tester);
      expect(ds.fetchedMonths, [_june]);

      await tester.tap(find.byTooltip('Approve').first);
      await tester.pumpAndSettle();

      expect(ds.decided, [(31, 'approved')]);
      expect(find.byType(AlertDialog), findsOneWidget);
      expect(
        find.text('2026-06-05: arrival cover below minimum'),
        findsOneWidget,
      );

      await tester.tap(find.text('Close'));
      await tester.pumpAndSettle();

      expect(ds.fetchedMonths, [_june, _june], reason: 'grid reloaded');
      expect(find.text('A1'), findsWidgets);
    });

    testWidgets('approve_without_warnings_toasts_and_reloads_grid', (
      tester,
    ) async {
      final ds = _FakeScheduleDataSource(requests: requests);
      await _pump(tester, user: _admin, ds: ds);
      await openPanel(tester);

      await tester.tap(find.byTooltip('Approve').first);
      await tester.pumpAndSettle();

      expect(find.byType(AlertDialog), findsNothing);
      expect(find.text('Request approved.'), findsOneWidget);
      expect(ds.fetchedMonths, [_june, _june]);
      await _drainToast(tester);
    });
  });

  testWidgets('swap_picker_lists_same_role_active_colleagues_only', (
    tester,
  ) async {
    // "Active only" is enforced by the backend: GET /users/directory
    // (user_service.list_directory) returns active users only and carries
    // no status, so the fake directory below is already active-only and the
    // dialog filters by role.
    final people = await _FakeUserDataSource().directory();
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          scheduleRemoteDataSourceProvider.overrideWithValue(
            _FakeScheduleDataSource(),
          ),
        ],
        child: MaterialApp(
          localizationsDelegates: const [
            AppLocalizations.delegate,
            DefaultMaterialLocalizations.delegate,
            DefaultWidgetsLocalizations.delegate,
          ],
          supportedLocales: AppLocalizations.supportedLocales,
          locale: const Locale('en'),
          home: Scaffold(
            body: ShiftChangeRequestDialog(
              workDate: DateTime(2026, 6, 3),
              role: _employee.role,
              people: people,
              currentUserId: _employee.id,
            ),
          ),
        ),
      ),
    );
    await tester.tap(find.text('Swap with colleague'));
    await tester.pumpAndSettle();

    final picker = tester.widget<DropdownButton<int>>(
      find.byType(DropdownButton<int>),
    );
    // T colleagues only (no A1, M1, F1, not the requester T1), natural order.
    expect(picker.items!.map((item) => (item.child as Text).data), [
      'T2',
      'T10',
    ]);
    expect(picker.items!.map((item) => item.value), [_t2, 12]);
  });

  group('ungenerated month (bug: columns read "ID n" after generate)', () {
    ProviderContainer containerWith(
      _FakeScheduleDataSource ds, {
      UserManagementDataSource? users,
    }) {
      final container = ProviderContainer(
        overrides: [
          scheduleRemoteDataSourceProvider.overrideWithValue(ds),
          userManagementDataSourceProvider.overrideWithValue(
            users ?? _FakeUserDataSource(),
          ),
        ],
      );
      addTearDown(container.dispose);
      return container;
    }

    test('people are kept when the month has no schedule', () async {
      final container = containerWith(_FakeScheduleDataSource());
      await container
          .read(scheduleControllerProvider.notifier)
          .load(2026, _july, isAdmin: true);

      final state = container.read(scheduleControllerProvider);
      expect(state.schedule, isNull);
      expect(state.loadErrorStatus, 404, reason: 'still "not generated"');
      expect(state.people.map((p) => p.code), ['A1', 'T1', 'T2']);
    });

    test('employee on an unpublished month keeps the directory', () async {
      final container = containerWith(_FakeScheduleDataSource());
      await container
          .read(scheduleControllerProvider.notifier)
          .load(2026, _july);

      final state = container.read(scheduleControllerProvider);
      expect(state.loadErrorStatus, 404);
      expect(state.people.map((p) => p.code), contains('T2'));
    });

    test('admin user-list failure is still a load error', () async {
      for (final month in [_june, _july]) {
        final container = containerWith(
          _FakeScheduleDataSource(),
          users: _FailingUserDataSource(),
        );
        await container
            .read(scheduleControllerProvider.notifier)
            .load(2026, month, isAdmin: true);

        final state = container.read(scheduleControllerProvider);
        expect(state.schedule, isNull, reason: 'month $month');
        expect(state.loadError, isA<ApiException>(), reason: 'month $month');
        expect(state.loadErrorStatus, 503, reason: 'month $month');
      }
    });

    testWidgets("generate on an ungenerated month shows codes and the role's "
        'own codes', (tester) async {
      final ds = _FakeScheduleDataSource(
        generateResult: ScheduleResult(
          feasible: true,
          violations: const [],
          schedule: MonthlySchedule(
            id: _FakeScheduleDataSource.idFor(_july),
            year: 2026,
            month: _july,
            status: ScheduleStatus.draft,
            assignments: [
              for (var d = 1; d <= 31; d++) ...[
                ShiftAssignment(
                  id: d,
                  userId: _a1,
                  workDate: DateTime(2026, _july, d),
                  code: 'A',
                  isManualOverride: false,
                ),
                ShiftAssignment(
                  id: 100 + d,
                  userId: _t2,
                  workDate: DateTime(2026, _july, d),
                  code: 'AD',
                  isManualOverride: false,
                ),
              ],
            ],
          ),
        ),
      );
      // Fresh login straight onto the ungenerated month.
      await _pump(tester, user: _admin, ds: ds, initialMonth: _july);
      expect(find.text(_generateHint), findsOneWidget);

      await tester.tap(find.text('Generate schedule'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Generate anyway')); // no flights this month
      await tester.pumpAndSettle();

      expect(find.text('A1'), findsOneWidget, reason: 'column header');
      expect(find.text('T2'), findsOneWidget, reason: 'column header');
      expect(find.textContaining('ID '), findsNothing);

      // Column 0 is A1 (role A): its cell offers the A role's codes.
      final a1Cell = find
          .descendant(
            of: find.byType(InkWell),
            matching: find.byType(DsShiftBadge),
          )
          .at(2 * 1);
      await tester.ensureVisible(a1Cell);
      await tester.tap(a1Cell);
      await tester.pumpAndSettle();
      final offered = tester
          .widget<DropdownButton<ShiftCode>>(
            find.byType(DropdownButton<ShiftCode>),
          )
          .items!
          .map((item) => item.value)
          .toList();
      expect(offered, ShiftCodeX.plannedCodesFor(UserRole.a));
      expect(offered, containsAll([ShiftCode.a, ShiftCode.d]));
      expect(offered, isNot(contains(ShiftCode.ad)));

      await tester.tap(find.text('Cancel'));
      await tester.pumpAndSettle();
      await _drainToast(tester);
    });
  });

  group('deciding the last pending request (bug: no feedback, stale grid)', () {
    final only = ShiftChangeRequest(
      id: 41,
      requesterId: _a1,
      workDate: DateTime(2026, 6, 9),
      kind: 'change_code',
      status: 'pending',
      strictReview: false,
      warnings: const [],
      requestedCode: 'X',
    );

    Future<void> openPanel(WidgetTester tester) async {
      await tester.tap(find.text('Shift-change requests'));
      await tester.pumpAndSettle();
    }

    /// Taps [tooltip] while the server holds the answer for a few frames.
    Future<void> decide(
      WidgetTester tester,
      _FakeScheduleDataSource ds,
      String tooltip,
    ) async {
      ds.decideGate = Completer<void>();
      await tester.tap(find.byTooltip(tooltip));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 200));
      ds.decideGate!.complete();
      await tester.pumpAndSettle();
    }

    testWidgets('approving the only shift change toasts and reloads once', (
      tester,
    ) async {
      final ds = _FakeScheduleDataSource(requests: [only]);
      await _pump(tester, user: _admin, ds: ds);
      await openPanel(tester);

      await decide(tester, ds, 'Approve');

      expect(ds.decided, [(41, 'approved')]);
      expect(find.text('Request approved.'), findsOneWidget);
      expect(ds.fetchedMonths, [_june, _june], reason: 'grid reloaded once');
      expect(find.text('No pending shift-change requests.'), findsOneWidget);
      await _drainToast(tester);
    });

    testWidgets('rejecting the only shift change toasts', (tester) async {
      final ds = _FakeScheduleDataSource(requests: [only]);
      await _pump(tester, user: _admin, ds: ds);
      await openPanel(tester);

      await decide(tester, ds, 'Reject');

      expect(ds.decided, [(41, 'rejected')]);
      expect(find.text('Request rejected.'), findsOneWidget);
      expect(ds.fetchedMonths, [_june], reason: 'a rejection changes no cell');
      await _drainToast(tester);
    });

    testWidgets('approving the only shift change with warnings shows them', (
      tester,
    ) async {
      final ds = _FakeScheduleDataSource(
        requests: [only],
        decideWarnings: const ['2026-06-09: departure cover below minimum'],
      );
      await _pump(tester, user: _admin, ds: ds);
      await openPanel(tester);

      await decide(tester, ds, 'Approve');

      expect(find.byType(AlertDialog), findsOneWidget);
      expect(
        find.text('2026-06-09: departure cover below minimum'),
        findsOneWidget,
      );
      await tester.tap(find.text('Close'));
      await tester.pumpAndSettle();
      expect(ds.fetchedMonths, [_june, _june], reason: 'grid reloaded once');
    });

    SelfArrangeBatch batch() => SelfArrangeBatch(
      id: 51,
      requesterId: _t2,
      year: 2026,
      month: _june,
      changes: [SelfArrangeChange(workDate: DateTime(2026, 6, 4), code: 'X')],
      status: 'pending',
    );

    for (final (status, tooltip) in [
      ('approved', 'Approve'),
      ('rejected', 'Reject'),
    ]) {
      testWidgets('deciding ($status) the only self-arrange batch toasts and '
          'reloads once', (tester) async {
        final ds = _FakeScheduleDataSource();
        final selfArrange = _FakeSelfArrangeDataSource(batches: [batch()]);
        await _pump(tester, user: _admin, ds: ds, selfArrange: selfArrange);
        await openPanel(tester);

        await tester.tap(find.byTooltip(tooltip));
        await tester.pumpAndSettle();

        expect(selfArrange.decided, [(51, status)]);
        expect(find.text('Request decided.'), findsOneWidget);
        expect(ds.fetchedMonths, [_june, _june], reason: 'grid reloaded once');
        await _drainToast(tester);
      });
    }

    testWidgets('approving the only self-arrange batch shows its warnings', (
      tester,
    ) async {
      final ds = _FakeScheduleDataSource();
      final selfArrange = _FakeSelfArrangeDataSource(
        batches: [batch()],
        decideWarnings: const ['2026-06-04: off chain too long'],
      );
      await _pump(tester, user: _admin, ds: ds, selfArrange: selfArrange);
      await openPanel(tester);

      await tester.tap(find.byTooltip('Approve'));
      await tester.pumpAndSettle();

      expect(
        find.textContaining('2026-06-04: off chain too long'),
        findsOneWidget,
      );
      expect(ds.fetchedMonths, [_june, _june], reason: 'grid reloaded once');
      await _drainToast(tester);
    });
    // The row's context is gone before the answer arrives: the feedback and
    // the reload must not depend on it.
    testWidgets('closing the panel while a shift change is decided still '
        'toasts and reloads', (tester) async {
      final ds = _FakeScheduleDataSource(requests: [only]);
      await _pump(tester, user: _admin, ds: ds);
      await openPanel(tester);

      ds.decideGate = Completer<void>();
      await tester.tap(find.byTooltip('Approve'));
      await tester.pump();
      await openPanel(tester); // toggles the panel closed
      expect(find.byTooltip('Approve'), findsNothing);
      ds.decideGate!.complete();
      await tester.pumpAndSettle();

      expect(find.text('Request approved.'), findsOneWidget);
      expect(ds.fetchedMonths, [_june, _june], reason: 'grid reloaded once');
      await _drainToast(tester);
    });

    testWidgets('closing the panel while a self-arrange batch is decided '
        'still toasts and reloads', (tester) async {
      final ds = _FakeScheduleDataSource();
      final selfArrange = _FakeSelfArrangeDataSource(batches: [batch()]);
      await _pump(tester, user: _admin, ds: ds, selfArrange: selfArrange);
      await openPanel(tester);

      selfArrange.decideGate = Completer<void>();
      await tester.tap(find.byTooltip('Approve'));
      await tester.pump();
      await openPanel(tester); // toggles the panel closed
      expect(find.byTooltip('Approve'), findsNothing);
      selfArrange.decideGate!.complete();
      await tester.pumpAndSettle();

      expect(find.text('Request decided.'), findsOneWidget);
      expect(ds.fetchedMonths, [_june, _june], reason: 'grid reloaded once');
      await _drainToast(tester);
    });
  });
}
