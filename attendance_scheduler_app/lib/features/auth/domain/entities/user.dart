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
