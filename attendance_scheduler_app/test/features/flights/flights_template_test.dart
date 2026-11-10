// The month's blank flight-plan template: admins download it for the month
// shown (saved to the downloads folder), the page skips the request when no
// preset is active, and importing a filled template shows the month it was
// for.

import 'dart:typed_data';

import 'package:attendance_scheduler_app/core/storage/locale_storage.dart';
import 'package:attendance_scheduler_app/core/utils/file_download.dart';
import 'package:attendance_scheduler_app/design_system/design_system.dart';
import 'package:attendance_scheduler_app/features/auth/domain/entities/user.dart';
import 'package:attendance_scheduler_app/features/auth/domain/repositories/auth_repository.dart';
import 'package:attendance_scheduler_app/features/auth/presentation/providers/auth_provider.dart';
import 'package:attendance_scheduler_app/features/flights/data/datasources/flights_remote_datasource.dart';
import 'package:attendance_scheduler_app/features/flights/data/models/flight_day_model.dart';
import 'package:attendance_scheduler_app/features/flights/data/models/flight_preset_model.dart';
import 'package:attendance_scheduler_app/features/flights/presentation/pages/flights_page.dart';
import 'package:attendance_scheduler_app/features/flights/presentation/providers/flights_provider.dart';
import 'package:attendance_scheduler_app/features/home/presentation/pages/home_shell.dart';
import 'package:attendance_scheduler_app/i18n/app_localizations.dart';
import 'package:attendance_scheduler_app/i18n/locale_provider.dart';
import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
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

FlightPresetModel _preset({required bool active}) => FlightPresetModel(
  id: 1,
  label: 'Morning',
  fltArr: 100,
  fltDep: 101,
  sta: '08:00',
  std: '09:00',
  sortOrder: 0,
  isActive: active,
);

FlightModel _flight(DateTime day) =>
    FlightModel(id: day.day, day: day, fltNumber: 100);

class _Flights extends FlightsRemoteDataSource {
  _Flights({this.presets = const [], this.imported = const []})
    : super(Dio());

  final List<FlightPresetModel> presets;
  final List<FlightModel> imported;
  final loaded = <(int, int)>[];
  final templateCalls = <(int, int)>[];

  @override
  Future<List<FlightDayModel>> listDays(int year, int month) async {
    loaded.add((year, month));
    return const [];
  }

  @override
  Future<List<FlightPresetModel>> listPresets() async => presets;

  @override
  Future<FileDownload> downloadTemplate(int year, int month) async {
    templateCalls.add((year, month));
    return FileDownload(
      bytes: const [1, 2, 3],
      filename: 'flight-plan-$year-${month.toString().padLeft(2, '0')}.xlsx',
    );
  }

  @override
  Future<List<FlightModel>> importExcel(PlatformFile file) async => imported;
}

/// Answers every request with xlsx bytes and, when set, [disposition].
class _TemplateAdapter implements HttpClientAdapter {
  _TemplateAdapter(this.disposition);

