import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

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
  AuthController(this._repository) : super(const AuthState());

  final AuthRepository _repository;

  Future<bool> login(String username, String password) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final user = await _repository.login(username, password);
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
    state = const AuthState();
  }
}

final authControllerProvider = StateNotifierProvider<AuthController, AuthState>(
  (ref) => AuthController(ref.watch(authRepositoryProvider)),
);
