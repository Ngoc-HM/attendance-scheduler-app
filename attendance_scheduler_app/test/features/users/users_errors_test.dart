// User-management errors (review 2026-11-08 D2): the backend's own message
// (last-admin lockout, duplicate username, not pending, quota out of range)
// reaches the admin instead of a generic "Could not load users.".

import 'dart:convert';
import 'dart:typed_data';

import 'package:attendance_scheduler_app/core/network/api_exception.dart';
import 'package:attendance_scheduler_app/core/storage/locale_storage.dart';
import 'package:attendance_scheduler_app/features/auth/domain/entities/user.dart';
import 'package:attendance_scheduler_app/features/auth/domain/repositories/auth_repository.dart';
import 'package:attendance_scheduler_app/features/auth/presentation/providers/auth_provider.dart';
import 'package:attendance_scheduler_app/features/users/data/user_management_datasource.dart';
import 'package:attendance_scheduler_app/features/users/presentation/pages/users_page.dart';
import 'package:attendance_scheduler_app/features/users/presentation/widgets/create_user_dialog.dart';
import 'package:attendance_scheduler_app/i18n/app_localizations.dart';
import 'package:attendance_scheduler_app/i18n/locale_provider.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

const _lastAdmin = 'You cannot remove or disable the last remaining admin.';
const _taken = 'That username is already taken.';
const _notPending = 'Only a pending account can be approved.';
const _quotaMsg = 'Input should be less than or equal to 365';

/// Backend stand-in answering with the real status codes and `detail`
/// shapes: a string for HTTPException, a list for pydantic's 422.
class _Backend implements HttpClientAdapter {
  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<Uint8List>? s, Future<void>? c) async {
    ResponseBody json(Object body, int code) => ResponseBody.fromString(jsonEncode(body), code,
        headers: {Headers.contentTypeHeader: [Headers.jsonContentType]});
    final path = o.uri.path;
    if (o.method == 'GET' && path.endsWith('/users')) {
      return json([
        {'id': 1, 'username': 'admin', 'code': 'M1', 'full_name': 'Admin', 'role': 'M', 'status': 'active', 'carry_comp': 0, 'carry_streak': 0, 'annual_leave_quota': 30},
        {'id': 5, 'username': 'newbie', 'code': 'T9', 'full_name': 'Newbie', 'role': 'T', 'status': 'pending', 'carry_comp': 0, 'carry_streak': 0, 'annual_leave_quota': 30},
      ], 200);
    }
    if (o.method == 'PATCH') {
      final data = o.data as Map<String, dynamic>;
      if (data.containsKey('annual_leave_quota')) {
        return json({
          'detail': [
            {'type': 'less_than_equal', 'loc': ['body', 'annual_leave_quota'], 'msg': _quotaMsg, 'input': 400, 'ctx': {'le': 365}},
          ],
        }, 422);
      }
      return json({'detail': _lastAdmin}, 409);
    }
    if (o.method == 'POST' && path.endsWith('/approve')) return json({'detail': _notPending}, 409);
    if (o.method == 'POST' && path.endsWith('/users')) return json({'detail': _taken}, 409);
    if (o.method == 'DELETE') return ResponseBody.fromString('<html>Internal Server Error</html>', 500);
    return json({'detail': 'nope'}, 404);
  }

  @override
  void close({bool force = false}) {}
}

class _Noop implements AuthRepository {
  @override
  dynamic noSuchMethod(Invocation i) => super.noSuchMethod(i);
}

class _SignedIn extends AuthController {
  _SignedIn(User u) : super(_Noop(), LocaleController(LocaleStorage())) {
    state = AuthState(user: u);
  }
}

const _me = User(id: 1, username: 'admin', fullName: 'Admin', role: UserRole.m, status: 'active', code: 'M1');

UserManagementDataSource _ds() =>
    UserManagementDataSource(Dio(BaseOptions(baseUrl: 'http://x/api/v1'))..httpClientAdapter = _Backend());

Future<ApiException> _failure(Future<Object?> Function() call) async {
  try {
    await call();
  } on ApiException catch (e) {
    return e;
  }
  fail('expected an ApiException');
}

