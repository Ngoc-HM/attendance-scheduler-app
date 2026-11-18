// A month's roster runs to the Sunday that ends its last week (owner
// 2026-11-18): the grid places every cell by its DATE, shows the next
// month's carried days as rows after the month's last day (dated day/month)
// and offers no Publish for a month that holds only carried days.

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
import 'package:attendance_scheduler_app/features/schedule/domain/entities/schedule_entities.dart';
import 'package:attendance_scheduler_app/features/schedule/presentation/pages/schedule_page.dart';
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

const _a1 = 8;
const _a2 = 9;

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

ShiftAssignment _cell(int id, int user, DateTime day, String code) =>
    ShiftAssignment(
      id: id,
      userId: user,
      workDate: day,
      code: code,
      isManualOverride: false,
      carried: day.day <= 6 && day.month == 12,
    );

class _FakeScheduleDataSource extends ScheduleRemoteDataSource {
  _FakeScheduleDataSource(this.schedule) : super(Dio());

  final MonthlySchedule schedule;

  @override
  Future<MonthlySchedule> fetchSchedule(int year, int month) async => schedule;

  @override
  Future<List<ConstraintViolation>> fetchViolations(int scheduleId) async =>
      const [];

  @override
  Future<List<ShiftChangeRequest>> fetchShiftChanges({
    bool all = false,
  }) async => const [];

  @override
  Future<List<ShiftChangeRequest>> fetchIncomingShiftChanges() async =>
      const [];
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
      id: _a2,
      username: 'binh',
      fullName: 'Binh',
      role: UserRole.a,
      status: 'active',
      code: 'A2',
    ),
  ];

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class _FakeFlightsDataSource extends FlightsRemoteDataSource {
  _FakeFlightsDataSource() : super(Dio());

  @override
  Future<List<FlightDayModel>> listDays(int year, int month) async => [];
}

Future<void> _pump(WidgetTester tester, MonthlySchedule schedule) async {
  await tester.binding.setSurfaceSize(const Size(1400, 2400));
  addTearDown(() => tester.binding.setSurfaceSize(null));
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        authControllerProvider.overrideWith(
          (ref) => _SignedInAuthController(_admin),
        ),
        scheduleRemoteDataSourceProvider.overrideWithValue(
          _FakeScheduleDataSource(schedule),
        ),
        userManagementDataSourceProvider.overrideWithValue(
          _FakeUserDataSource(),
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
          body: SchedulePage(
            initialMonth: DateTime(schedule.year, schedule.month),
          ),
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

/// The roster row whose day column reads [label].
Row _row(WidgetTester tester, String label) => find
    .ancestor(of: find.text(label), matching: find.byType(Row))
    .evaluate()
    .map((e) => e.widget as Row)
    .firstWhere(
      (r) =>
          r.children.length > 3 &&
          r.children.skip(3).every((c) => c is SizedBox && c.child is InkWell),
    );

/// The badges of the roster row [label], left to right (A1 then A2); null
/// where the person has no cell.
List<ShiftCode?> _rowCodes(WidgetTester tester, String label) => [
  for (final cell in _row(tester, label).children.skip(3))
    switch (((cell as SizedBox).child! as InkWell).child) {
      Center(child: final DsShiftBadge badge) => badge.code,
      _ => null,
    },
];

/// The height of the roster row [label].
double _rowHeight(WidgetTester tester, String label) =>
    tester.getSize(find.byWidget(_row(tester, label))).height;

bool _publishShown(WidgetTester tester) =>
    find.text('Publish schedule').evaluate().isNotEmpty;

void main() {
  testWidgets('cells_are_placed_by_date', (tester) async {
    // A2 holds cells on the 17th and the 18th only: they stay on those rows.
    await _pump(
      tester,
      MonthlySchedule(
        id: 1,
        year: 2026,
        month: 6,
        status: ScheduleStatus.draft,
        assignments: [
          for (var d = 1; d <= 30; d++)
            _cell(d, _a1, DateTime(2026, 6, d), 'A'),
          _cell(100, _a2, DateTime(2026, 6, 17), 'D'),
          _cell(101, _a2, DateTime(2026, 6, 18), 'X'),
        ],
      ),
    );

    expect(_rowCodes(tester, '1'), [ShiftCode.a, null]);
    expect(_rowCodes(tester, '17'), [ShiftCode.a, ShiftCode.d]);
    expect(_rowCodes(tester, '18'), [ShiftCode.a, ShiftCode.x]);
    expect(_rowCodes(tester, '30'), [ShiftCode.a, null]);
  });

  testWidgets('carried_days_follow_the_last_day', (tester) async {
    // November 2026 ends on Monday the 30th: its roster runs to 6 December.
    await _pump(
      tester,
      MonthlySchedule(
        id: 11,
        year: 2026,
        month: 11,
        status: ScheduleStatus.published,
        assignments: [
          for (var d = 1; d <= 30; d++)
            _cell(d, _a1, DateTime(2026, 11, d), 'D'),
        ],
        carryAssignments: [
          for (var d = 1; d <= 6; d++) ...[
            _cell(100 + d, _a1, DateTime(2026, 12, d), d == 5 ? 'X' : 'A'),
            _cell(200 + d, _a2, DateTime(2026, 12, d), 'D'),
          ],
        ],
      ),
    );

    expect(_rowCodes(tester, '30'), [ShiftCode.d, null]);
    expect(_rowCodes(tester, '1/12'), [ShiftCode.a, ShiftCode.d]);
    expect(_rowCodes(tester, '5/12'), [ShiftCode.x, ShiftCode.d]);
    expect(_rowCodes(tester, '6/12'), [ShiftCode.a, ShiftCode.d]);
    expect(find.text('7/12'), findsNothing);
    expect(find.text('31'), findsNothing);
    // The counts are November's only: the day row "30", A1's D total and
    // the departures card read 30; A2's six carried D are not counted.
    expect(find.text('30'), findsNWidgets(3));
    expect(find.text('36'), findsNothing);
    expect(_publishShown(tester), isTrue);
    // A carried row is as tall as a day row: the label stays on one line.
    expect(_rowHeight(tester, '6/12'), _rowHeight(tester, '30'));
    expect(_rowHeight(tester, '1/12'), _rowHeight(tester, '29'));
  });

  testWidgets('carry_only_month_offers_no_publish', (tester) async {
    await _pump(
      tester,
      MonthlySchedule(
        id: 12,
        year: 2026,
        month: 12,
        status: ScheduleStatus.draft,
        assignments: [
          for (var d = 1; d <= 6; d++)
            _cell(d, _a1, DateTime(2026, 12, d), 'A'),
        ],
      ),
    );

    expect(_rowCodes(tester, '6'), [ShiftCode.a]);
    expect(_rowCodes(tester, '7'), [null]);
    expect(_publishShown(tester), isFalse);
  });
}
