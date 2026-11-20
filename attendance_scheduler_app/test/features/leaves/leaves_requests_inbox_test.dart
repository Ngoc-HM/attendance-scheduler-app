// One screen for everything the admin approves (owner 2026-11-20): the
// Leaves page lists leave, shift-change and sign-up requests in one table,
// newest first. A swap still waiting for the colleague has no actions;
// approving a shift change warns first and refreshes the roster; a sign-up
// is approved with a role and rejected by deleting the account. Employees
// see their own leave and shift changes there; the Users page no longer
// approves sign-ups.

import 'package:attendance_scheduler_app/core/network/api_exception.dart';
import 'package:attendance_scheduler_app/core/storage/locale_storage.dart';
import 'package:attendance_scheduler_app/design_system/design_system.dart';
import 'package:attendance_scheduler_app/features/auth/data/models/user_model.dart';
import 'package:attendance_scheduler_app/features/auth/domain/entities/user.dart';
import 'package:attendance_scheduler_app/features/auth/domain/repositories/auth_repository.dart';
import 'package:attendance_scheduler_app/features/auth/presentation/providers/auth_provider.dart';
import 'package:attendance_scheduler_app/features/leaves/data/datasources/leaves_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/leaves/data/models/leave_model.dart';
import 'package:attendance_scheduler_app/features/leaves/presentation/pages/leaves_page.dart';
import 'package:attendance_scheduler_app/features/schedule/data/datasources/schedule_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/schedule/domain/entities/schedule_entities.dart';
import 'package:attendance_scheduler_app/features/schedule/presentation/providers/schedule_provider.dart';
import 'package:attendance_scheduler_app/features/users/data/user_management_datasource.dart';
import 'package:attendance_scheduler_app/features/users/presentation/pages/users_page.dart';
import 'package:attendance_scheduler_app/i18n/app_localizations.dart';
import 'package:attendance_scheduler_app/i18n/locale_provider.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

class _Noop implements AuthRepository {
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class _SignedIn extends AuthController {
  _SignedIn(User user) : super(_Noop(), LocaleController(LocaleStorage())) {
    state = AuthState(user: user);
  }
}

const _admin = UserModel(
  id: 1,
  username: 'boss',
  fullName: 'Boss',
  role: UserRole.m,
  status: 'active',
  code: 'M1',
);
const _t1 = UserModel(
  id: 7,
  username: 'tuan',
  fullName: 'Tuan',
  role: UserRole.t,
  status: 'active',
  code: 'T1',
  carryComp: 2,
);
const _a1 = UserModel(
  id: 8,
  username: 'anh',
  fullName: 'Anh',
  role: UserRole.a,
  status: 'active',
  code: 'A1',
);
const _t2 = UserModel(
  id: 9,
  username: 'thu',
  fullName: 'Thu',
  role: UserRole.t,
  status: 'active',
  code: 'T2',
);
final _signUp = UserModel(
  id: 20,
  username: 'longg',
  fullName: 'Long',
  role: UserRole.f,
  status: 'pending',
  code: '',
  createdAt: DateTime(2026, 11, 14, 9),
);

class _Leaves implements LeavesRemoteDataSource {
  final decided = <(int, String)>[];

  LeaveModel get _leave => LeaveModel(
    id: 1,
    userId: 8,
    startDate: DateTime(2026, 12, 3),
    endDate: DateTime(2026, 12, 4),
    leaveType: 'monthly',
    status: 'pending',
    createdAt: DateTime(2026, 11, 10),
  );

  @override
  Future<List<LeaveModel>> listAll() async => [_leave];

  @override
  Future<List<LeaveModel>> listOwn() async => [
    LeaveModel(
      id: 2,
      userId: 7,
      startDate: DateTime(2026, 12, 7),
      endDate: DateTime(2026, 12, 7),
      leaveType: 'monthly',
      status: 'pending',
      createdAt: DateTime(2026, 11, 10),
    ),
  ];

  @override
  Future<LeaveWindow> fetchWindow() async => const LeaveWindow(
    monthlyOpen: true,
    monthlyTargetYear: 2026,
    monthlyTargetMonth: 12,
    annualTargetYear: 2027,
    closesOnDay: 20,
    enforced: true,
  );

