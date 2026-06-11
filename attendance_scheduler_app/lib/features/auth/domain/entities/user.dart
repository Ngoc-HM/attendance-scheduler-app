import 'package:equatable/equatable.dart';

/// Personnel roles (spec §3).
enum UserRole { m, t, a1, a2, a3, a4 }

extension UserRoleX on UserRole {
  bool get isAdmin => this == UserRole.m;
  bool get isFixed =>
      this == UserRole.a1 ||
      this == UserRole.a2 ||
      this == UserRole.a3 ||
      this == UserRole.a4;

  /// Backend enum value (e.g. `UserRole.a1` → `'A1'`, `UserRole.m` → `'M'`).
  String get apiValue => name.toUpperCase();

  /// Human label for dropdowns / tables.
  String get label => switch (this) {
    UserRole.m => 'M — Admin',
    UserRole.t => 'T — Flexible',
    UserRole.a1 => 'A1 — Fixed',
    UserRole.a2 => 'A2 — Fixed',
    UserRole.a3 => 'A3 — Fixed',
    UserRole.a4 => 'A4 — Fixed',
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
  });

  final int id;
  final String username;
  final String fullName;
  final UserRole role;
  final String status;

  bool get isAdmin => role.isAdmin;

  @override
  List<Object?> get props => [id, username, fullName, role, status];
}