Future<void> _pump(WidgetTester tester, Widget home) async {
  await tester.binding.setSurfaceSize(const Size(2000, 1200));
  addTearDown(() => tester.binding.setSurfaceSize(null));
  await tester.pumpWidget(ProviderScope(
    overrides: [
      authControllerProvider.overrideWith((ref) => _SignedIn(_me)),
      userManagementDataSourceProvider.overrideWithValue(_ds()),
    ],
    child: MaterialApp(
      localizationsDelegates: const [AppLocalizations.delegate, DefaultMaterialLocalizations.delegate, DefaultWidgetsLocalizations.delegate],
      supportedLocales: AppLocalizations.supportedLocales,
      locale: const Locale('en'),
      home: Scaffold(body: home),
    ),
  ));
  await tester.pumpAndSettle();
}

Finder _inDialog(Finder f) => find.descendant(of: find.byType(AlertDialog), matching: f);

/// Lets the feedback toast's dismiss timer run out before the test ends.
Future<void> _clearToast(WidgetTester tester) => tester.pump(const Duration(seconds: 10));

void main() {
  group('user_errors_surface_backend_detail', () {
    test('the datasource throws ApiException with the status and backend detail', () async {
      final ds = _ds();

      final lastAdmin = await _failure(() => ds.update(1, {'status': 'disabled'}));
      expect((lastAdmin.statusCode, lastAdmin.message), (409, _lastAdmin));

      final taken = await _failure(() => ds.create(username: 'admin', fullName: 'Dup', password: 'secret123', role: 'T'));
      expect((taken.statusCode, taken.message), (409, _taken));

      final notPending = await _failure(() => ds.approve(5, role: 'T'));
      expect((notPending.statusCode, notPending.message), (409, _notPending));

      // pydantic's 422 list is flattened to its messages, not shown raw.
      final quota = await _failure(() => ds.update(5, {'annual_leave_quota': 400}));
      expect((quota.statusCode, quota.message), (422, _quotaMsg));

      // A 5xx HTML body still becomes an ApiException.
      final crash = await _failure(() => ds.delete(5));
      expect(crash.statusCode, 500);
    });

    testWidgets('last-admin 409 on Disable shows the backend message', (tester) async {
      await _pump(tester, const UsersPage());
      await tester.tap(find.byTooltip('Actions').first);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Disable'));
      await tester.pumpAndSettle();
      await tester.tap(_inDialog(find.text('Confirm')));
      await tester.pumpAndSettle();

      expect(find.text(_lastAdmin), findsOneWidget);
      expect(find.text('Could not load users.'), findsNothing);
      await _clearToast(tester);
    });

    testWidgets('not_pending 409 on Approve shows the backend message', (tester) async {
      await _pump(tester, const UsersPage());
      await tester.tap(find.text('Approve'));
      await tester.pumpAndSettle();
      await tester.tap(_inDialog(find.text('Approve')));
      await tester.pumpAndSettle();

      expect(find.text(_notPending), findsOneWidget);
      await _clearToast(tester);
    });

    testWidgets('quota 422 shows the validation message, not the raw list', (tester) async {
      await _pump(tester, const UsersPage());
      await tester.tap(find.byTooltip('Actions').last);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Edit leave quota').last);
      await tester.pumpAndSettle();
      await tester.enterText(_inDialog(find.byType(TextField)), '300');
      await tester.tap(_inDialog(find.text('Save')));
      await tester.pumpAndSettle();

      expect(find.text(_quotaMsg), findsOneWidget);
      expect(find.textContaining('less_than_equal'), findsNothing);
      await _clearToast(tester);
    });

    testWidgets('a 5xx on Delete shows a localized server error', (tester) async {
      await _pump(tester, const UsersPage());
      await tester.tap(find.byTooltip('Actions').last);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Delete').last);
      await tester.pumpAndSettle();
      await tester.tap(_inDialog(find.text('Delete')));
      await tester.pumpAndSettle();

      expect(find.text(const AppLocalizations(Locale('en')).text('requestServerError')), findsOneWidget);
      expect(find.textContaining('html'), findsNothing);
      await _clearToast(tester);
    });

    testWidgets('duplicate username 409 in the create dialog shows the backend message', (tester) async {
      await _pump(tester, const CreateUserDialog());
      final fields = find.byType(TextFormField);
      await tester.enterText(fields.at(0), 'admin');
      await tester.enterText(fields.at(1), 'Dup');
      await tester.enterText(fields.at(2), 'secret123');
      await tester.tap(find.text('Create'));
      await tester.pumpAndSettle();

      expect(find.text(_taken), findsOneWidget);
      expect(find.text(const AppLocalizations(Locale('en')).createUserFailed), findsNothing);
    });
  });
}
