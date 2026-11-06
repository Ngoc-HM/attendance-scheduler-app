import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/router/app_router.dart';
import 'design_system/design_system.dart';
import 'features/auth/presentation/providers/auth_provider.dart';
import 'i18n/app_localizations.dart';
import 'i18n/locale_provider.dart';

/// Root widget. Wires routing, theming and localization.
class AttendanceSchedulerApp extends ConsumerWidget {
  const AttendanceSchedulerApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Session restore runs before the router exists: a returning user lands
    // on their pages instead of flashing the login screen first.
    if (ref.watch(sessionRestoreProvider).isLoading) {
      return MaterialApp(
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light,
        home: const Scaffold(
          body: Center(child: CircularProgressIndicator()),
        ),
      );
    }
    final router = ref.watch(appRouterProvider);
    final locale = ref.watch(localeControllerProvider);

    return MaterialApp.router(
      onGenerateTitle: (context) => AppLocalizations.of(context).appTitle,
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      themeMode: ThemeMode.light,
      locale: locale,
      routerConfig: router,
      // English primary, Vietnamese optional (spec §2).
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
    );
  }
}
