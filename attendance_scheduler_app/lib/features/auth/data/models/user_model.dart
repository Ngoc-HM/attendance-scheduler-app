import '../../domain/entities/user.dart';

/// Data-layer model: maps the backend JSON to the [User] entity.
class UserModel extends User {
  const UserModel({
    required super.id,
    required super.username,
    required super.fullName,
    required super.role,
    required super.status,
    required super.code,
    super.carryComp,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) => UserModel(
    id: json['id'] as int,
    username: json['username'] as String,
    fullName: json['full_name'] as String? ?? '',
    // Single source of truth for role parsing — a private duplicate here once
    // missed role F and silently rendered F users as T.
    role: UserRoleX.fromApi(json['role'] as String? ?? 'T'),
    status: json['status'] as String? ?? 'pending',
    code: json['code'] as String? ?? '',
    carryComp: json['carry_comp'] as int? ?? 0,
  );
}
