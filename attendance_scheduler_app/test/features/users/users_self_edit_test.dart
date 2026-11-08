// An admin editing their own account (review 2026-11-08 E): the app re-reads
// GET /users/me so a self-demotion drops the admin UI straight away, and a
// self-disable ends the session.

import 'package:attendance_scheduler_app/core/storage/token_storage.dart';
import 'package:attendance_scheduler_app/features/auth/data/models/user_model.dart';
import 'package:attendance_scheduler_app/features/auth/data/repositories/auth_repository_impl.dart';
import 'package:attendance_scheduler_app/features/auth/domain/entities/user.dart';
import 'package:attendance_scheduler_app/features/auth/domain/repositories/auth_repository.dart';
import 'package:attendance_scheduler_app/features/auth/presentation/providers/auth_provider.dart';
import 'package:attendance_scheduler_app/features/users/data/user_management_datasource.dart';
import 'package:attendance_scheduler_app/features/users/presentation/pages/users_page.dart';
import 'package:attendance_scheduler_app/i18n/app_localizations.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

const _admin = UserModel(id: 1, username: 'admin', fullName: 'Admin', role: UserRole.m, status: 'active', code: 'M1');
const _other = UserModel(id: 2, username: 'boss', fullName: 'Boss', role: UserRole.m, status: 'active', code: 'M2');
const _demoted = UserModel(id: 1, username: 'admin', fullName: 'Admin', role: UserRole.t, status: 'active', code: 'T5');

class _MemoryTokenStorage extends TokenStorage {
  String? token;

  @override
  Future<void> save(String value) async => token = value;

  @override
  Future<String?> read() async => token;

  @override
  Future<void> clear() async => token = null;
}

/// Signs in the admin; `GET /users/me` answers [me] or throws [meError].
class _Repo implements AuthRepository {
  User me = _admin;
  Object? meError;
  int currentUserCalls = 0;

  @override
  Future<User> login(String u, String p) async => _admin;

  @override
  Future<User> currentUser() async {
    currentUserCalls++;
    if (meError != null) throw meError!;
    return me;
  }

  bool loggedOut = false;

  @override
  Future<void> logout() async => loggedOut = true;

  @override
  dynamic noSuchMethod(Invocation i) => super.noSuchMethod(i);
}

class _Users implements UserManagementDataSource {
  final updates = <(int, Map<String, dynamic>)>[];
  final deleted = <int>[];
  late final _Repo repo;

  /// GET /users calls made after a delete while still signed in: with a
  /// deleted account's token the real backend answers 401, which ends the
  /// session as "expired".
  int listsAfterDelete = 0;

  @override
  Future<List<UserModel>> list() async {
    if (deleted.isNotEmpty && !repo.loggedOut) listsAfterDelete++;
    return const [_admin, _other];
  }

  @override
  Future<void> delete(int id) async => deleted.add(id);

  @override
  Future<UserUpdateResult> update(int id, Map<String, dynamic> changes) async {
    updates.add((id, changes));
    return UserUpdateResult(user: id == 1 ? _demoted : _other, warnings: const []);
  }

  @override
  dynamic noSuchMethod(Invocation i) => super.noSuchMethod(i);
}

DioException _forbidden() {
  final request = RequestOptions(path: '/users/me');
  return DioException(
    requestOptions: request,
    response: Response(requestOptions: request, statusCode: 403, data: {'detail': 'User account is not active.'}),
    type: DioExceptionType.badResponse,
  );
}

