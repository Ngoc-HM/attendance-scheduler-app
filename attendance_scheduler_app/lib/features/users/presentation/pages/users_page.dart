import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../../auth/domain/entities/user.dart';
import '../providers/users_provider.dart';
import '../widgets/create_user_dialog.dart';

class UsersPage extends ConsumerWidget {
  const UsersPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
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
            code: user.code,
          ),
      ],
      loading: usersAsync.isLoading,
      error: usersAsync.hasError ? l.loadFailed : null,
      onRefresh: controller.load,
      onCreate: () => showDialog<bool>(
        context: context,
        builder: (_) => const CreateUserDialog(),
      ),
      onApprove: controller.approve,
      onDisable: (id) => controller.setStatus(id, 'disabled'),
      onEnable: (id) => controller.setStatus(id, 'active'),
      onChangeRole: (id, role) => _confirmChangeRole(context, controller, id, role),
    );
  }

  /// Confirm before changing a role: the backend reassigns the account code to
  /// match the new role (e.g. T2 → M3), so we warn the admin first.
  Future<void> _confirmChangeRole(
    BuildContext context,
    UsersController controller,
    int id,
    String role,
  ) async {
    final l = AppLocalizations.of(context);
    final ok = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text('${l.text('changeRole')} → ${l.roleLabel(role)}'),
        content: Text(l.text('changeRoleMessage')),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: Text(l.cancel),
          ),
          FilledButton(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: Text(l.text('confirm')),
          ),
        ],
      ),
    );
    if (ok ?? false) {
      await controller.setRole(id, UserRoleX.fromApi(role));
    }
  }
}
