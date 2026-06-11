import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../../auth/domain/entities/user.dart';
import '../providers/users_provider.dart';

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
  UserRole _role = UserRole.t;
  bool _isLoading = false;
  String? _error;

  @override
  void dispose() {
    _username.dispose();
    _fullName.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      await ref
          .read(usersControllerProvider.notifier)
          .create(
            username: _username.text.trim(),
            fullName: _fullName.text.trim(),
            password: _password.text,
            role: _role,
          );
      if (mounted) Navigator.of(context).pop(true);
    } catch (_) {
      setState(() => _error = AppLocalizations.of(context).createUserFailed);
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
          DsSelectOption(value: role, label: role.label),
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
      error: _error,
      loading: _isLoading,
    );
  }
}
