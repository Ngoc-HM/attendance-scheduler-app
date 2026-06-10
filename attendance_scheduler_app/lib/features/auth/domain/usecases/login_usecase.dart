import '../entities/user.dart';
import '../repositories/auth_repository.dart';

/// F-02 — log a user in. Thin use case kept for testability and to model the
/// clean-architecture flow other features should follow.
class LoginUseCase {
  const LoginUseCase(this._repository);

  final AuthRepository _repository;

  Future<User> call(String username, String password) =>
      _repository.login(username, password);
}
