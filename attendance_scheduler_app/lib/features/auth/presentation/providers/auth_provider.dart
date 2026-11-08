import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/api_client.dart';
import '../../../../core/storage/token_storage.dart';
import '../../../../i18n/locale_provider.dart';
import '../../../attendance/presentation/providers/attendance_provider.dart';
import '../../../attendance/presentation/providers/time_clock_provider.dart';
import '../../../flights/presentation/providers/flights_provider.dart';
import '../../../leaves/presentation/providers/leaves_provider.dart';
import '../../../reports/presentation/providers/reports_provider.dart';
import '../../../schedule/presentation/providers/schedule_provider.dart';
import '../../../schedule/presentation/providers/self_arrange_provider.dart';
import '../../../schedule/presentation/providers/shift_change_provider.dart';
import '../../../users/presentation/providers/users_provider.dart';
import '../../data/repositories/auth_repository_impl.dart';
import '../../domain/entities/user.dart';
import '../../domain/repositories/auth_repository.dart';

/// Immutable auth UI state.
class AuthState {
  const AuthState({this.user, this.isLoading = false, this.error});

  final User? user;
  final bool isLoading;
  final String? error;

  bool get isAuthenticated => user != null;

  AuthState copyWith({
    User? user,
    bool? isLoading,
    String? error,
    bool clearError = false,
  }) {
    return AuthState(
      user: user ?? this.user,
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
    );
  }
}

class AuthController extends StateNotifier<AuthState> {
  AuthController(
    this._repository,
    this._localeController, {
    this._tokenStorage,
    this._onSessionReset,
  }) : super(const AuthState());

  final AuthRepository _repository;
  final LocaleController _localeController;

  /// Where a previous session's token lives. Null → [restoreSession] has
  /// nothing to look at and is a no-op.
  final TokenStorage? _tokenStorage;

  /// Drops every provider that cached the previous person's data (see
  /// [resetUserScopedProviders]). Called whenever the signed-in person or
  /// their role changes, so a shared desktop never shows one employee what
  /// the previous one loaded.
  final void Function()? _onSessionReset;

  /// A 403 check of `GET /users/me` is in flight ([checkAccountStillActive]).
  bool _checkingAccount = false;

  /// App start: sign back in with the stored token instead of forcing a new
  /// login every launch. No token → stay signed out.
  ///
  /// Only a token the backend refused (401/403: expired, user disabled) is
  /// dropped, without a "session expired" banner — nobody was signed in yet.
  /// If the server could not be reached or failed, the token is kept for the
  /// next start and the login page says why.
  Future<void> restoreSession() async {
    final token = await _tokenStorage?.read();
    if (token == null || token.isEmpty) return;
    try {
      final user = await _repository.currentUser();
      await _localeController.activateUser(user.id);
      state = AuthState(user: user);
    } on DioException catch (e) {
      final status = e.response?.statusCode;
      if (status == 401 || status == 403) {
        await _repository.logout();
        state = const AuthState();
      } else {
        state = AuthState(error: _messageFor(e));
      }
    } catch (_) {
      state = const AuthState(error: 'unknown_failure');
    }
  }