  final String? disposition;
  RequestOptions? last;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    last = options;
    return ResponseBody.fromBytes(
      [7, 8, 9],
      200,
      headers: {
        if (disposition != null) 'content-disposition': [disposition!],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}

final _xlsx = PlatformFile(name: 'plan.xlsx', size: 1, bytes: null);

Future<void> _pumpFlights(
  WidgetTester tester, {
  required User user,
  required _Flights ds,
  Size size = const Size(1600, 1000),
  Locale locale = const Locale('en'),
  bool inShell = false,
}) async {
  await tester.binding.setSurfaceSize(size);
  addTearDown(() => tester.binding.setSurfaceSize(null));
  const page = FlightsPage();
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        authControllerProvider.overrideWith(
          (ref) => _SignedInAuthController(user),
        ),
        flightsDataSourceProvider.overrideWithValue(ds),
        flightsControllerProvider.overrideWith(
          (ref) => FlightsController(
            ds,
            saveFile: (bytes, name) async => '/downloads/$name',
          ),
        ),
      ],
      child: MaterialApp(
        theme: AppTheme.light,
        localizationsDelegates: const [
          AppLocalizations.delegate,
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: AppLocalizations.supportedLocales,
        locale: locale,
        home: inShell
            ? const HomeShell(location: '/flights', child: page)
            : const Scaffold(body: page),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  test('the data source reads the filename, with a fallback', () async {
    final named = _TemplateAdapter(
      'attachment; filename="flight-plan-2026-12.xlsx"',
    );
    final ds = FlightsRemoteDataSource(
      Dio(BaseOptions(baseUrl: 'http://x/api/v1'))..httpClientAdapter = named,
    );
    final download = await ds.downloadTemplate(2026, 12);
    expect(named.last!.path, '/flights/template');
    expect(named.last!.queryParameters, {'year': 2026, 'month': 12});
    expect(download.bytes, [7, 8, 9]);
    expect(download.filename, 'flight-plan-2026-12.xlsx');

    final unnamed = _TemplateAdapter(null);
    final fallback = await FlightsRemoteDataSource(
      Dio(BaseOptions(baseUrl: 'http://x/api/v1'))..httpClientAdapter = unnamed,
    ).downloadTemplate(2027, 3);
    expect(fallback.filename, 'flight-plan-2027-03.xlsx');
  });

  test('downloadTemplate requests the shown month and saves the file', () async {
    final ds = _Flights();
    final saved = <(List<int>, String)>[];
    final ctrl = FlightsController(
      ds,
      saveFile: (bytes, name) async {
        saved.add((bytes, name));
        return '/downloads/$name';
      },
    );
    await Future<void>.delayed(Duration.zero);
    ctrl.nextMonth();
    final month = ctrl.state.month;
    final name =
        'flight-plan-${month.year}-${month.month.toString().padLeft(2, '0')}.xlsx';

    final path = await ctrl.downloadTemplate();

    expect(ds.templateCalls, [(month.year, month.month)]);
    expect(saved, hasLength(1));
    expect(saved.single.$1, [1, 2, 3]);
    expect(saved.single.$2, name);
    expect(path, '/downloads/$name');
  });

  group('importExcel shows the imported month', () {
    test('a single other month switches the page to it', () async {
      final now = DateTime.now();
      final other = DateTime(now.year, now.month + 3);
      final ds = _Flights(
        imported: [
          _flight(DateTime(other.year, other.month, 2)),
          _flight(DateTime(other.year, other.month, 20)),
        ],
      );
      final ctrl = FlightsController(ds);

      expect(await ctrl.importExcel(_xlsx), 2);
      expect(ctrl.state.month, other);
      expect(ds.loaded.last, (other.year, other.month));
    });

    test('the month shown stays when the flights are in it', () async {
      final now = DateTime.now();
      final shown = DateTime(now.year, now.month);
      final ds = _Flights(imported: [_flight(DateTime(now.year, now.month, 5))]);
      final ctrl = FlightsController(ds);

      await ctrl.importExcel(_xlsx);
      expect(ctrl.state.month, shown);
      expect(ds.loaded.last, (shown.year, shown.month));
    });

    test('flights spanning two months leave the page where it is', () async {
      final now = DateTime.now();
      final shown = DateTime(now.year, now.month);
      final ds = _Flights(
        imported: [
          _flight(DateTime(now.year, now.month + 1, 28)),
          _flight(DateTime(now.year, now.month + 2, 1)),
        ],
      );
      final ctrl = FlightsController(ds);

      await ctrl.importExcel(_xlsx);
      expect(ctrl.state.month, shown);
      expect(ds.loaded.last, (shown.year, shown.month));
    });

    test('an empty import leaves the page where it is', () async {
      final now = DateTime.now();
      final ds = _Flights();
      final ctrl = FlightsController(ds);

      expect(await ctrl.importExcel(_xlsx), 0);
      expect(ctrl.state.month, DateTime(now.year, now.month));
    });
  });

  testWidgets('admin downloads the template and sees the saved path', (
    tester,
  ) async {
    final ds = _Flights(presets: [_preset(active: true)]);
    await _pumpFlights(tester, user: _admin, ds: ds);

    final button = find.widgetWithText(DsSecondaryButton, 'Download template');
    expect(button, findsOneWidget);
    // Placed just before "Import Excel".
    final download = tester.getTopLeft(button).dx;
    final import = tester
        .getTopLeft(find.widgetWithText(DsSecondaryButton, 'Import Excel'))
        .dx;
    expect(download, lessThan(import));

    await tester.tap(button);
    await tester.pumpAndSettle();

    final now = DateTime.now();
    final name =
        'flight-plan-${now.year}-${now.month.toString().padLeft(2, '0')}.xlsx';
    expect(ds.templateCalls, [(now.year, now.month)]);
    expect(find.text('Template saved to /downloads/$name'), findsOneWidget);
    await tester.pump(const Duration(seconds: 10));
  });

  testWidgets('no download button for a non-admin', (tester) async {
    await _pumpFlights(tester, user: _employee, ds: _Flights());

    expect(find.text('Download template'), findsNothing);
    expect(find.text('Import Excel'), findsNothing);
  });

  testWidgets('no active preset: the hint, and no request', (tester) async {
    final ds = _Flights(presets: [_preset(active: false)]);
    await _pumpFlights(tester, user: _admin, ds: ds);

    await tester.tap(find.text('Download template'));
    await tester.pumpAndSettle();

    expect(ds.templateCalls, isEmpty);
    expect(
      find.text(AppLocalizations(const Locale('en')).text('noPresetsMessage')),
      findsOneWidget,
    );
    await tester.pump(const Duration(seconds: 10));
  });

  for (final locale in const [Locale('en'), Locale('vi')]) {
    testWidgets(
      'four header actions fit the minimum window (${locale.languageCode})',
      (tester) async {
        await _pumpFlights(
          tester,
          user: _admin,
          ds: _Flights(presets: [_preset(active: true)]),
          size: const Size(1280, 720),
          locale: locale,
          inShell: true,
        );

        // No overflow, and the title keeps a readable width.
        expect(tester.takeException(), isNull);
        expect(find.byType(DsSecondaryButton), findsNWidgets(3));
        final title = AppLocalizations(locale).text('flightsTitle');
        Finder inHeader(Finder f) =>
            find.descendant(of: find.byType(DsPageHeader), matching: f);
        expect(
          tester.getSize(inHeader(find.text(title))).width,
          greaterThan(200),
        );
        final add = AppLocalizations(locale).text('addFlight');
        expect(
          tester.getTopRight(inHeader(find.text(add))).dx,
          lessThanOrEqualTo(1280),
        );
      },
    );
  }
}
