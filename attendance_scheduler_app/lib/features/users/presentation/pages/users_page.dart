import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../design_system/design_system.dart';
import '../../../auth/domain/entities/user.dart';
import '../providers/users_provider.dart';
import '../widgets/create_user_dialog.dart';

class UsersPage extends ConsumerWidget {
  const UsersPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final usersAsync = ref.watch(usersControllerProvider);
    final controller = ref.read(usersControllerProvider.notifier);
    final users = usersAsync.asData?.value ?? const [];

    return DsUsersView(
      users: [
        for (final user in users)
          DsUserRowData(
            id: user.id,
            username: user.username,
            fullName: user.fullName,
            role: user.role.apiValue,
            status: user.status,
          ),
      ],
      loading: usersAsync.isLoading,
      error: usersAsync.hasError ? usersAsync.error.toString() : null,
      onRefresh: controller.load,
      onCreate: () => showDialog<bool>(
        context: context,
        builder: (_) => const CreateUserDialog(),
      ),
      onApprove: controller.approve,
      onDisable: (id) => controller.setStatus(id, 'disabled'),
      onEnable: (id) => controller.setStatus(id, 'active'),
    );
  }
}
