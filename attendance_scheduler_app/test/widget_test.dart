// Smoke test: the app boots and lands on the login screen.

import 'package:attendance_scheduler_app/app.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('App boots to the login screen', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(child: AttendanceSchedulerApp()),
    );
    await tester.pumpAndSettle();

    expect(find.text('Log in'), findsOneWidget);
    expect(find.text('Username'), findsOneWidget);
  });
}
