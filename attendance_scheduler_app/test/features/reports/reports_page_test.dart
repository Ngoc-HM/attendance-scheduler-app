// D5: the year / month / format selectors sit on the Reports page with
// translated labels, and "Full year" exports through the yearly endpoint
// (month stays null, never month 0, which the backend rejects).

import 'dart:convert';
import 'dart:typed_data';

import 'package:attendance_scheduler_app/design_system/design_system.dart';
import 'package:attendance_scheduler_app/features/reports/data/datasources/reports_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/reports/presentation/pages/reports_page.dart';
import 'package:attendance_scheduler_app/features/reports/presentation/providers/reports_provider.dart';
import 'package:attendance_scheduler_app/i18n/app_localizations.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

class _RecordingReports extends ReportsRemoteDataSource {
  _RecordingReports() : super(Dio());

  final monthlyCalls = <(int, int, String)>[];
  final yearlyCalls = <(int, String)>[];

  @override
  Future<ReportDownload> monthly(int year, int month, String format) async {
    monthlyCalls.add((year, month, format));
    return const ReportDownload(bytes: [1], filename: 'm.csv');
  }

  @override
  Future<ReportDownload> yearly(int year, String format) async {
    yearlyCalls.add((year, format));
    return const ReportDownload(bytes: [1], filename: 'y.csv');
  }
}

/// Every download fails with 409 and a JSON detail in the (bytes) body.
class _Conflict implements HttpClientAdapter {
  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async => ResponseBody.fromString(
    jsonEncode({'detail': 'Không có dữ liệu cho tháng này.'}),
    409,
    headers: {
      Headers.contentTypeHeader: [Headers.jsonContentType],
    },
  );

  @override
  void close({bool force = false}) {}
}

void main() {
  testWidgets('reports_selectors_on_page_full_year_uses_null_month', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(1600, 1200));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final reports = _RecordingReports();
    late ReportsController ctrl;
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          reportsControllerProvider.overrideWith(
            (ref) => ctrl = ReportsController(
              reports,
              saveFile: (bytes, name) async => '/downloads/$name',
            ),
          ),
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
          home: const Scaffold(body: ReportsPage()),
        ),
      ),
    );
    await tester.pumpAndSettle();

    // Selectors are on the page itself, with translated labels.
    expect(find.text('Year'), findsOneWidget);
    expect(find.text('Month'), findsOneWidget);
    expect(find.text('Format'), findsOneWidget);
    expect(find.textContaining('year:'), findsNothing);

    await tester.tap(find.byType(DropdownButtonFormField<int?>));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Full year').last);
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    expect(ctrl.state.selectedMonth, isNull);

    await tester.tap(find.text('Export'));
    await tester.pumpAndSettle();

    expect(reports.monthlyCalls, isEmpty);
    expect(reports.yearlyCalls, [(ctrl.state.selectedYear!, 'csv')]);
    expect(find.text('Report saved to /downloads/y.csv'), findsOneWidget);
    // Let the toast's auto-dismiss timer run out.
    await tester.pump(const Duration(seconds: 10));
  });

  test('a failed download surfaces the backend detail', () async {
    final dio = Dio(BaseOptions(baseUrl: 'http://x/api/v1'))
      ..httpClientAdapter = _Conflict();
    final ctrl = ReportsController(ReportsRemoteDataSource(dio));

    final result = await ctrl.exportMonthly();

    expect(result, isA<ExportFailure>());
    expect(
      (result as ExportFailure).message,
      'Không có dữ liệu cho tháng này.',
    );
  });
}
