import 'package:flutter/material.dart';

import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../../auth/domain/entities/user.dart';

/// Approving a sign-up assigns the role (F-03): self-registration cannot
/// pick one, so the admin chooses it here, starting from the account's
/// current role — except admin (M), which is never preselected: such an
/// account starts on T, and granting admin rights takes an explicit pick.
/// The backend reassigns the code if the role changes. Null = cancelled.
///
/// Opened from the admin's request table (owner 2026-11-20: everything the
/// admin approves lives on one screen).
Future<UserRole?> showApproveAccountDialog(BuildContext context, User user) {
  final l = AppLocalizations.of(context);
  var selected = user.role == UserRole.m ? UserRole.t : user.role;
  return showDialog<UserRole>(
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
}

/// Confirms deleting an account (hard delete with cascade). Rejecting a
/// sign-up is this same delete; [isSelf] adds the last-admin warning.
Future<bool> confirmDeleteAccount(
  BuildContext context, {
  bool isSelf = false,
}) async {
  final l = AppLocalizations.of(context);
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
  return ok ?? false;
}
