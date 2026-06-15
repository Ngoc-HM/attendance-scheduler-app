import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/router/app_router.dart';
import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../../../i18n/locale_provider.dart';
import '../../data/repositories/auth_repository_impl.dart';
import '../../domain/entities/user.dart';

class RegisterPage extends ConsumerStatefulWidget {
  const RegisterPage({super.key});

  @override
  ConsumerState<RegisterPage> createState() => _RegisterPageState();
}

class _RegisterPageState extends ConsumerState<RegisterPage> {
  final _formKey = GlobalKey<FormState>();
  final _username = TextEditingController();
  final _fullName = TextEditingController();
  final _password = TextEditingController();

  static const _selectableRoles = [UserRole.t, UserRole.a];

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
          .read(authRepositoryProvider)
          .register(
            username: _username.text.trim(),
            fullName: _fullName.text.trim(),
            password: _password.text,
            role: _role,
          );
      if (!mounted) return;
      final l = AppLocalizations.of(context);
      DsFeedback.show(context, l.registerPending, tone: DsTone.success);
      context.go(AppRoute.login);
    } catch (_) {
      setState(() => _error = AppLocalizations.of(context).registerFailed);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final locale = ref.watch(localeControllerProvider);
    return DsRegisterView<UserRole>(
      formKey: _formKey,
      usernameController: _username,
      fullNameController: _fullName,
      passwordController: _password,
      role: _role,
      roleOptions: [
        for (final role in _selectableRoles)
          DsSelectOption(value: role, label: l.roleLabel(role.apiValue)),
      ],
      title: l.register,
      subtitle: l.text('registerSubtitle'),
      usernameLabel: l.username,
      fullNameLabel: l.fullName,
      passwordLabel: l.password,
      roleLabel: l.role,
      submitLabel: l.register,
      backLabel: l.backToLogin,
      minThreeMessage: l.minThreeChars,
      requiredMessage: l.fieldRequired,
      minSixMessage: l.minSixChars,
      error: _error,
      loading: _isLoading,
      languageCode: locale.languageCode,
      onLanguageChanged: ref
          .read(localeControllerProvider.notifier)
          .setLanguage,
      onRoleChanged: (role) => setState(() => _role = role),
      onSubmit: _submit,
      onBack: () => context.go(AppRoute.login),
    );
  }
}
