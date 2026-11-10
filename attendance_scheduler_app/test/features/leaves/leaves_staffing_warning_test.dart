// Flight-staffing risk stays on the leave's row (owner 2026-11-10): the
// approval toast disappears, so the admin's list shows the backend's
// translated lines under that row's cells — and nothing on other rows.

import 'package:attendance_scheduler_app/design_system/design_system.dart';
import 'package:attendance_scheduler_app/features/auth/domain/entities/user.dart';
import 'package:attendance_scheduler_app/features/leaves/data/models/leave_model.dart';
import 'package:attendance_scheduler_app/features/leaves/presentation/providers/leaves_provider.dart';
import 'package:attendance_scheduler_app/i18n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

const _risk = [
  '2026-12-04: 1 short on the DEP shift',
  '2026-12-06: 1 short on the ARR shift',
  '2026-12-06: 2 short on the DEP shift',
];

DsLeaveRowData _row({
  String employee = 'A1',
  String status = 'Approved',
  List<String> warnings = const [],
}) => DsLeaveRowData(
  employee: employee,
  role: 'A',
  type: 'Monthly leave',
  range: '04–06/12/2026',
  days: 3,
  status: status,
  carryComp: 0,
  staffingWarnings: warnings,
);

/// The test font (Ahem) draws every glyph a full em wide, about twice a real
/// UI font, so the page's existing header and Approve/Reject buttons already
/// overflow at 1280 px in it (the other leave tests use a 2000 px surface).
/// [realisticWidths] scales text to roughly a UI font's glyph width, so the
/// minimum-window check measures the layout rather than the test font.
const _uiFontWidth = TextScaler.linear(0.55);

Future<void> _pump(
  WidgetTester tester,
  List<DsLeaveRowData> rows, {
  Size size = const Size(2000, 1000),
  bool realisticWidths = false,
}) async {
  await tester.binding.setSurfaceSize(size);
  addTearDown(() => tester.binding.setSurfaceSize(null));
  await tester.pumpWidget(
    MaterialApp(
      theme: AppTheme.light,
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: AppLocalizations.supportedLocales,
      locale: const Locale('en'),
      builder: (context, child) => realisticWidths
          ? MediaQuery(
              data: MediaQuery.of(context).copyWith(textScaler: _uiFontWidth),
              child: child!,
            )
          : child!,
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
}

/// The row container (the data row's padded box) holding [employee]'s cell.
Finder _rowOf(String employee) => find
    .ancestor(of: find.text(employee), matching: find.byType(Container))
    .first;

void main() {
  testWidgets('a row with risk shows every line on the row, with an icon', (
    tester,
  ) async {
    await _pump(tester, [
      _row(warnings: _risk),
      _row(employee: 'A2', status: 'Pending'),
    ]);

    for (final line in _risk) {
      expect(find.text(line), findsOneWidget);
    }
    expect(find.byIcon(Icons.warning_amber_outlined), findsOneWidget);

    // The lines sit under A1's cells, above A2's row — inside A1's row.
    final a1Bottom = tester.getBottomLeft(find.text('A1')).dy;
    final a2Top = tester.getTopLeft(find.text('A2')).dy;
    for (final line in _risk) {
      final y = tester.getTopLeft(find.text(line)).dy;
      expect(y, greaterThan(a1Bottom));
      expect(y, lessThan(a2Top));
    }
    // Stacked: one line per row of text.
    final ys = [for (final l in _risk) tester.getTopLeft(find.text(l)).dy];
    expect(ys, orderedEquals([...ys]..sort()));
    expect(ys.toSet(), hasLength(_risk.length));
    expect(tester.takeException(), isNull);
  });

  testWidgets('rows without risk show nothing and keep their height', (
    tester,
  ) async {
    await _pump(tester, [_row(), _row(employee: 'A2', status: 'Pending')]);
    expect(find.byIcon(Icons.warning_amber_outlined), findsNothing);
    final plain = tester.getSize(_rowOf('A1')).height;

    await _pump(tester, [
      _row(),
      _row(employee: 'A2', status: 'Pending', warnings: _risk),
    ]);
    expect(tester.getSize(_rowOf('A1')).height, plain);
    expect(tester.getSize(_rowOf('A2')).height, greaterThan(plain));
  });

  testWidgets('long and many lines do not overflow at 1280x720', (
    tester,
  ) async {
    final many = [
      for (var d = 1; d <= 14; d++)
        '2026-12-${d.toString().padLeft(2, '0')}: còn 1 người nhóm A, '
            'cần 1 ca ARR + 2 ca DEP — '
            '${'một dòng rất dài để thử xuống dòng ' * 4}',
    ];
    final rows = [
      _row(warnings: many),
      _row(employee: 'A2', status: 'Pending', warnings: _risk),
    ];
    await _pump(
      tester,
      rows,
      size: const Size(1280, 720),
      realisticWidths: true,
    );
    expect(tester.takeException(), isNull);
    expect(find.text(many.first), findsOneWidget);
    // The columns keep their places: the dates cell starts where it does on
    // a row without warnings.
    final withRisk = tester.getTopLeft(find.text('04–06/12/2026').first).dx;
    await _pump(
      tester,
      [_row(), _row(employee: 'A2', status: 'Pending')],
      size: const Size(1280, 720),
      realisticWidths: true,
    );
    expect(tester.takeException(), isNull);
    expect(tester.getTopLeft(find.text('04–06/12/2026').first).dx, withRisk);

    // Narrower than the admin table's minimum (the content area beside the
    // navigation): the table scrolls sideways instead.
    await _pump(
      tester,
      rows,
      size: const Size(900, 720),
      realisticWidths: true,
    );
    expect(tester.takeException(), isNull);
  });

  group('mapping', () {
    test('LeaveModel reads staffing_warnings, empty when absent', () {
      final json = {
        'id': 3,
        'user_id': 9,
        'start_date': '2026-12-04',
        'end_date': '2026-12-06',
        'leave_type': 'monthly',
        'status': 'pending',
        'note': null,
        'warnings': <String>[],
        'staffing_warnings': _risk,
      };
      expect(LeaveModel.fromJson(json).staffingWarnings, _risk);
      expect(
        LeaveModel.fromJson({...json}..remove('staffing_warnings'))
            .staffingWarnings,
        isEmpty,
      );
    });

    test('the row carries the lines; copyWith keeps them', () {
      final model = LeaveModel.fromJson({
        'id': 3,
        'user_id': 9,
        'start_date': '2026-12-04',
        'end_date': '2026-12-06',
        'leave_type': 'monthly',
        'status': 'approved',
        'staffing_warnings': _risk,
      });
      const user = User(
        id: 9,
        username: 'a1',
        fullName: 'A One',
        role: UserRole.a,
        status: 'active',
        code: 'A1',
      );
      final row = LeavesController.toRow(model, {9: user});
      expect(row.employee, 'A1');
      expect(row.staffingWarnings, _risk);
      expect(row.copyWith(status: 'Rejected').staffingWarnings, _risk);
    });
  });
}
