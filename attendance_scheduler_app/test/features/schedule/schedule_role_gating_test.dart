// Widget tests for the schedule page's role gating (C1, C3, C4, C7):
// generate/publish are admin-only, code pickers only offer the row's planned
// codes (never S), employees see colleagues by directory code, and an
// employee can request a change on their own cell and see their requests.

import 'package:attendance_scheduler_app/core/constants/shift_codes.dart';
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
import 'package:attendance_scheduler_app/features/users/data/user_management_datasource.dart';
import 'package:attendance_scheduler_app/i18n/app_localizations.dart';
import 'package:attendance_scheduler_app/i18n/locale_provider.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

const _employee = User(
  id: 7,
  username: 'tuan',
  fullName: 'Tuan Nguyen',
  role: UserRole.t,
  status: 'active',
  code: 'T1',
);

const _admin = User(
  id: 1,
  username: 'boss',
  fullName: 'Boss',
  role: UserRole.m,
  status: 'active',
  code: 'M1',
);

/// Colleague on the fixed role, so the admin picker can be checked for A/D.
const _colleagueId = 8;

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

/// Published month where T1 (id 7) works AD and A1 (id 8) works A every day.
class _FakeScheduleDataSource extends ScheduleRemoteDataSource {
  _FakeScheduleDataSource() : super(Dio());

  final created = <Map<String, Object?>>[];
  final fetchAllFlags = <bool>[];
  final _requests = <ShiftChangeRequest>[];

  @override
  Future<MonthlySchedule> fetchSchedule(int year, int month) async {
    final days = DateTime(year, month + 1, 0).day;
    return MonthlySchedule(
      id: 1,
      year: year,
      month: month,
      status: ScheduleStatus.published,
      assignments: [
        for (var d = 1; d <= days; d++) ...[
          ShiftAssignment(
            id: d * 10 + 1,
            userId: _employee.id,
            workDate: DateTime(year, month, d),
            code: 'AD',
            isManualOverride: false,
          ),
          ShiftAssignment(
            id: d * 10 + 2,
            userId: _colleagueId,
            workDate: DateTime(year, month, d),
            code: 'A',
            isManualOverride: false,
          ),
        ],
      ],
    );
  }

  @override
  Future<List<ShiftChangeRequest>> fetchShiftChanges({bool all = false}) async {
    fetchAllFlags.add(all);
    return List.of(_requests);
  }

  @override
  Future<ShiftChangeRequest> createShiftChange({
    required DateTime workDate,
    required String kind,
    String? requestedCode,
    int? counterpartUserId,
    String? note,
  }) async {
    created.add({
      'workDate': workDate,
      'kind': kind,
      'requestedCode': requestedCode,
      'counterpartUserId': counterpartUserId,
    });
    final request = ShiftChangeRequest(
      id: created.length,
      requesterId: _employee.id,
      workDate: workDate,
      kind: kind,
      status: 'pending',
      strictReview: false,
      warnings: const [],
      requestedCode: requestedCode,
      counterpartUserId: counterpartUserId,
    );
    _requests.insert(0, request);
    return request;
  }
}

class _FakeUserDataSource implements UserManagementDataSource {
  var listCalls = 0;
  var directoryCalls = 0;

  @override
  Future<List<UserModel>> list() async {
    listCalls++;
    return const [
      UserModel(
        id: 7,
        username: 'tuan',
        fullName: 'Tuan Nguyen',
        role: UserRole.t,
        status: 'active',
        code: 'T1',
      ),
      UserModel(
        id: _colleagueId,
        username: 'anh',
        fullName: 'Anh Tran',
        role: UserRole.a,
        status: 'active',
        code: 'A1',
      ),
    ];
  }

