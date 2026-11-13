// Time clock errors (review 2026-11-08, final wave): a refused check-out
// shows the backend's own sentence, an unreachable server a translated
// "server unavailable" — never "ApiException(409): ...". A controller
// disposed mid-request (logout) stores nothing and throws nothing.

import 'dart:async';

import 'package:attendance_scheduler_app/core/network/api_exception.dart';
import 'package:attendance_scheduler_app/features/attendance/data/datasources/time_clock_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/attendance/presentation/pages/time_clock_page.dart';
import 'package:attendance_scheduler_app/features/attendance/presentation/providers/time_clock_provider.dart';
import 'package:attendance_scheduler_app/i18n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

const _alreadyOut = 'You have already checked out today.';

final _today = TimeClockEntry(
  id: 1,
  userId: 7,
  workDate: DateTime(2026, 11, 8),
  checkInAt: DateTime(2026, 11, 8, 8),
);

/// Checked in today; check-out fails with [checkOutError].
class _Clock implements TimeClockRemoteDataSource {
  _Clock(this.checkOutError);

  final Object checkOutError;

  @override
  Future<ClockNow> now() async =>
      ClockNow(date: DateTime(2026, 11, 13), time: '08:00');

  @override
  Future<TimeClockEntry?> today() async => _today;

  @override
  Future<List<TimeClockEntry>> month(int year, int month) async => [_today];

  @override
  Future<TimeClockEntry> checkOut() async => throw checkOutError;

  @override
  dynamic noSuchMethod(Invocation i) => super.noSuchMethod(i);
}

/// Every call waits for the test.
class _Gated implements TimeClockRemoteDataSource {
  // load() asks the server clock first, so the load waits on this gate.
  final nowGate = Completer<ClockNow>();
  final todayGate = Completer<TimeClockEntry?>();
  final actionGate = Completer<TimeClockEntry>();

  @override
  Future<ClockNow> now() => nowGate.future;

  @override
  Future<TimeClockEntry?> today() => todayGate.future;

  @override
  Future<List<TimeClockEntry>> month(int year, int month) async => const [];

  @override
  Future<TimeClockEntry> checkIn() => actionGate.future;

  @override
  dynamic noSuchMethod(Invocation i) => super.noSuchMethod(i);
}

Future<void> _checkOut(WidgetTester tester, Object error) async {
  await tester.binding.setSurfaceSize(const Size(1400, 1000));
  addTearDown(() => tester.binding.setSurfaceSize(null));
  await tester.pumpWidget(ProviderScope(
    overrides: [
      timeClockRemoteDataSourceProvider.overrideWithValue(_Clock(error)),
    ],
    child: MaterialApp(
      localizationsDelegates: const [
        AppLocalizations.delegate,
        DefaultMaterialLocalizations.delegate,
        DefaultWidgetsLocalizations.delegate,
      ],
      supportedLocales: AppLocalizations.supportedLocales,
      locale: const Locale('en'),
      home: const Scaffold(body: TimeClockPage()),
    ),
  ));
  await tester.pumpAndSettle();
  await tester.tap(find.text('Check-out'));
  await tester.pumpAndSettle();
}

void main() {
  const en = AppLocalizations(Locale('en'));

  testWidgets('a 409 on check-out shows only the backend detail', (tester) async {
    await _checkOut(tester, const ApiException(_alreadyOut, statusCode: 409));

    expect(find.text(_alreadyOut), findsOneWidget);
    expect(find.textContaining('ApiException'), findsNothing);
    await tester.pump(const Duration(seconds: 10));
  });

  testWidgets('no response on check-out shows "server unavailable"', (tester) async {
    await _checkOut(
      tester,
      const ApiException('The connection errored: Connection refused'),
    );

    expect(find.text(en.text('requestServerUnavailable')), findsOneWidget);
    expect(find.textContaining('Connection refused'), findsNothing);
    await tester.pump(const Duration(seconds: 10));
  });

  test('a load or check-in finishing after dispose throws nothing', () async {
    final ds = _Gated();
    final ctrl = TimeClockController(ds);

    final load = ctrl.load();
    final checkIn = ctrl.checkIn();
    ctrl.dispose();
    ds.nowGate.completeError(const ApiException('late', statusCode: 500));
    ds.actionGate.completeError(const ApiException('late', statusCode: 500));

    await expectLater(load, completes);
    expect(await checkIn, isFalse);
  });

  test('a successful load finishing after dispose throws nothing', () async {
    final ds = _Gated();
    final ctrl = TimeClockController(ds);

    final load = ctrl.load();
    ctrl.dispose();
    ds.nowGate.complete(ClockNow(date: DateTime(2026, 11, 13), time: '08:00'));

    await expectLater(load, completes);
  });
}
