import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/api_exception.dart';
import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../../auth/domain/entities/user.dart';
import '../providers/users_provider.dart';
import '../user_error_message.dart';

class CreateUserDialog extends ConsumerStatefulWidget {
  const CreateUserDialog({super.key});

  @override
  ConsumerState<CreateUserDialog> createState() => _CreateUserDialogState();
}

class _CreateUserDialogState extends ConsumerState<CreateUserDialog> {
  final _formKey = GlobalKey<FormState>();
  final _username = TextEditingController();
  final _fullName = TextEditingController();
  final _password = TextEditingController();
  final _quota = TextEditingController();
  UserRole _role = UserRole.t;
  bool _isLoading = false;
  String? _error;

  @override
  void dispose() {
    _username.dispose();
    _fullName.dispose();
    _password.dispose();
    _quota.dispose();
    super.dispose();
    _password.removeListener(_rebuild);
    _username.removeListener(_rebuild);
  }

  @override
  void initState() {
    super.initState();
    _password.addListener(_rebuild);
    _username.addListener(_rebuild);
  }

  void _rebuild() {
    if (mounted) setState(() {});
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _isLoading = true;
      _error = null;
    });
    // Validated above: empty (server default) or a whole number 0–365.
    final quota = _quota.text.trim();
    try {
      await ref
          .read(usersControllerProvider.notifier)
          .create(
            username: _username.text.trim(),
            fullName: _fullName.text.trim(),
            password: _password.text,
            role: _role,
            annualLeaveQuota: quota.isEmpty ? null : int.parse(quota),
          );
      if (mounted) Navigator.of(context).pop(true);
    } catch (e) {
      // A 4xx carries the backend's reason (username taken, quota out of
      // range, ...); anything else is the generic create failure.
      if (!mounted) return;
      final l = AppLocalizations.of(context);
      final status = e is ApiException ? e.statusCode : null;
      setState(
        () => _error = status != null && status < 500
            ? userErrorMessage(l, e)
            : l.createUserFailed,
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return DsCreateUserDialog<UserRole>(
      formKey: _formKey,
      usernameController: _username,
      fullNameController: _fullName,
      passwordController: _password,
      role: _role,
      roleOptions: [
        for (final role in UserRole.values)
          DsSelectOption(value: role, label: l.roleLabel(role.apiValue)),
      ],
      onRoleChanged: (role) => setState(() => _role = role),
      onCancel: () => Navigator.of(context).pop(false),
      onSubmit: _submit,
      usernameLabel: l.username,
      fullNameLabel: l.fullName,
      passwordLabel: l.password,
      roleLabel: l.role,
      cancelLabel: l.cancel,
      submitLabel: l.create,
      minThreeMessage: l.minThreeChars,
      requiredMessage: l.fieldRequired,
      minSixMessage: l.minSixChars,
      quotaController: _quota,
      quotaLabel: l.text('annualLeaveQuota'),
      quotaHint: l.text('annualLeaveQuotaHint'),
      quotaInvalidMessage: l.text('annualLeaveQuotaInvalid'),
      error: _error,
      loading: _isLoading,
    );
  }
}
