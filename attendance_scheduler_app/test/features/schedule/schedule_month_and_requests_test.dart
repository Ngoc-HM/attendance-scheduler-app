// Review 2026-11-08 fixes on the schedule screen (A3, D3, C2 client side,
// swap picker and schedule toasts): the grid always belongs to the month on
// screen, Publish targets that month and shows the rule violations first,
// and the swap picker offers same-role colleagues only.
// Three-step swap (customer 2026-11-18): the colleague answers a swap first.
// The admin decides shift changes on the Approvals screen (owner
// 2026-11-20, see test/features/leaves/leaves_requests_inbox_test.dart): the
// schedule page has no request panel for them.

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
import 'package:attendance_scheduler_app/features/schedule/domain/entities/schedule_entities.dart';
import 'package:attendance_scheduler_app/features/schedule/presentation/pages/schedule_page.dart';
import 'package:attendance_scheduler_app/features/schedule/presentation/providers/schedule_provider.dart';
import 'package:attendance_scheduler_app/features/schedule/presentation/widgets/shift_change_dialog.dart';
import 'package:attendance_scheduler_app/features/users/data/user_management_datasource.dart';
import 'package:attendance_scheduler_app/i18n/app_localizations.dart';
import 'package:attendance_scheduler_app/i18n/locale_provider.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
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
    this.incoming = const [],
    this.respondError,
    this.publishError,
    this.fetchError,
    this.violationsError,
    this.generateError,
    this.generateResult,
  }) : super(Dio());

  final bool julyExists;
  final List<ConstraintViolation> violations;
  final List<ShiftChangeRequest> requests;

  /// Swaps waiting for the signed-in person's answer; an answered one
  /// leaves the list.
  final List<ShiftChangeRequest> incoming;

  /// Thrown by [respondToShiftChange].
  final Object? respondError;

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
  final responded = <(int, bool)>[];

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

  /// Calls of [fetchShiftChanges].
  int shiftChangeFetches = 0;

  @core.override
  Future<List<ShiftChangeRequest>> fetchShiftChanges({bool all = false}) async {
    shiftChangeFetches++;
    return [
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
              counterpartStatus: r.counterpartStatus,
            )
          else
            r,
    ];
  }

  @core.override
  Future<List<ShiftChangeRequest>> fetchIncomingShiftChanges() async => [
    for (final r in incoming)
      if (!responded.any((a) => a.$1 == r.id)) r,
  ];

  @core.override
  Future<ShiftChangeRequest> respondToShiftChange({
    required int id,
    required bool accept,
  }) async {
    if (respondError != null) throw respondError!;
    responded.add((id, accept));
    final r = incoming.firstWhere((r) => r.id == id);
    return ShiftChangeRequest(
      id: r.id,
      requesterId: r.requesterId,
      workDate: r.workDate,
      kind: r.kind,
      status: accept ? 'pending' : 'rejected',
      strictReview: r.strictReview,
      warnings: const [],
      counterpartUserId: r.counterpartUserId,
      counterpartStatus: accept ? 'approved' : 'rejected',
    );
  }

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
      warnings: const [],
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

