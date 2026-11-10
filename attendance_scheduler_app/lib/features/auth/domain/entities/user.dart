import 'package:equatable/equatable.dart';

/// Personnel roles (spec §3 + owner 2026-07-09): M = admin+flexible,
/// T = flexible, A = fixed, F = split from T (T-like, only weekly-off rule).
/// The per-person unique identifier (e.g. "A3") is the separate [User.code] field.
enum UserRole { m, t, a, f }

extension UserRoleX on UserRole {
  bool get isAdmin => this == UserRole.m;
  bool get isFixed => this == UserRole.a;

  /// Backend enum value: `UserRole.m` → `'M'`, `UserRole.t` → `'T'`, ...
  String get apiValue => name.toUpperCase();

  /// Parse a backend role letter (`'M'`/`'T'`/`'A'`/`'F'`) back into a
  /// [UserRole]; anything unrecognised falls back to the flexible `T` role.
  static UserRole fromApi(String value) => switch (value.toUpperCase()) {
    'M' => UserRole.m,
    'A' => UserRole.a,
    'F' => UserRole.f,
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
    this.carryComp = 0,
    this.annualLeaveQuota = 0,
  });

  final int id;
  final String username;
  final String fullName;
  final UserRole role;
  final String status;

  /// Confidential per-person identifier auto-assigned by the server (e.g. "A3", "T1").
  final String code;

  /// Comp days (CD) carried into the current month, as stored by the last
  /// month close (`carry_comp` on `/users/me` and `/users`).
  final int carryComp;

  /// Admin-set days of leave per calendar year (`annual_leave_quota`, D4).
  final int annualLeaveQuota;

  bool get isAdmin => role.isAdmin;

  @override
  List<Object?> get props =>
      [id, username, fullName, role, status, code, carryComp, annualLeaveQuota];
}