Future<(ProviderContainer, _Repo, _Users)> _pump(WidgetTester tester) async {
  SharedPreferences.setMockInitialValues({});
  await tester.binding.setSurfaceSize(const Size(2000, 1200));
  addTearDown(() => tester.binding.setSurfaceSize(null));
  final repo = _Repo();
  final users = _Users()..repo = repo;
  final c = ProviderContainer(overrides: [
    authRepositoryProvider.overrideWithValue(repo),
    tokenStorageProvider.overrideWithValue(_MemoryTokenStorage()),
    userManagementDataSourceProvider.overrideWithValue(users),
  ]);
  addTearDown(c.dispose);
  await c.read(authControllerProvider.notifier).login('admin', 'x');
  await tester.pumpWidget(UncontrolledProviderScope(
    container: c,
    child: MaterialApp(
      localizationsDelegates: const [AppLocalizations.delegate, DefaultMaterialLocalizations.delegate, DefaultWidgetsLocalizations.delegate],
      supportedLocales: AppLocalizations.supportedLocales,
      locale: const Locale('en'),
      home: const Scaffold(body: UsersPage()),
    ),
  ));
  await tester.pumpAndSettle();
  return (c, repo, users);
}

Finder _inDialog(Finder f) => find.descendant(of: find.byType(AlertDialog), matching: f);

Future<void> _changeRole(WidgetTester tester, Finder menu, String roleLabel) async {
  await tester.tap(menu);
  await tester.pumpAndSettle();
  await tester.tap(find.text(roleLabel).last);
  await tester.pumpAndSettle();
  await tester.tap(_inDialog(find.text('Confirm')));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('editing_self_refreshes_me', (tester) async {
    final (c, repo, users) = await _pump(tester);
    repo.me = _demoted;

    await _changeRole(tester, find.text('Change role').first, 'T — Flexible');

    final (id, changes) = users.updates.single;
    expect(id, 1);
    expect(changes, {'role': 'T'});
    expect(repo.currentUserCalls, 1);
    final me = c.read(authControllerProvider).user!;
    expect(me.role, UserRole.t);
    expect(me.isAdmin, isFalse, reason: 'the admin UI must drop after a self-demotion');
    await tester.pump(const Duration(seconds: 10));
  });

  testWidgets('editing someone else does not re-read /users/me', (tester) async {
    final (c, repo, users) = await _pump(tester);

    await _changeRole(tester, find.text('Change role').last, 'A — Fixed');

    final (id, changes) = users.updates.single;
    expect(id, 2);
    expect(changes, {'role': 'A'});
    expect(repo.currentUserCalls, 0);
    expect(c.read(authControllerProvider).user!.isAdmin, isTrue);
    await tester.pump(const Duration(seconds: 10));
  });

  testWidgets('disabling yourself ends the session', (tester) async {
    final (c, repo, _) = await _pump(tester);
    repo.meError = _forbidden();

    await tester.tap(find.text('Disable').first);
    await tester.pumpAndSettle();
    await tester.tap(_inDialog(find.text('Confirm')));
    await tester.pumpAndSettle();

    expect(repo.currentUserCalls, 1);
    final state = c.read(authControllerProvider);
    expect(state.user, isNull);
    expect(state.error, 'account_inactive');
    await tester.pump(const Duration(seconds: 10));
  });

  testWidgets('deleting yourself logs out without a "session expired" banner', (tester) async {
    final (c, repo, users) = await _pump(tester);

    await tester.tap(find.text('Delete').first);
    await tester.pumpAndSettle();
    await tester.tap(_inDialog(find.text('Delete')));
    await tester.pumpAndSettle();

    expect(users.deleted, [1]);
    final state = c.read(authControllerProvider);
    expect(state.user, isNull, reason: 'the deleted admin is signed out');
    expect(state.error, isNull, reason: 'a deliberate self-delete is no expired session');
    expect(users.listsAfterDelete, 0, reason: 'no request with the dead token');
    expect(repo.currentUserCalls, 0);
    await tester.pump(const Duration(seconds: 10));
  });

  testWidgets('deleting someone else keeps the session and reloads the list', (tester) async {
    final (c, _, users) = await _pump(tester);

    await tester.tap(find.text('Delete').last);
    await tester.pumpAndSettle();
    await tester.tap(_inDialog(find.text('Delete')));
    await tester.pumpAndSettle();

    expect(users.deleted, [2]);
    expect(users.listsAfterDelete, 1);
    expect(c.read(authControllerProvider).user, isNotNull);
    await tester.pump(const Duration(seconds: 10));
  });
}
