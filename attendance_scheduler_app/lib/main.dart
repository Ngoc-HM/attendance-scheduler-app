import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app.dart';

void main() {
  // Riverpod root. Desktop window sizing/init (window_manager) can be added here.
  runApp(const ProviderScope(child: AttendanceSchedulerApp()));
}
