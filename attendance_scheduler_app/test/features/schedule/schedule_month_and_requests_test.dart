// Review 2026-11-08 fixes on the schedule screen (A3, D3, C2 client side,
// swap picker and schedule toasts): the grid always belongs to the month on
// screen, Publish targets that month and shows the rule violations first,
// the admin shift-change panel names requester and counterpart, approving
// shows the backend warnings and reloads the grid, and the swap picker
// offers same-role colleagues only.

import 'dart:async';

import 'package:attendance_scheduler_app/core/network/api_exception.dart';
import 'package:attendance_scheduler_app/core/storage/locale_storage.dart';
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
  }) : super(Dio());

  final bool julyExists;
  final List<ConstraintViolation> violations;
  final List<ShiftChangeRequest> requests;
  final List<String> decideWarnings;
  final Object? publishError;

  /// Thrown by every [fetchSchedule] call (instead of the 404 for July).
  final Object? fetchError;

  /// Month → completer that holds that month's response until completed.
  final held = <int, Completer<void>>{};

  final fetchedMonths = <int>[];
  final published = <int>[];
  final violationCalls = <int>[];
  final decided = <(int, String)>[];

  static int idFor(int month) => 600 + month;

  @override
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

  @override
  Future<List<ConstraintViolation>> fetchViolations(int scheduleId) async {
    violationCalls.add(scheduleId);
    return violations;
  }

  @override
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

  @override
  Future<List<ShiftChangeRequest>> fetchShiftChanges({bool all = false}) async =>
      List.of(requests);

  @override
  Future<ShiftChangeRequest> decideShiftChange({
    required int id,
    required String status,
  }) async {
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

class _FakeFlightsDataSource extends FlightsRemoteDataSource {
  _FakeFlightsDataSource() : super(Dio());

  @override
  Future<List<FlightDayModel>> listDays(int year, int month) async => [];
}

class _FakeSelfArrangeDataSource extends SelfArrangeRemoteDataSource {
  _FakeSelfArrangeDataSource() : super(Dio());

  @override
  Future<List<SelfArrangeBatch>> list({
    bool all = false,
    bool pendingOnly = false,
  }) async => [];
}

Future<void> _pump(
  WidgetTester tester, {
  required User user,
  required _FakeScheduleDataSource ds,
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
          _FakeUserDataSource(),
        ),
        flightsDataSourceProvider.overrideWithValue(_FakeFlightsDataSource()),
        selfArrangeRemoteDataSourceProvider.overrideWithValue(
          _FakeSelfArrangeDataSource(),
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
        home: Scaffold(body: SchedulePage(initialMonth: DateTime(2026, 6))),
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
    expect(find.textContaining('Database unavailable'), findsOneWidget);
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
}
