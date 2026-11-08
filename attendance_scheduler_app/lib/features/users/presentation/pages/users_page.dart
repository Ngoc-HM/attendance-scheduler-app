import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/api_exception.dart';
import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../../auth/domain/entities/user.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../providers/users_provider.dart';
import '../widgets/create_user_dialog.dart';
import '../widgets/edit_quota_dialog.dart';

class UsersPage extends ConsumerWidget {
  const UsersPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final usersAsync = ref.watch(usersControllerProvider);
    final controller = ref.read(usersControllerProvider.notifier);
    final users = usersAsync.asData?.value ?? const [];
    final currentUser = ref.watch(authControllerProvider).user;

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
        builder: (_) => CreateUserDialog(),
      ),
      onApprove: (id) => _confirmApprove(
        context,
        controller,
        users.firstWhere((user) => user.id == id),
      ),
      onDisable: (id) =>
          _confirmSelfOrAdmin(context, controller, currentUser?.id, id, (ctrl) {
        return ctrl.setStatus(id, 'disabled');
      }, warningKey: 'selfActionWarning'),
      onEnable: (id) =>
          _confirmSelfOrAdmin(context, controller, currentUser?.id, id, (ctrl) {
        return ctrl.setStatus(id, 'active');
      }, warningKey: 'selfActionWarning'),
      onChangeRole: (id, role) => _confirmChangeRole(
        context,
        controller,
        currentUser?.id,
        id,
        role,
      ),
      onDelete: (id) => _confirmDelete(context, controller, currentUser?.id, id),
      onEditQuota: (id) => _editQuota(
        context,
        controller,
        users.firstWhere((user) => user.id == id),
      ),
    );
  }

  /// Sets one person's annual leave quota (D4). Migrated accounts all start
  /// at the default, so this is how the admin applies each person's figure.
  Future<void> _editQuota(
    BuildContext context,
    UsersController controller,
    User user,
  ) async {
    final l = AppLocalizations.of(context);
    final quota = await showDialog<int>(
      context: context,
      builder: (_) => EditQuotaDialog(
        username: user.username,
        quota: user.annualLeaveQuota,
      ),
    );
    if (quota == null || !context.mounted) return;
    await _runMutation(
      context,
      controller.setAnnualLeaveQuota(user.id, quota),
      onWarnings: _showWarnings,
      onSuccess: () => DsFeedback.show(
        context,
        l.text('annualLeaveQuotaUpdated'),
        tone: DsTone.success,
      ),
    );
  }

  /// Approval assigns the role (F-03): self-registration cannot pick one, so
  /// the admin chooses it here, starting from the account's current role —
  /// except admin (M), which is never preselected: such an account starts on
  /// T, and granting admin rights takes an explicit pick. The backend
  /// reassigns the code if the role changes. Errors (e.g. last-admin lockout)
  /// are shown like any other mutation.
  Future<void> _confirmApprove(
    BuildContext context,
    UsersController controller,
    User user,
  ) async {
    final l = AppLocalizations.of(context);
    var selected = user.role == UserRole.m ? UserRole.t : user.role;
    final role = await showDialog<UserRole>(
      context: context,
      builder: (dialogContext) => DsFormDialog(
        title: '${l.approve}: ${user.username}',
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(l.text('approveRoleMessage')),
            const SizedBox(height: DsSpacing.x4),
            DsSelectField<UserRole>(
              label: l.role,
              value: selected,
              items: [
                for (final option in UserRole.values)
                  DropdownMenuItem(
                    value: option,
                    child: Text(l.roleLabel(option.apiValue)),
                  ),
              ],
              // The field shows the pick itself; only remember it here.
              onChanged: (picked) {
                if (picked != null) selected = picked;
              },
            ),
          ],
        ),
        actions: [
          DsTextAction(
            label: l.cancel,
            onPressed: () => Navigator.of(dialogContext).pop(),
          ),
          DsPrimaryButton(
            label: l.approve,
            onPressed: () => Navigator.of(dialogContext).pop(selected),
          ),
        ],
      ),
    );
    if (role == null || !context.mounted) return;
    await _runMutation(context, controller.approve(user.id, role));
  }

  /// Confirm before changing a role: the backend reassigns the account code to
  /// match the new role (e.g. T2 → M3), so we warn the admin first.
  /// If the admin is changing their own role, show a stronger self-action
  /// warning (TC-006). Hard errors (last admin lockout) propagate up so the
  /// caller can show the backend message verbatim.
  Future<void> _confirmChangeRole(
    BuildContext context,
    UsersController controller,
    int? currentUserId,
    int targetId,
    String role,
  ) async {
    final l = AppLocalizations.of(context);
    final isSelf = currentUserId == targetId;
    final ok = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => DsFormDialog(
        title: '${l.text('changeRole')} → ${l.roleLabel(role)}',
        content: Text(
          isSelf
              ? l.text('lastAdminDialogMessage')
              : l.text('changeRoleMessage'),
        ),
        actions: [
          DsTextAction(
            label: l.cancel,
            onPressed: () => Navigator.of(dialogContext).pop(false),
          ),
          DsPrimaryButton(
            label: l.text('confirm'),
            onPressed: () => Navigator.of(dialogContext).pop(true),
          ),
        ],
      ),
    );
    if (!(ok ?? false) || !context.mounted) return;
    await _runMutation(
      context,
      controller.setRole(targetId, UserRoleX.fromApi(role)),
      onWarnings: _showWarnings,
    );
  }

  Future<void> _confirmSelfOrAdmin(
    BuildContext context,
    UsersController controller,
    int? currentUserId,
    int targetId,
    Future<List<String>> Function(UsersController ctrl) action, {
    required String warningKey,
  }) async {
    final l = AppLocalizations.of(context);
    final isSelf = currentUserId == targetId;
    if (isSelf) {
      final ok = await showDialog<bool>(
        context: context,
        builder: (dialogContext) => DsFormDialog(
          title: l.text('lastAdminWarning'),
          content: Text(l.text(warningKey)),
          actions: [
            DsTextAction(
              label: l.cancel,
              onPressed: () => Navigator.of(dialogContext).pop(false),
            ),
            DsPrimaryButton(
              label: l.text('confirm'),
              onPressed: () => Navigator.of(dialogContext).pop(true),
            ),
          ],
        ),
      );
      if (!(ok ?? false)) return;
    }
    if (!context.mounted) return;
    await _runMutation(context, action(controller), onWarnings: _showWarnings);
  }

  Future<void> _confirmDelete(
    BuildContext context,
    UsersController controller,
    int? currentUserId,
    int targetId,
  ) async {
    final l = AppLocalizations.of(context);
    final isSelf = currentUserId == targetId;
    final ok = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => DsFormDialog(
        title: l.text('confirmDeleteUser'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(l.text('deleteUserWarning')),
            if (isSelf) ...[
              const SizedBox(height: DsSpacing.x2),
              Text(l.text('lastAdminWarning')),
            ],
          ],
        ),
        actions: [
          DsTextAction(
            label: l.cancel,
            onPressed: () => Navigator.of(dialogContext).pop(false),
          ),
          DsPrimaryButton(
            label: l.text('delete'),
            onPressed: () => Navigator.of(dialogContext).pop(true),
          ),
        ],
      ),
    );
    if (!(ok ?? false) || !context.mounted) return;
    await _runMutation(
      context,
      controller.delete(targetId),
      onSuccess: () => DsFeedback.show(context, l.text('userDeleted'), tone: DsTone.success),
    );
  }

  /// Runs a mutation, shows warnings if any, and surfaces backend errors
  /// (e.g. last-admin lockout → 409). Returns silently on success. Nothing is
  /// shown once [context] is gone (page left while the request was in flight).
  Future<void> _runMutation(
    BuildContext context,
    Future<dynamic> future, {
    void Function(BuildContext, List<String> warnings)? onWarnings,
    VoidCallback? onSuccess,
  }) async {
    final l = AppLocalizations.of(context);
    try {
      final result = await future;
      if (!context.mounted) return;
      final warnings = result is List<String> ? result : <String>[];
      if (warnings.isNotEmpty && onWarnings != null) {
        onWarnings(context, warnings);
      }
      onSuccess?.call();
    } on ApiException catch (e) {
      if (!context.mounted) return;
      final message = _mapGuardMessage(l, e);
      DsFeedback.show(context, message, tone: DsTone.danger);
    } catch (_) {
      if (!context.mounted) return;
      DsFeedback.show(context, l.loadFailed, tone: DsTone.danger);
    }
  }

  void _showWarnings(BuildContext context, List<String> warnings) {
    for (final w in warnings) {
      DsFeedback.show(context, w, tone: DsTone.warning);
    }
  }

  String _mapGuardMessage(AppLocalizations l, ApiException e) {
    if (e.message == 'You cannot remove or disable the last remaining admin.' ||
        e.message ==
            'Không thể hạ quyền hoặc vô hiệu hoá admin cuối cùng.') {
      return l.text('lastAdminWarning');
    }
    return e.message;
  }
}
