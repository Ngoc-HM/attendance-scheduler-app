import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/router/app_router.dart';
import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../../../i18n/locale_provider.dart';
import '../providers/auth_provider.dart';

class LoginPage extends ConsumerStatefulWidget {
  const LoginPage({super.key});

  @override
  ConsumerState<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends ConsumerState<LoginPage> {
  final _formKey = GlobalKey<FormState>();
  // Pre-filled with the seed-admin defaults (config FIRST_ADMIN_*) so login
  // is one click during development.
  final _username = TextEditingController(text: 'admin');
  final _password = TextEditingController(text: 'admin123');

  @override
  void dispose() {
    _username.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    final ok = await ref
        .read(authControllerProvider.notifier)
        .login(_username.text.trim(), _password.text);
    if (ok && mounted) context.go(AppRoute.schedule);
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final locale = ref.watch(localeControllerProvider);
    final state = ref.watch(authControllerProvider);
    return DsLoginView(
      formKey: _formKey,
      usernameController: _username,
      passwordController: _password,
      title: l.login,
      subtitle: l.text('loginSubtitle'),
      usernameLabel: l.username,
      passwordLabel: l.password,
      loginLabel: l.login,
      registerLabel: l.createAccount,
      requiredMessage: l.fieldRequired,
      error: state.error == null ? null : l.authError(state.error),
      loading: state.isLoading,
      languageCode: locale.languageCode,
      onLanguageChanged: ref
          .read(localeControllerProvider.notifier)
          .setLanguage,
      onLogin: _submit,
      onRegister: () => context.go(AppRoute.register),
    );
  }
}