Future<void> _pump(
  WidgetTester tester, {
  required User user,
  required _FakeScheduleDataSource ds,
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

  testWidgets('admin: no shift-change request toggle or panel', (
    tester,
  ) async {
    final ds = _FakeScheduleDataSource(
      requests: [
        ShiftChangeRequest(
          id: 32,
          requesterId: _a1,
          workDate: DateTime(2026, 6, 9),
          kind: 'change_code',
          status: 'pending',
          strictReview: false,
          warnings: const [],
          requestedCode: 'X',
        ),
      ],
    );
    await _pump(tester, user: _admin, ds: ds);

    expect(find.text('Shift-change requests'), findsNothing);
    expect(find.byTooltip('Approve'), findsNothing);
    expect(find.text('Approve'), findsNothing);
    expect(ds.shiftChangeFetches, 0, reason: 'decided on Approvals');
  });

  group('incoming swap panel (employee)', () {
    final asked = ShiftChangeRequest(
      id: 51,
      requesterId: _t2,
      workDate: DateTime(2026, 6, 12),
      kind: 'swap_with',
      status: 'pending',
      strictReview: false,
      warnings: const [],
      counterpartUserId: 7,
      counterpartStatus: 'pending',
      requesterShift: 'AD',
      counterpartShift: 'X',
    );

    testWidgets('hidden when no colleague asks', (tester) async {
      await _pump(tester, user: _employee, ds: _FakeScheduleDataSource());

      expect(find.text('Colleagues asking to swap shifts'), findsNothing);
      expect(find.text('Accept'), findsNothing);
      expect(find.text('My shift-change requests'), findsOneWidget);
    });

    for (final (label, accept, toast) in [
      ('Accept', true, 'Swap accepted. The admin decides next.'),
      ('Decline', false, 'Swap declined.'),
    ]) {
      testWidgets('$label answers the swap and the row leaves', (tester) async {
        final ds = _FakeScheduleDataSource(incoming: [asked]);
        await _pump(tester, user: _employee, ds: ds);

        expect(find.text('Colleagues asking to swap shifts'), findsOneWidget);
        expect(find.text('T2'), findsWidgets);
        expect(find.text('2026-06-12'), findsOneWidget);

        await tester.tap(find.text(label));
        await tester.pumpAndSettle();

        expect(ds.responded, [(51, accept)]);
        expect(find.text(toast), findsOneWidget);
        expect(find.text('2026-06-12'), findsNothing);
        expect(find.text('Colleagues asking to swap shifts'), findsNothing);
        await _drainToast(tester);
      });
    }

    testWidgets('shows the asker\'s and the own code of that day', (
      tester,
    ) async {
      final noCell = ShiftChangeRequest(
        id: 52,
        requesterId: _t2,
        workDate: DateTime(2026, 6, 13),
        kind: 'swap_with',
        status: 'pending',
        strictReview: false,
        warnings: const [],
        counterpartUserId: 7,
        counterpartStatus: 'pending',
        requesterShift: 'X',
      );
      final ds = _FakeScheduleDataSource(incoming: [asked, noCell]);
      await _pump(tester, user: _employee, ds: ds);

      Finder inPanel(Finder f) => find.descendant(
        of: find.byType(IncomingSwapRequestsPanel),
        matching: f,
      );
      expect(inPanel(find.text('Their shift')), findsOneWidget);
      expect(inPanel(find.text('Your shift')), findsOneWidget);
      final badges = tester
          .widgetList<DsShiftBadge>(inPanel(find.byType(DsShiftBadge)))
          .map((b) => b.code)
          .toList();
      // Row 51: T2 gives AD, I give X. Row 52: T2 gives X, I have no cell.
      expect(badges, [ShiftCode.ad, ShiftCode.x, ShiftCode.x]);
      expect(inPanel(find.text('—')), findsOneWidget);

      // The two code columns sit between the date and the actions.
      final dateX = tester.getCenter(find.text('2026-06-12')).dx;
      final theirX = tester
          .getCenter(inPanel(find.byType(DsShiftBadge)).first)
          .dx;
      final acceptX = tester.getCenter(find.text('Accept').first).dx;
      expect(dateX < theirX && theirX < acceptX, isTrue);
    });

    testWidgets('a failed answer keeps the row and says why', (tester) async {
      final ds = _FakeScheduleDataSource(
        incoming: [asked],
        respondError: const ApiException(
          'This shift-change request was already decided.',
          statusCode: 409,
        ),
      );
      await _pump(tester, user: _employee, ds: ds);

      await tester.tap(find.text('Accept'));
      await tester.pumpAndSettle();

      expect(
        find.text('This shift-change request was already decided.'),
        findsOneWidget,
      );
      expect(find.text('2026-06-12'), findsOneWidget);
      await _drainToast(tester);
    });

    testWidgets('own swap shows which step it is waiting for', (tester) async {
      ShiftChangeRequest mine(int id, String status, String? counterpart) =>
          ShiftChangeRequest(
            id: id,
            requesterId: 7,
            workDate: DateTime(2026, 6, id - 40),
            kind: 'swap_with',
            status: status,
            strictReview: false,
            warnings: const [],
            counterpartUserId: _t2,
            counterpartStatus: counterpart,
          );
      final ds = _FakeScheduleDataSource(
        requests: [
          mine(61, 'pending', 'pending'),
          mine(62, 'pending', 'approved'),
          mine(63, 'rejected', 'rejected'),
          mine(64, 'approved', 'approved'),
          mine(65, 'rejected', 'approved'),
        ],
      );
      await _pump(tester, user: _employee, ds: ds);

      expect(find.text('Waiting for colleague'), findsOneWidget);
      expect(find.text('Waiting for admin'), findsOneWidget);
      expect(find.text('Declined by colleague'), findsOneWidget);
      expect(find.text('Approved'), findsOneWidget);
      expect(find.text('Rejected'), findsOneWidget);
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

    final picker = tester.widget<DropdownButton<int?>>(
      find.byType(DropdownButton<int?>),
    );
    // T colleagues only (no A1, M1, F1, not the requester T1), natural order.
    expect(picker.items!.map((item) => (item.child as Text).data), [
      'T2',
      'T10',
    ]);
    expect(picker.items!.map((item) => item.value), [_t2, 12]);
  });

  group('shift-change form (owner 2026-11-20: show what a swap exchanges)', () {
    /// Opens the real corner form over a page, as the roster page does.
    /// T1 (the employee) has AD that day, T2 has X, T10 has no cell.
    Future<void> openForm(
      WidgetTester tester, {
      Locale locale = const Locale('en'),
      Map<int, String> codesOnDay = const {7: 'AD', _t2: 'X'},
    }) async {
      await tester.binding.setSurfaceSize(const Size(1000, 900));
      addTearDown(() => tester.binding.setSurfaceSize(null));
      final people = await _FakeUserDataSource().directory();
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            scheduleRemoteDataSourceProvider.overrideWithValue(
              _FakeScheduleDataSource(),
            ),
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
            locale: locale,
            home: Scaffold(
              body: Builder(
                builder: (context) => Center(
                  child: TextButton(
                    onPressed: () => showDsCornerDialog<bool>(
                      context: context,
                      builder: (_) => ShiftChangeRequestDialog(
                        workDate: DateTime(2026, 11, 4),
                        role: _employee.role,
                        people: people,
                        currentUserId: _employee.id,
                        codesOnDay: codesOnDay,
                      ),
                    ),
                    child: const Text('open'),
                  ),
                ),
              ),
            ),
          ),
        ),
      );
      await tester.tap(find.text('open'));
      await tester.pumpAndSettle();
    }

    Future<void> pickColleague(WidgetTester tester, String code) async {
      await tester.tap(find.byType(DropdownButtonFormField<int?>));
      await tester.pumpAndSettle();
      await tester.tap(find.text(code).last);
      await tester.pumpAndSettle();
    }

    bool submitEnabled(WidgetTester tester) => tester
        .widget<ButtonStyleButton>(
          find.ancestor(
            of: find.text('Submit request'),
            matching: find.byWidgetPredicate((w) => w is ButtonStyleButton),
          ),
        )
        .onPressed !=
        null;

    /// The row (fixed-height SizedBox) holding [label].
    Finder rowOf(String label) => find
        .ancestor(of: find.text(label), matching: find.byType(SizedBox))
        .first;

    testWidgets('own row first, both rows once a colleague is chosen', (
      tester,
    ) async {
      await openForm(tester);
      expect(find.text('Wed, 04 Nov 2026'), findsOneWidget);
      expect(find.text('Your shift'), findsNothing, reason: 'code change');

      await tester.tap(find.text('Swap with colleague'));
      await tester.pumpAndSettle();

      expect(find.text('Your shift'), findsOneWidget);
      expect(find.textContaining("'s shift"), findsNothing);
      expect(find.byType(DsShiftBadge), findsOneWidget);
      expect(submitEnabled(tester), isFalse, reason: 'no colleague yet');

      await pickColleague(tester, 'T2');

      expect(find.text("T2's shift"), findsOneWidget);
      final badges = tester
          .widgetList<DsShiftBadge>(find.byType(DsShiftBadge))
          .toList();
      expect(badges.map((b) => b.code), [ShiftCode.ad, ShiftCode.x]);
      expect(submitEnabled(tester), isTrue);

      // Same height; labels share a left edge, badges a right edge.
      final mine = tester.getRect(rowOf('Your shift'));
      final theirs = tester.getRect(rowOf("T2's shift"));
      expect(theirs.height, mine.height);
      expect(theirs.top, mine.bottom, reason: 'stacked, no gap');
      expect(
        tester.getTopLeft(find.text("T2's shift")).dx,
        tester.getTopLeft(find.text('Your shift')).dx,
      );
      final badgeRects = find
          .byType(DsShiftBadge)
          .evaluate()
          .map((e) => tester.getRect(find.byWidget(e.widget)))
          .toList();
      expect(badgeRects[1].right, badgeRects[0].right);
      // The rows sit under the colleague picker.
      expect(
        mine.top,
        greaterThan(
          tester.getRect(find.byType(DropdownButtonFormField<int?>)).bottom,
        ),
      );
    });

    testWidgets('a colleague without a roster cell shows "—" and blocks '
        'the submit', (tester) async {
      await openForm(tester);
      await tester.tap(find.text('Swap with colleague'));
      await tester.pumpAndSettle();

      await pickColleague(tester, 'T10');

      expect(find.text("T10's shift"), findsOneWidget);
      expect(
        find.descendant(of: rowOf("T10's shift"), matching: find.text('—')),
        findsOneWidget,
      );
      expect(find.byType(DsShiftBadge), findsOneWidget, reason: 'own only');
      expect(
        tester.getRect(rowOf("T10's shift")).height,
        tester.getRect(rowOf('Your shift')).height,
      );
      expect(submitEnabled(tester), isFalse);

      await pickColleague(tester, 'T2');
      expect(submitEnabled(tester), isTrue);
    });

    for (final locale in const [Locale('en'), Locale('vi')]) {
      testWidgets('fits 320 wide in both modes without overflow '
          '(${locale.languageCode})', (tester) async {
        // Any RenderFlex overflow is reported as a test failure.
        await openForm(tester, locale: locale);
        final note = find.byType(TextField);
        expect(tester.getSize(note).width, 320);

        final swap = AppLocalizations(locale).text('swapWith');
        await tester.tap(find.text(swap));
        await tester.pumpAndSettle();
        await pickColleague(tester, 'T2');

        expect(tester.getSize(note).width, 320);
        expect(
          tester.getSize(find.byType(DropdownButtonFormField<int?>)).width,
          320,
        );
        expect(tester.takeException(), isNull);
      });
    }
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

    testWidgets('generate lists what it broke in the already-generated next '
        'month (owner 2026-11-13)', (tester) async {
      const line = '2026-08: A1: more than 5 working days in a row from 2026-07-28.';
      final ds = _FakeScheduleDataSource(
        generateResult: ScheduleResult(
          feasible: true,
          violations: const [],
          nextMonthWarnings: const [line],
          schedule: MonthlySchedule(
            id: _FakeScheduleDataSource.idFor(_july),
            year: 2026,
            month: _july,
            status: ScheduleStatus.draft,
            assignments: const [],
          ),
        ),
      );
      await _pump(tester, user: _admin, ds: ds, initialMonth: _july);

      await tester.tap(find.text('Generate schedule'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Generate anyway')); // no flights this month
      await tester.pumpAndSettle();

      expect(find.text('Next month needs a look'), findsOneWidget);
      expect(find.text(line), findsOneWidget);
      await tester.tap(find.text('Close'));
      await tester.pumpAndSettle();
      expect(find.text('Next month needs a look'), findsNothing);
      await _drainToast(tester);
    });
  });
}
