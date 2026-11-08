import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:window_manager/window_manager.dart';

import 'app.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Desktop: open maximized like the user pressed the maximize button.
  // Not exclusive full-screen — the window chrome and menu bar stay visible
  // and the user can restore / resize / maximize again normally.
  if (Platform.isMacOS || Platform.isWindows || Platform.isLinux) {
    await windowManager.ensureInitialized();
    await windowManager.waitUntilReadyToShow(null, () async {
      await windowManager.setMinimumSize(const Size(1280, 720));
      await windowManager.maximize();
      await windowManager.show();
      await windowManager.focus();
    });
  }

  // Load runtime config (API base URL). Optional; a non-empty
  // --dart-define=API_BASE_URL wins over it (see AppConfig).
  await dotenv.load(fileName: '.env', isOptional: true);
  runApp(const ProviderScope(child: AttendanceSchedulerApp()));
}