  Future<bool> login(String username, String password) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final user = await _repository.login(username, password);
      await _localeController.activateUser(user.id);
      // Anything a provider rebuilt while nobody was signed in (a page still
      // open during logout) is dropped before the new person sees it.
      _onSessionReset?.call();
      state = AuthState(user: user);
      return true;
    } on DioException catch (e) {
      state = AuthState(error: _messageFor(e));
      return false;
    } catch (_) {
      state = const AuthState(error: 'unknown_failure');
      return false;
    }
  }

  /// Distinguish "wrong credentials" from "can't reach the server" so the user
  /// can tell a 401 apart from a backend/network problem.
  String _messageFor(DioException e) {
    if (e.response?.statusCode == 401) {
      return 'incorrect_credentials';
    }
    if (e.response == null) {
      return 'server_unavailable';
    }
    return 'http_failure';
  }

  Future<void> logout() => _endSession(null);

  /// The backend stopped accepting the bearer token (401 outside login).
  /// Same teardown as [logout], but the login page gets told why — the router
  /// lands there on its own once `user` becomes null. A no-op beyond clearing
  /// the stale token when nobody is signed in (e.g. several requests failing
  /// at once, only the first one ends the session).
  Future<void> sessionExpired() async {
    if (state.user == null) {
      await _repository.logout();
      return;
    }
    await _endSession('session_expired');
  }

  /// Some request came back 403. That is either a plain permission refusal
  /// or an account an admin disabled mid-session; the backend's `detail` is
  /// translated text, so instead of matching it, re-read `GET /users/me`:
  /// a 403 there too means the account is inactive and the session ends.
  /// Several 403s at once trigger a single check.
  Future<void> checkAccountStillActive() async {
    if (state.user == null || _checkingAccount) return;
    _checkingAccount = true;
    try {
      await refreshCurrentUser();
    } finally {
      _checkingAccount = false;
    }
  }

  /// Re-reads `GET /users/me` and updates the signed-in user — e.g. after an
  /// admin edited their own account, so a self-demotion drops the admin UI
  /// at once. A 403 ends the session as inactive; a 401 is already handled
  /// by the session-expired signal; other failures leave the session as is.
  Future<void> refreshCurrentUser() async {
    final before = state.user;
    if (before == null) return;
    try {
      final fresh = await _repository.currentUser();
      final now = state.user;
      if (now == null || now.id != before.id) return; // signed out meanwhile
      // Nothing changed (the usual case after a plain permission 403): keep
      // the current state object so HomeShell and the router do not rebuild.
      if (fresh == now && !state.isLoading && state.error == null) return;
      if (fresh.role != now.role) _onSessionReset?.call();
      state = AuthState(user: fresh);
    } on DioException catch (e) {
      if (e.response?.statusCode == 403 && state.user?.id == before.id) {
        await _endSession('account_inactive');
      }
    } catch (_) {
      // Unreadable profile: keep the session, the next request will tell.
    }
  }

  /// Common teardown: drop the token, the user's language, the session and
  /// every provider holding the previous person's data. [error] is the
  /// reason shown on the login page (null for a deliberate logout).
  Future<void> _endSession(String? error) async {
    await _repository.logout();
    _localeController.resetForLogin();
    state = AuthState(error: error);
    _onSessionReset?.call();
  }
}

/// Invalidates every provider that caches data loaded for the signed-in
/// person (their leaves, attendance, clock, schedule, requests, and the
/// admin-only lists). Called on logout, session expiry, an inactive account,
/// a role change of the signed-in user and before a new login, so the next
/// person on a shared desktop starts from a fresh fetch.
///
/// Goes through the container on purpose: `Ref.invalidate` first *creates*
/// a provider nobody has read yet (a debug-mode dependency check), which
/// would start a fetch just to throw it away.
void resetUserScopedProviders(Ref ref) {
  ref.container
    ..invalidate(leavesControllerProvider)
    ..invalidate(attendanceControllerProvider)
    ..invalidate(timeClockControllerProvider)
    ..invalidate(selfArrangeControllerProvider)
    ..invalidate(selfArrangeAdminControllerProvider)
    ..invalidate(scheduleControllerProvider)
    ..invalidate(shiftChangeControllerProvider)
    ..invalidate(reportsControllerProvider)
    ..invalidate(flightsControllerProvider)
    ..invalidate(usersControllerProvider);
}

final authControllerProvider = StateNotifierProvider<AuthController, AuthState>(
  (ref) {
    final controller = AuthController(
      ref.watch(authRepositoryProvider),
      ref.read(localeControllerProvider.notifier),
      tokenStorage: ref.watch(tokenStorageProvider),
      onSessionReset: () => resetUserScopedProviders(ref),
    );
    // Dio bumps these counters on 401 / 403; reacting here (instead of Dio
    // calling the controller) keeps the provider graph acyclic:
    // auth → dio → signal.
    ref.listen<int>(
      sessionExpiredSignalProvider,
      (_, _) => controller.sessionExpired(),
    );
    ref.listen<int>(
      forbiddenSignalProvider,
      (_, _) => controller.checkAccountStillActive(),
    );
    return controller;
  },
);

/// Runs [AuthController.restoreSession] once per app start. The app shows a
/// splash until it completes, so a returning user never flashes the login
/// page before the router sends them on.
final sessionRestoreProvider = FutureProvider<void>(
  (ref) => ref.read(authControllerProvider.notifier).restoreSession(),
);
