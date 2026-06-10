import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/router/app_router.dart';
import 'core/theme/app_theme.dart';

/// Root widget. Wires routing, theming and localization.
class AttendanceSchedulerApp extends ConsumerWidget {
  const AttendanceSchedulerApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(appRouterProvider);

    return MaterialApp.router(
      title: 'Attendance & Scheduler',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      routerConfig: router,
      // English primary, Vietnamese optional (spec §2).
      supportedLocales: const [Locale('en'), Locale('vi')],
      localizationsDelegates: const [
        // After `flutter gen-l10n`, also add: AppLocalizations.delegate
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
    );
  }
}