  @override
  Future<List<UserDirectoryEntry>> directory() async {
    directoryCalls++;
    return const [
      UserDirectoryEntry(id: _colleagueId, code: 'A1', role: UserRole.a),
      UserDirectoryEntry(id: 1, code: 'M1', role: UserRole.m),
      UserDirectoryEntry(id: 7, code: 'T1', role: UserRole.t),
    ];
  }

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

Future<void> _pumpSchedule(
  WidgetTester tester, {
  required User user,
  required _FakeScheduleDataSource scheduleDs,
  required _FakeUserDataSource userDs,
}) async {
  await tester.binding.setSurfaceSize(const Size(1400, 1800));
  addTearDown(() => tester.binding.setSurfaceSize(null));
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        authControllerProvider.overrideWith(
          (ref) => _SignedInAuthController(user),
        ),
        scheduleRemoteDataSourceProvider.overrideWithValue(scheduleDs),
        userManagementDataSourceProvider.overrideWithValue(userDs),
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
        home: const Scaffold(body: SchedulePage()),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

/// Roster cell badge for [day] (1-based) in roster column [column]. Columns
/// are ordered by role then code: A1 is column 0, T1 is column 1.
Finder _cell(int day, int column) => find
    .descendant(of: find.byType(InkWell), matching: find.byType(DsShiftBadge))
    .at((day - 1) * 2 + column);

const _a1Column = 0;
const _t1Column = 1;

Future<void> _tapCell(WidgetTester tester, int day, int column) async {
  await tester.ensureVisible(_cell(day, column));
  await tester.tap(_cell(day, column));
  await tester.pumpAndSettle();
}

List<ShiftCode?> _offeredCodes(WidgetTester tester) => tester
    .widget<DropdownButton<ShiftCode>>(find.byType(DropdownButton<ShiftCode>))
    .items!
    .map((item) => item.value)
    .toList();

/// Let the auto-dismiss timer of a DsFeedback toast run out.
Future<void> _drainToast(WidgetTester tester) async {
  await tester.pump(const Duration(seconds: 9));
  await tester.pumpAndSettle();
}

void main() {
  group('ShiftCodeX.plannedCodesFor', () {
    test('mirrors the backend planned-grid domain per role', () {
      expect(ShiftCodeX.plannedCodesFor(UserRole.a), [
        ShiftCode.a,
        ShiftCode.d,
        ShiftCode.aD,
        ShiftCode.x,
        ShiftCode.cd,
        ShiftCode.t,
        ShiftCode.b,
        ShiftCode.al,
      ]);
      const flexible = [
        ShiftCode.ad,
        ShiftCode.x,
        ShiftCode.cd,
        ShiftCode.t,
        ShiftCode.b,
        ShiftCode.al,
      ];
      expect(ShiftCodeX.plannedCodesFor(UserRole.t), flexible);
      expect(ShiftCodeX.plannedCodesFor(UserRole.f), flexible);
      expect(ShiftCodeX.plannedCodesFor(UserRole.m), [
        ShiftCode.oD,
        ShiftCode.x,
        ShiftCode.cd,
        ShiftCode.t,
        ShiftCode.b,
        ShiftCode.al,
      ]);
    });

    test('never offers sickness S on the planned grid', () {
      for (final role in UserRole.values) {
        expect(ShiftCodeX.plannedCodesFor(role), isNot(contains(ShiftCode.s)));
      }
    });
  });

  testWidgets('employee sees no generate/publish and cannot pick S', (
    tester,
  ) async {
    await _pumpSchedule(
      tester,
      user: _employee,
      scheduleDs: _FakeScheduleDataSource(),
      userDs: _FakeUserDataSource(),
    );

    expect(find.text('Generate schedule'), findsNothing);
    expect(find.text('Publish schedule'), findsNothing);

    await _tapCell(tester, 3, _t1Column);
    expect(find.text('Request shift change'), findsOneWidget);
    expect(_offeredCodes(tester), ShiftCodeX.plannedCodesFor(UserRole.t));
    expect(_offeredCodes(tester), isNot(contains(ShiftCode.s)));
  });

  testWidgets('admin cell editor offers only the row role planned codes', (
    tester,
  ) async {
    await _pumpSchedule(
      tester,
      user: _admin,
      scheduleDs: _FakeScheduleDataSource(),
      userDs: _FakeUserDataSource(),
    );

    expect(find.text('Generate schedule'), findsOneWidget);
    expect(find.text('Publish schedule'), findsOneWidget);

    await _tapCell(tester, 2, _a1Column);
    expect(_offeredCodes(tester), ShiftCodeX.plannedCodesFor(UserRole.a));
    expect(_offeredCodes(tester), isNot(contains(ShiftCode.s)));
    await tester.tap(find.text('Cancel'));
    await tester.pumpAndSettle();

    await _tapCell(tester, 2, _t1Column);
    expect(_offeredCodes(tester), ShiftCodeX.plannedCodesFor(UserRole.t));
  });

  testWidgets('employee roster names colleagues by directory code', (
    tester,
  ) async {
    final userDs = _FakeUserDataSource();
    await _pumpSchedule(
      tester,
      user: _employee,
      scheduleDs: _FakeScheduleDataSource(),
      userDs: userDs,
    );

    expect(userDs.listCalls, 0, reason: 'GET /users is admin-only');
    expect(userDs.directoryCalls, 1);
    expect(find.text('A1'), findsOneWidget);
    expect(find.text('T1'), findsOneWidget);
    expect(find.textContaining('User '), findsNothing);
  });

  testWidgets('employee tapping a colleague cell opens nothing', (
    tester,
  ) async {
    await _pumpSchedule(
      tester,
      user: _employee,
      scheduleDs: _FakeScheduleDataSource(),
      userDs: _FakeUserDataSource(),
    );

    await _tapCell(tester, 3, _a1Column);
    expect(find.byType(AlertDialog), findsNothing);
  });

  testWidgets('employee requests a change on own cell and sees it listed', (
    tester,
  ) async {
    final scheduleDs = _FakeScheduleDataSource();
    await _pumpSchedule(
      tester,
      user: _employee,
      scheduleDs: scheduleDs,
      userDs: _FakeUserDataSource(),
    );

    expect(scheduleDs.fetchAllFlags, [false]);
    expect(find.text('My shift-change requests'), findsOneWidget);

    await _tapCell(tester, 3, _t1Column);
    await tester.tap(find.text('Submit request'));
    await tester.pumpAndSettle();

    final now = DateTime.now();
    expect(scheduleDs.created, [
      {
        'workDate': DateTime(now.year, now.month, 3),
        'kind': 'change_code',
        'requestedCode': 'X',
        'counterpartUserId': null,
      },
    ]);
    expect(find.byType(AlertDialog), findsNothing);
    expect(find.text('Shift-change request submitted.'), findsOneWidget);

    // The own-requests table reloads and shows the new pending request.
    expect(scheduleDs.fetchAllFlags, [false, false]);
    final day = '${now.year}-${now.month.toString().padLeft(2, '0')}-03';
    expect(find.text(day), findsOneWidget);
    expect(find.text('Change code'), findsOneWidget);
    expect(find.text('Pending'), findsOneWidget);

    await _drainToast(tester);
  });

  testWidgets('swap picker lists colleagues by code, excluding self', (
    tester,
  ) async {
    await _pumpSchedule(
      tester,
      user: _employee,
      scheduleDs: _FakeScheduleDataSource(),
      userDs: _FakeUserDataSource(),
    );

    await _tapCell(tester, 3, _t1Column);
    await tester.tap(find.text('Swap with colleague'));
    await tester.pumpAndSettle();

    final picker = tester.widget<DropdownButton<int>>(
      find.byType(DropdownButton<int>),
    );
    expect(picker.items!.map((item) => item.value), [_colleagueId, 1]);
    expect(picker.items!.map((item) => (item.child as Text).data), [
      'A1',
      'M1',
    ]);
  });
}
