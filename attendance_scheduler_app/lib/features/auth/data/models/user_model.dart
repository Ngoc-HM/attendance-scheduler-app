import '../../domain/entities/user.dart';

/// Data-layer model: maps the backend JSON to the [User] entity.
class UserModel extends User {
  const UserModel({
    required super.id,
    required super.username,
    required super.fullName,
    required super.role,
    required super.status,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) => UserModel(
        id: json['id'] as int,
        username: json['username'] as String,
        fullName: json['full_name'] as String? ?? '',
        role: _roleFromApi(json['role'] as String? ?? 'T'),
        status: json['status'] as String? ?? 'pending',
      );

  static UserRole _roleFromApi(String role) => switch (role) {
        'M' => UserRole.m,
        'A1' => UserRole.a1,
        'A2' => UserRole.a2,
        'A3' => UserRole.a3,
        'A4' => UserRole.a4,
        _ => UserRole.t,
      };
}