  @override
  Future<AnnualLeaveBalance> fetchBalance({int? year}) async =>
      const AnnualLeaveBalance(
        year: 2026,
        quota: 30,
        used: 0,
        pending: 0,
        remaining: 30,
      );

  @override
  Future<List<String>> approvalPreview(int id) async => const [];

  @override
  Future<(LeaveModel, List<String>)> decide(int id, String status) async {
    decided.add((id, status));
    return (_leave, const <String>[]);
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

ShiftChangeRequest _change({
  required int id,
  required int requesterId,
  required String kind,
  required DateTime workDate,
  required DateTime createdAt,
  String status = 'pending',
  String? counterpartStatus,
  int? counterpartUserId,
  String? requestedCode,
  String? requesterShift,
  String? counterpartShift,
}) => ShiftChangeRequest(
  id: id,
  requesterId: requesterId,
  workDate: workDate,
  kind: kind,
  status: status,
  strictReview: false,
  warnings: const [],
  counterpartUserId: counterpartUserId,
  counterpartStatus: counterpartStatus,
  requestedCode: requestedCode,
  requesterShift: requesterShift,
  counterpartShift: counterpartShift,
  createdAt: createdAt,
);

/// T1 ⇄ T2 accepted by T2 (the admin decides).
final _acceptedSwap = _change(
  id: 31,
  requesterId: 7,
  kind: 'swap_with',
  workDate: DateTime(2026, 11, 8),
  createdAt: DateTime(2026, 11, 12),
  counterpartUserId: 9,
  counterpartStatus: 'approved',
  requesterShift: 'AD',
  counterpartShift: 'X',
);

/// T1 ⇄ T2 not answered by T2 yet.
final _waitingSwap = _change(
  id: 33,
  requesterId: 7,
  kind: 'swap_with',
  workDate: DateTime(2026, 11, 20),
  createdAt: DateTime(2026, 11, 13),
  counterpartUserId: 9,
  counterpartStatus: 'pending',
  requesterShift: 'A',
  counterpartShift: 'D',
);

/// A1 asks A → X.
final _codeChange = _change(
  id: 32,
  requesterId: 8,
  kind: 'change_code',
  workDate: DateTime(2026, 11, 9),
  createdAt: DateTime(2026, 11, 11),
  requestedCode: 'X',
  requesterShift: 'A',
);

class _Schedule extends ScheduleRemoteDataSource {
  _Schedule({this.requests = const [], this.previewWarnings = const []})
    : super(Dio());

  final List<ShiftChangeRequest> requests;
  final List<String> previewWarnings;
  final decided = <(int, String)>[];
  final fetchedMonths = <int>[];
  bool? fetchedAll;

  @override
  Future<List<ShiftChangeRequest>> fetchShiftChanges({bool all = false}) async {
    fetchedAll = all;
    return [
      for (final r in requests)
        if (!decided.any((d) => d.$1 == r.id)) r,
    ];
  }

  @override
  Future<List<String>> shiftChangeApprovalPreview(int id) async =>
      previewWarnings;

  @override
  Future<ShiftChangeRequest> decideShiftChange({
    required int id,
    required String status,
  }) async {
    decided.add((id, status));
    final r = requests.firstWhere((r) => r.id == id);
    return _change(
      id: r.id,
      requesterId: r.requesterId,
      kind: r.kind,
      workDate: r.workDate,
      createdAt: r.createdAt!,
      status: status,
    );
  }

  @override
  Future<MonthlySchedule> fetchSchedule(int year, int month) async {
    fetchedMonths.add(month);
    return MonthlySchedule(
      id: 600 + month,
      year: year,
      month: month,
      status: ScheduleStatus.draft,
      assignments: const [],
    );
  }

  @override
  Future<List<ConstraintViolation>> fetchViolations(int scheduleId) async =>
      const [];
}

class _Users implements UserManagementDataSource {
  _Users({this.approveError});

  /// Thrown by [approve] (e.g. the account is no longer pending).
  final Object? approveError;
  final approvals = <(int, String)>[];
  final deleted = <int>[];

  @override
  Future<List<UserModel>> list() async => [
    _admin,
    _t1,
    _a1,
    _t2,
    if (!deleted.contains(_signUp.id) &&
        !approvals.any((a) => a.$1 == _signUp.id))
      _signUp,
  ];

  @override
  Future<List<UserDirectoryEntry>> directory() async => const [
    UserDirectoryEntry(id: 7, code: 'T1', role: UserRole.t),
    UserDirectoryEntry(id: 9, code: 'T2', role: UserRole.t),
  ];

  @override
  Future<UserModel> approve(int id, {required String role}) async {
    if (approveError != null) throw approveError!;
    approvals.add((id, role));
    return _signUp;
  }

  @override
  Future<void> delete(int id) async => deleted.add(id);

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

Future<ProviderContainer> _pump(
  WidgetTester tester, {
  required User user,
  required _Schedule schedule,
  _Leaves? leaves,
  _Users? users,
  Widget page = const LeavesPage(),
}) async {
  await tester.binding.setSurfaceSize(const Size(2000, 1400));
  addTearDown(() => tester.binding.setSurfaceSize(null));
  final container = ProviderContainer(
    overrides: [
      authControllerProvider.overrideWith((ref) => _SignedIn(user)),
      leavesDataSourceProvider.overrideWithValue(leaves ?? _Leaves()),
      scheduleRemoteDataSourceProvider.overrideWithValue(schedule),
      userManagementDataSourceProvider.overrideWithValue(users ?? _Users()),
    ],
  );
  addTearDown(container.dispose);
  await tester.pumpWidget(
    UncontrolledProviderScope(
      container: container,
      child: MaterialApp(
        theme: AppTheme.light,
        localizationsDelegates: const [
          AppLocalizations.delegate,
          DefaultMaterialLocalizations.delegate,
          DefaultWidgetsLocalizations.delegate,
        ],
        supportedLocales: AppLocalizations.supportedLocales,
        locale: const Locale('en'),
        home: Scaffold(body: page),
      ),
    ),
  );
  await tester.pumpAndSettle();
  return container;
}

/// Let the auto-dismiss timer of a DsFeedback toast run out.
Future<void> _drainToast(WidgetTester tester) async {
  await tester.pump(const Duration(seconds: 9));
  await tester.pumpAndSettle();
}

Finder _inDialog(Finder finder) =>
    find.descendant(of: find.byType(AlertDialog), matching: finder);

double _top(WidgetTester tester, String text) =>
    tester.getTopLeft(find.text(text).first).dy;

/// The [label] action (Approve / Reject) of the row whose dates cell
/// reads [dates]; finds nothing when that row has no such action.
Finder _actionOf(WidgetTester tester, String dates, String label) {
  final y = tester.getCenter(find.text(dates)).dy;
  return find.byWidgetPredicate(
    (w) =>
        w is DsTextAction &&
        w.label == label &&
        (tester.getCenter(find.byWidget(w)).dy - y).abs() < 4,
  );
}

Finder _approveOf(WidgetTester tester, String dates) =>
    _actionOf(tester, dates, 'Approve');

void main() {
  final allRequests = [_acceptedSwap, _waitingSwap, _codeChange];

  testWidgets('admin: one table of leave, shift changes and sign-ups, '
      'newest first', (tester) async {
    final schedule = _Schedule(requests: allRequests);
    await _pump(tester, user: _admin, schedule: schedule);

    expect(find.text('Approvals'), findsOneWidget);
    expect(schedule.fetchedAll, isTrue, reason: 'the admin sees everyone');

    // Type and dates of each kind.
    expect(find.text('New account'), findsOneWidget);
    expect(find.text('longg'), findsOneWidget);
    expect(find.text('14/11/2026'), findsOneWidget);
    expect(find.text('Shift swap'), findsNWidgets(2));
    expect(find.text('08/11/2026 · T1 (AD) ⇄ T2 (X)'), findsOneWidget);
    expect(find.text('20/11/2026 · T1 (A) ⇄ T2 (D)'), findsOneWidget);
    expect(find.text('Code change'), findsOneWidget);
    expect(find.text('09/11/2026 · A → X'), findsOneWidget);
    expect(find.text('Monthly leave'), findsOneWidget);
    expect(find.text('03–04/12/2026'), findsOneWidget);

    // Newest first: sign-up (14th), waiting swap (13th), accepted swap
    // (12th), code change (11th), leave (10th).
    final ys = [
      _top(tester, '14/11/2026'),
      _top(tester, '20/11/2026 · T1 (A) ⇄ T2 (D)'),
      _top(tester, '08/11/2026 · T1 (AD) ⇄ T2 (X)'),
      _top(tester, '09/11/2026 · A → X'),
      _top(tester, '03–04/12/2026'),
    ];
    expect(ys, orderedEquals([...ys]..sort()));

    // Days and carry: one day and the requester's carry for a shift
    // change, "—" for a sign-up.
    expect(find.text('—'), findsNWidgets(2));
    expect(find.text('Waiting for colleague'), findsOneWidget);
    // Pending card: what the admin can decide now (sign-up, accepted
    // swap, code change, leave), not the swap waiting for the colleague.
    expect(
      find.descendant(
        of: find.ancestor(
          of: find.text('Pending'),
          matching: find.byType(DsMetricCard),
        ),
        matching: find.text('4'),
      ),
      findsOneWidget,
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets('admin: a swap waiting for the colleague has no actions', (
    tester,
  ) async {
    await _pump(tester, user: _admin, schedule: _Schedule(requests: allRequests));

    expect(find.text('Approve'), findsNWidgets(4));
    expect(find.text('Reject'), findsNWidgets(4));
    expect(
      _approveOf(tester, '20/11/2026 · T1 (A) ⇄ T2 (D)'),
      findsNothing,
    );
    expect(
      _approveOf(tester, '08/11/2026 · T1 (AD) ⇄ T2 (X)'),
      findsOneWidget,
    );
  });

  testWidgets('admin: approving a shift change warns first, then approves '
      'and refreshes the roster', (tester) async {
    final schedule = _Schedule(
      requests: allRequests,
      previewWarnings: const ['2026-11-08: arrival cover below minimum'],
    );
    final container = await _pump(tester, user: _admin, schedule: schedule);
    // The Schedule page had November loaded.
    await container
        .read(scheduleControllerProvider.notifier)
        .load(2026, 11, isAdmin: true);
    expect(schedule.fetchedMonths, [11]);

    await tester.tap(_approveOf(tester, '08/11/2026 · T1 (AD) ⇄ T2 (X)'));
    await tester.pumpAndSettle();

    expect(schedule.decided, isEmpty, reason: 'nothing approved yet');
    expect(
      _inDialog(find.text('2026-11-08: arrival cover below minimum')),
      findsOneWidget,
    );

    await tester.tap(find.text('Approve anyway'));
    await tester.pumpAndSettle();

    expect(schedule.decided, [(31, 'approved')]);
    expect(schedule.fetchedMonths, [11, 11], reason: 'roster reloaded');
    expect(find.text('Request approved.'), findsOneWidget);
    expect(find.text('08/11/2026 · T1 (AD) ⇄ T2 (X)'), findsNothing);
    await _drainToast(tester);
  });

  testWidgets('admin: cancelling the warning decides nothing', (tester) async {
    final schedule = _Schedule(
      requests: allRequests,
      previewWarnings: const ['2026-11-09: rest below 11 h'],
    );
    await _pump(tester, user: _admin, schedule: schedule);

    await tester.tap(_approveOf(tester, '09/11/2026 · A → X'));
    await tester.pumpAndSettle();
    await tester.tap(_inDialog(find.text('Cancel')));
    await tester.pumpAndSettle();

    expect(schedule.decided, isEmpty);
    expect(find.text('Approve'), findsNWidgets(4));
  });

  testWidgets('admin: rejecting a code change changes no roster cell', (
    tester,
  ) async {
    final schedule = _Schedule(requests: allRequests);
    final container = await _pump(tester, user: _admin, schedule: schedule);
    await container
        .read(scheduleControllerProvider.notifier)
        .load(2026, 11, isAdmin: true);

    await tester.tap(_actionOf(tester, '09/11/2026 · A → X', 'Reject'));
    await tester.pumpAndSettle();

    expect(schedule.decided, [(32, 'rejected')]);
    expect(schedule.fetchedMonths, [11], reason: 'a rejection changes no cell');
    expect(find.text('Request rejected.'), findsOneWidget);
    await _drainToast(tester);
  });

  group('sign-ups (moved from the Users page)', () {
    testWidgets('approve opens the role dialog on the account role', (
      tester,
    ) async {
      final users = _Users();
      await _pump(tester, user: _admin, schedule: _Schedule(), users: users);

      await tester.tap(_approveOf(tester, '14/11/2026'));
      await tester.pumpAndSettle();
      expect(_inDialog(find.text('F — Flexible')), findsOneWidget);

      await tester.tap(_inDialog(find.text('Approve')));
      await tester.pumpAndSettle();

      expect(users.approvals, [(20, 'F')]);
      expect(find.text('longg'), findsNothing, reason: 'list reloaded');
      await _drainToast(tester);
    });

    testWidgets('cancelling the role dialog approves nothing', (tester) async {
      final users = _Users();
      await _pump(tester, user: _admin, schedule: _Schedule(), users: users);

      await tester.tap(_approveOf(tester, '14/11/2026'));
      await tester.pumpAndSettle();
      await tester.tap(_inDialog(find.text('Cancel')));
      await tester.pumpAndSettle();

      expect(users.approvals, isEmpty);
      expect(find.text('longg'), findsOneWidget);
    });

    testWidgets('a failed approval shows the backend message', (tester) async {
      const notPending = 'Only a pending account can be approved.';
      final users = _Users(
        approveError: const ApiException(notPending, statusCode: 409),
      );
      await _pump(tester, user: _admin, schedule: _Schedule(), users: users);

      await tester.tap(_approveOf(tester, '14/11/2026'));
      await tester.pumpAndSettle();
      await tester.tap(_inDialog(find.text('Approve')));
      await tester.pumpAndSettle();

      expect(find.text(notPending), findsOneWidget);
      await _drainToast(tester);
    });

    testWidgets('reject deletes the account after the delete confirmation', (
      tester,
    ) async {
      final users = _Users();
      await _pump(tester, user: _admin, schedule: _Schedule(), users: users);

      await tester.tap(_actionOf(tester, '14/11/2026', 'Reject'));
      await tester.pumpAndSettle();
      expect(_inDialog(find.text('Delete')), findsOneWidget);
      expect(users.deleted, isEmpty, reason: 'nothing before the confirm');

      await tester.tap(_inDialog(find.text('Delete')));
      await tester.pumpAndSettle();

      expect(users.deleted, [20]);
      expect(find.text('longg'), findsNothing);
      await _drainToast(tester);
    });

    testWidgets('the Users page no longer approves a pending account', (
      tester,
    ) async {
      await _pump(
        tester,
        user: _admin,
        schedule: _Schedule(),
        page: const UsersPage(),
      );

      expect(find.text('longg'), findsOneWidget);
      expect(find.text('Approve'), findsNothing);
    });
  });

  testWidgets('employee: own leave and shift changes, cancel on leave only', (
    tester,
  ) async {
    final schedule = _Schedule(
      requests: [
        _waitingSwap,
        _change(
          id: 34,
          requesterId: 7,
          kind: 'swap_with',
          workDate: DateTime(2026, 11, 21),
          createdAt: DateTime(2026, 11, 14),
          status: 'rejected',
          counterpartUserId: 9,
          counterpartStatus: 'rejected',
          requesterShift: 'A',
          counterpartShift: 'X',
        ),
        _change(
          id: 35,
          requesterId: 7,
          kind: 'change_code',
          workDate: DateTime(2026, 11, 22),
          createdAt: DateTime(2026, 11, 15),
          status: 'pending',
          requestedCode: 'X',
          requesterShift: 'AD',
        ),
      ],
    );
    await _pump(tester, user: _t1, schedule: schedule);

    expect(find.text('Leave & shift changes'), findsOneWidget);
    expect(schedule.fetchedAll, isFalse, reason: 'own requests only');
    expect(find.text('20/11/2026 · T1 (A) ⇄ T2 (D)'), findsOneWidget);
    expect(find.text('21/11/2026 · T1 (A) ⇄ T2 (X)'), findsOneWidget);
    expect(find.text('22/11/2026 · AD → X'), findsOneWidget);
    expect(find.text('Waiting for colleague'), findsOneWidget);
    expect(find.text('Declined by colleague'), findsOneWidget);
    // Cancel only on the pending leave, not on the pending code change.
    expect(find.text('Cancel'), findsOneWidget);
    expect(find.text('Approve'), findsNothing);
    expect(tester.takeException(), isNull);
  });

  // At 1280 px the content beside the 240 px rail is narrower than the
  // admin table's minimum (1000 px), so the table is laid out at exactly
  // that width: every cell must fit there, in both languages.
  // Padded = touch tap targets (the test default), shrinkWrap = desktop.
  for (final (locale, target) in const [
    (Locale('en'), MaterialTapTargetSize.padded),
    (Locale('vi'), MaterialTapTargetSize.padded),
    (Locale('vi'), MaterialTapTargetSize.shrinkWrap),
  ]) {
    testWidgets('${locale.languageCode} ${target.name}: request rows fit the '
        'table at its minimum width, one line, one height', (tester) async {
      await tester.binding.setSurfaceSize(const Size(1048, 900));
      addTearDown(() => tester.binding.setSurfaceSize(null));
      DsLeaveRowData row(
        String employee,
        String range,
        DsRequestKind kind,
        String status,
      ) => DsLeaveRowData(
        employee: employee,
        role: kind == DsRequestKind.signUp ? 'F' : 'T',
        type: switch (kind) {
          DsRequestKind.leave => 'Monthly leave',
          DsRequestKind.shiftChange => 'Code change',
          DsRequestKind.signUp => 'New account',
        },
        range: range,
        days: kind == DsRequestKind.signUp ? null : 1,
        status: status,
        carryComp: kind == DsRequestKind.signUp ? null : 0,
        kind: kind,
      );
      const long = '08/11/2026 · T10 (AD) ⇄ T12 (X)';
      final rows = [
        row('T10', long, DsRequestKind.shiftChange, 'Pending'),
        row('T11', '09/11/2026 · T11 (AD) ⇄ T12 (X)', DsRequestKind.shiftChange,
            DsLeaveRowData.statusDeclinedByColleague),
        row('T12', '10/11/2026 · T12 (AD) ⇄ T10 (X)', DsRequestKind.shiftChange,
            DsLeaveRowData.statusAwaitingColleague),
        row('longg', '14/11/2026', DsRequestKind.signUp, 'Pending'),
        row('A1', '03–04/12/2026', DsRequestKind.leave, 'Approved'),
      ];
      await tester.pumpWidget(
        MaterialApp(
          theme: AppTheme.light.copyWith(materialTapTargetSize: target),
          localizationsDelegates: const [
            AppLocalizations.delegate,
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          supportedLocales: AppLocalizations.supportedLocales,
          locale: locale,
          // Roughly a UI font's glyph width (the test font is twice as wide).
          builder: (context, child) => MediaQuery(
            data: MediaQuery.of(
              context,
            ).copyWith(textScaler: const TextScaler.linear(0.55)),
            child: child!,
          ),
          home: Scaffold(
            body: DsLeavesView(
              rows: rows,
              onMonthlyRequest: () {},
              onAnnualRequest: () {},
              onApprove: (_) {},
              onReject: (_) {},
              onRevoke: (_) {},
              compDays: 0,
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(tester.takeException(), isNull);
      final text = tester.widget<Text>(find.text(long));
      expect(text.maxLines, 1);
      expect(text.overflow, TextOverflow.ellipsis);
      expect(find.byTooltip(long), findsOneWidget);
      // A code change, a sign-up and a leave are whole; only a swap with
      // two-digit codes may end in "…" (the tooltip has it all).
      for (final range in ['14/11/2026', '03–04/12/2026']) {
        expect(
          tester.renderObject<RenderParagraph>(find.text(range))
              .didExceedMaxLines,
          isFalse,
          reason: range,
        );
      }
      // Equal row heights, whatever the kind.
      final heights = {
        for (final r in rows)
          tester
              .getSize(
                find
                    .ancestor(
                      of: find.text(r.employee),
                      matching: find.byType(Container),
                    )
                    .first,
              )
              .height,
      };
      expect(heights, hasLength(1));
    });
  }
}
