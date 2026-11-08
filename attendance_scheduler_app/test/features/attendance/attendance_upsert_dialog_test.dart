// The admin attendance dialog offers only the selected person's planned
// codes plus S, lists only active users (E), and a failed save shows the
// backend's detail instead of "ApiException(409): ..." (E, raw toasts).

import 'dart:convert';
import 'dart:typed_data';

import 'package:attendance_scheduler_app/core/constants/shift_codes.dart';
import 'package:attendance_scheduler_app/design_system/design_system.dart';
import 'package:attendance_scheduler_app/features/attendance/data/datasources/attendance_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/attendance/data/datasources/calculations_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/attendance/presentation/providers/attendance_provider.dart';
import 'package:attendance_scheduler_app/features/attendance/presentation/widgets/attendance_upsert_dialog.dart';
import 'package:attendance_scheduler_app/features/auth/domain/entities/user.dart';
import 'package:attendance_scheduler_app/features/users/data/user_management_datasource.dart';
import 'package:attendance_scheduler_app/i18n/app_localizations.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

class _Unused implements UserManagementDataSource, CalculationsRemoteDataSource {
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

/// Every request fails with HTTP 409 and a localized backend detail.
class _Conflict implements HttpClientAdapter {
  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async => ResponseBody.fromString(
    jsonEncode({'detail': 'Tháng này đã chốt công.'}),
    409,
    headers: {
      Headers.contentTypeHeader: [Headers.jsonContentType],
    },
  );

  @override
  void close({bool force = false}) {}
}

const _fixed = User(
  id: 1,
  username: 'alex',
  fullName: 'Alex Fixed',
  role: UserRole.a,
  status: 'active',
  code: 'A1',
);
const _flex = User(
  id: 2,
  username: 'tina',
  fullName: 'Tina Flex',
  role: UserRole.t,
  status: 'active',
  code: 'T1',
);
const _gone = User(
  id: 3,
  username: 'olaf',
  fullName: 'Olaf Disabled',
  role: UserRole.t,
  status: 'disabled',
  code: 'T2',
);

Future<void> _pump(WidgetTester tester, Widget dialog) async {
  await tester.binding.setSurfaceSize(const Size(1400, 1000));
  addTearDown(() => tester.binding.setSurfaceSize(null));
  final dio = Dio(BaseOptions(baseUrl: 'http://x/api/v1'))
    ..httpClientAdapter = _Conflict();
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        attendanceControllerProvider.overrideWith(
          (ref) => AttendanceController(
            AttendanceRemoteDataSource(dio),
            _Unused(),
            _Unused(),
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
        home: Scaffold(body: Center(child: dialog)),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

List<String> _menuCodes(WidgetTester tester) => tester
    .widget<DropdownButton<ShiftCode>>(find.byType(DropdownButton<ShiftCode>))
    .items!
    .map((item) => item.value!.code)
    .toList();

void main() {
  testWidgets('attendance_dialog_offers_role_codes_plus_S_active_users_only', (
    tester,
  ) async {
    await _pump(
      tester,
      const AttendanceUpsertDialog(users: [_fixed, _flex, _gone]),
    );

    // Only active people can be picked.
    final userIds = tester
        .widget<DropdownButton<int>>(find.byType(DropdownButton<int>))
        .items!
        .map((item) => item.value)
        .toList();
    expect(userIds, [1, 2]);

    await tester.tap(find.byType(DropdownButton<int>));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Tina Flex').last);
    await tester.pumpAndSettle();

    // A flexible person: AD/X/CD/T/B/AL plus S, defaulting to AD.
    expect(_menuCodes(tester), ['AD', 'X', 'CD', 'T', 'B', 'AL', 'S']);
    expect(
      tester
          .widget<DropdownButton<ShiftCode>>(find.byType(DropdownButton<ShiftCode>))
          .value?.code,
      'AD',
    );

    // Switching to a fixed person swaps the list and the default.
    await tester.tap(find.byType(DropdownButton<int>));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Alex Fixed').last);
    await tester.pumpAndSettle();
    expect(_menuCodes(tester), ['A', 'D', 'A/D', 'X', 'CD', 'T', 'B', 'AL', 'S']);
    expect(
      tester
          .widget<DropdownButton<ShiftCode>>(find.byType(DropdownButton<ShiftCode>))
          .value?.code,
      'A',
    );
  });

  testWidgets('error_toast_shows_backend_detail_not_exception_text', (
    tester,
  ) async {
    await _pump(
      tester,
      AttendanceUpsertDialog(
        users: const [_fixed],
        preselectedUserId: 1,
        preselectedDate: DateTime(2026, 11, 3),
      ),
    );

    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();

    expect(find.text('Tháng này đã chốt công.'), findsWidgets);
    expect(find.textContaining('ApiException'), findsNothing);
    expect(find.textContaining('DioException'), findsNothing);
    // Let the toast's auto-dismiss timer run out.
    await tester.pump(const Duration(seconds: 10));
  });
}
