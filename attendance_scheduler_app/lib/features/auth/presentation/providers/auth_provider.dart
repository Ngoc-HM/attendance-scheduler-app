import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/api_client.dart';
import '../../../../core/storage/token_storage.dart';
import '../../../../i18n/locale_provider.dart';
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
  }) : super(const AuthState());

  final AuthRepository _repository;
  final LocaleController _localeController;

  /// Where a previous session's token lives. Null → [restoreSession] has
  /// nothing to look at and is a no-op.
  final TokenStorage? _tokenStorage;

  /// App start: sign back in with the stored token instead of forcing a new
  /// login every launch. No token → stay signed out. A token the backend no
  /// longer accepts (expired, user disabled, server unreachable) is dropped
  /// so the login page shows, without a "session expired" banner — nobody
  /// was signed in yet.
  Future<void> restoreSession() async {
    final token = await _tokenStorage?.read();
    if (token == null || token.isEmpty) return;
    try {
      final user = await _repository.currentUser();
      await _localeController.activateUser(user.id);
      state = AuthState(user: user);
    } catch (_) {
      await _repository.logout();
      state = const AuthState();
    }
  }

  Future<bool> login(String username, String password) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final user = await _repository.login(username, password);
      await _localeController.activateUser(user.id);
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

  Future<void> logout() async {
    await _repository.logout();
    _localeController.resetForLogin();
    state = const AuthState();
  }

  /// The backend stopped accepting the bearer token (401 outside login).
  /// Same teardown as [logout], but the login page gets told why — the router
  /// lands there on its own once `user` becomes null. A no-op beyond clearing
  /// the stale token when nobody is signed in (e.g. several requests failing
  /// at once, only the first one ends the session).
  Future<void> sessionExpired() async {
    final wasAuthenticated = state.user != null;
    await _repository.logout();
    if (!wasAuthenticated) return;
    _localeController.resetForLogin();
    state = const AuthState(error: 'session_expired');
  }
}

final authControllerProvider = StateNotifierProvider<AuthController, AuthState>(
  (ref) {
    final controller = AuthController(
      ref.watch(authRepositoryProvider),
      ref.read(localeControllerProvider.notifier),
      tokenStorage: ref.watch(tokenStorageProvider),
    );
    // Dio bumps this counter on 401; reacting here (instead of Dio calling the
    // controller) keeps the provider graph acyclic: auth → dio → signal.
    ref.listen<int>(
      sessionExpiredSignalProvider,
      (_, _) => controller.sessionExpired(),
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
