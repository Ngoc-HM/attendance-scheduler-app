import '../entities/user.dart';

/// Auth contract (implemented in the data layer).
abstract interface class AuthRepository {
  /// Logs in (F-02) and returns the authenticated user.
  Future<User> login(String username, String password);

  /// Fetches the current user from the stored token.
  Future<User> currentUser();

  /// Clears the stored token.
  Future<void> logout();
}
