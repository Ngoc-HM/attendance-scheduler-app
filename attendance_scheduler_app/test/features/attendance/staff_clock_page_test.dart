// Admin's clock tab (2026-11-13): everyone's punches of the month, a
// forgotten check-out flagged, and a correction sent in Frankfurt time.

import 'package:attendance_scheduler_app/design_system/design_system.dart';
import 'package:attendance_scheduler_app/features/attendance/data/datasources/time_clock_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/attendance/presentation/pages/staff_clock_page.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

class _FakeClock extends TimeClockRemoteDataSource {
  _FakeClock() : super(Dio());

  final corrections = <Map<String, Object?>>[];
  List<StaffClockEntry> entries = [
    StaffClockEntry(
      userId: 3,
      workDate: DateTime(2026, 11, 12),
      fullName: 'Vũ Văn Long',
      code: 'F1',
      checkIn: '16:28',
    ),
  ];

  @override
  Future<List<StaffClockEntry>> staffMonth(int year, int month) async =>
      entries;

  @override
  Future<void> correct({
    required int userId,
    required DateTime workDate,
    required String checkIn,
    String? checkOut,
  }) async {
    corrections.add({'user': userId, 'in': checkIn, 'out': checkOut});
    entries = [
      StaffClockEntry(
        userId: userId,
        workDate: workDate,
        fullName: 'Vũ Văn Long',
        code: 'F1',
        checkIn: checkIn,
        checkOut: checkOut,
      ),
    ];
  }
}

void main() {
  testWidgets('lists punches and flags a forgotten check-out', (tester) async {
    await tester.binding.setSurfaceSize(const Size(1280, 800));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final ds = _FakeClock();
    await tester.pumpWidget(ProviderScope(
      overrides: [timeClockRemoteDataSourceProvider.overrideWithValue(ds)],
      child: MaterialApp(
        theme: AppTheme.light,
        home: const Scaffold(body: StaffClockPage()),
      ),
    ));
    await tester.pumpAndSettle();

    expect(find.text('F1 · Vũ Văn Long'), findsOneWidget);
    expect(find.text('16:28'), findsOneWidget);
    expect(find.text('No check-out'), findsOneWidget); // the row's note
    expect(find.text('No check-out (1)'), findsOneWidget); // the filter

    await tester.tap(find.text('No check-out (1)'));
    await tester.pumpAndSettle();
    expect(find.text('F1 · Vũ Văn Long'), findsOneWidget);
  });
}
