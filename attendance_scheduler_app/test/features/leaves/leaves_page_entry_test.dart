// D4: the Leaves page reloads every time it is opened and has a refresh
// button. Leave dates (E): the end date never stays before the start date,
// and monthly leave pickers only offer the target month.

import 'package:attendance_scheduler_app/core/storage/locale_storage.dart';
import 'package:attendance_scheduler_app/design_system/design_system.dart';
import 'package:attendance_scheduler_app/features/auth/domain/entities/user.dart';
import 'package:attendance_scheduler_app/features/auth/domain/repositories/auth_repository.dart';
import 'package:attendance_scheduler_app/features/auth/presentation/providers/auth_provider.dart';
import 'package:attendance_scheduler_app/features/leaves/data/datasources/leaves_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/leaves/data/models/leave_model.dart';
import 'package:attendance_scheduler_app/features/leaves/presentation/pages/leaves_page.dart';
import 'package:attendance_scheduler_app/i18n/app_localizations.dart';
import 'package:attendance_scheduler_app/i18n/locale_provider.dart';
import 'package:flutter/material.dart';
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

/// Monthly leave targets December 2026; counts list calls.
class _Leaves implements LeavesRemoteDataSource {
  int listCalls = 0;

  @override
  Future<List<LeaveModel>> listOwn() async {
    listCalls++;
    return const [];
  }

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
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

const _anna = User(
  id: 7,
  username: 'anna',
  fullName: 'Anna',
  role: UserRole.t,
  status: 'active',
  code: 'T3',
);

Future<_Leaves> _pump(WidgetTester tester, {ValueNotifier<bool>? shown}) async {
  await tester.binding.setSurfaceSize(const Size(2000, 1400));
  addTearDown(() => tester.binding.setSurfaceSize(null));
  final leaves = _Leaves();
  final visible = shown ?? ValueNotifier(true);
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        authControllerProvider.overrideWith((ref) => _SignedIn(_anna)),
        leavesDataSourceProvider.overrideWithValue(leaves),
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
        home: Scaffold(
          body: ValueListenableBuilder<bool>(
            valueListenable: visible,
            builder: (_, show, _) =>
                show ? const LeavesPage() : const SizedBox.shrink(),
          ),
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
  return leaves;
}

Future<void> _pickDay(WidgetTester tester, String field, String day) async {
  await tester.tap(find.widgetWithText(TextField, field));
  await tester.pumpAndSettle();
  await tester.tap(find.text(day).last);
  await tester.pumpAndSettle();
  await tester.tap(find.text('OK'));
  await tester.pumpAndSettle();
}

String _fieldText(WidgetTester tester, String label) => tester
    .widget<TextField>(find.widgetWithText(TextField, label))
    .controller!
    .text;

void main() {
  testWidgets('leaves_page_reloads_on_entry_and_refresh_button', (
    tester,
  ) async {
    final shown = ValueNotifier(true);
    final leaves = await _pump(tester, shown: shown);
    expect(leaves.listCalls, 1);

    // Leave the page and come back: the list is fetched again.
    shown.value = false;
    await tester.pumpAndSettle();
    shown.value = true;
    await tester.pumpAndSettle();
    expect(leaves.listCalls, 2);

    await tester.tap(find.text('Refresh'));
    await tester.pumpAndSettle();
    expect(leaves.listCalls, 3);
  });

  testWidgets('end_date_resets_when_start_moves_past_it', (tester) async {
    await _pump(tester);
    await tester.tap(find.text('Request monthly leave'));
    await tester.pumpAndSettle();

    await _pickDay(tester, 'Start date', '10');
    expect(_fieldText(tester, 'End date'), '10/12/2026');

    await _pickDay(tester, 'Start date', '25');
    expect(_fieldText(tester, 'Start date'), '25/12/2026');
    expect(_fieldText(tester, 'End date'), '25/12/2026');

    // The end picker opens (its initial date is no longer before firstDate).
    await tester.tap(find.widgetWithText(TextField, 'End date'));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    expect(find.byType(DatePickerDialog), findsOneWidget);
  });

  testWidgets('monthly_picker_bounded_to_target_month', (tester) async {
    await _pump(tester);
    await tester.tap(find.text('Request monthly leave'));
    await tester.pumpAndSettle();

    await tester.tap(find.widgetWithText(TextField, 'Start date'));
    await tester.pumpAndSettle();
    var picker = tester.widget<DatePickerDialog>(find.byType(DatePickerDialog));
    expect(picker.firstDate, DateTime(2026, 12, 1));
    expect(picker.lastDate, DateTime(2026, 12, 31));
    await tester.tap(find.text('12').last);
    await tester.pumpAndSettle();
    await tester.tap(find.text('OK'));
    await tester.pumpAndSettle();

    await tester.tap(find.widgetWithText(TextField, 'End date'));
    await tester.pumpAndSettle();
    picker = tester.widget<DatePickerDialog>(find.byType(DatePickerDialog));
    expect(picker.firstDate, DateTime(2026, 12, 12));
    expect(picker.lastDate, DateTime(2026, 12, 31));
  });
}
