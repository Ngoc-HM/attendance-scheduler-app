import 'package:equatable/equatable.dart';

/// Personnel roles (spec §3): M = admin+flexible, T = flexible, A = fixed.
/// The per-person unique identifier (e.g. "A3") is the separate [User.code] field.
enum UserRole { m, t, a }

extension UserRoleX on UserRole {
  bool get isAdmin => this == UserRole.m;
  bool get isFixed => this == UserRole.a;

  /// Backend enum value: `UserRole.m` → `'M'`, `UserRole.t` → `'T'`, `UserRole.a` → `'A'`.
  String get apiValue => name.toUpperCase();

  /// Parse a backend role letter (`'M'`/`'T'`/`'A'`) back into a [UserRole];
  /// anything unrecognised falls back to the flexible `T` role.
  static UserRole fromApi(String value) => switch (value.toUpperCase()) {
    'M' => UserRole.m,
    'A' => UserRole.a,
    _ => UserRole.t,
  };
}

/// Domain entity for an authenticated user.
class User extends Equatable {
  const User({
    required this.id,
    required this.username,
    required this.fullName,
    required this.role,
    required this.status,
    required this.code,
  });

  final int id;
  final String username;
  final String fullName;
  final UserRole role;
  final String status;

  /// Confidential per-person identifier auto-assigned by the server (e.g. "A3", "T1").
  final String code;

  bool get isAdmin => role.isAdmin;

  @override
  List<Object?> get props => [id, username, fullName, role, status, code];
}
