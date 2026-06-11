import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // Load runtime config (API base URL). Optional: falls back to the
  // --dart-define value / default if the file is absent.
  await dotenv.load(fileName: '.env', isOptional: true);
  // Riverpod root. Desktop window sizing/init (window_manager) can be added here.
  runApp(const ProviderScope(child: AttendanceSchedulerApp()));
}
