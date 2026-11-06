import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/api_client.dart';
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
  AuthController(this._repository, this._localeController)
    : super(const AuthState());

  final AuthRepository _repository;
  final LocaleController _localeController;

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
