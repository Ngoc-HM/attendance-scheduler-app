import 'package:attendance_scheduler_app/core/storage/locale_storage.dart';
import 'package:attendance_scheduler_app/i18n/locale_provider.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

class _MemoryLocaleStorage extends LocaleStorage {
  final Map<int, String> values = {};

  @override
  Future<String?> read(int userId) async => values[userId];

  @override
  Future<void> write(int userId, String languageCode) async {
    values[userId] = languageCode;
  }
}

void main() {
  test('preference survives new controller and storage instances', () async {
    SharedPreferences.setMockInitialValues({});
    final firstSession = LocaleController(LocaleStorage());
    await firstSession.activateUser(10);
    await firstSession.setLanguage('vi');

    final laterSession = LocaleController(LocaleStorage());
    await laterSession.activateUser(10);

    expect(laterSession.state.languageCode, 'vi');
  });

  test(
    'first login defaults to English and persists it for that user',
    () async {
      final storage = _MemoryLocaleStorage();
      final controller = LocaleController(storage);

      await controller.activateUser(1);

      expect(controller.state.languageCode, 'en');
      expect(storage.values[1], 'en');
    },
  );

  test(
    'a user gets their previously selected language on later logins',
    () async {
      final storage = _MemoryLocaleStorage();
      final firstSession = LocaleController(storage);
      await firstSession.activateUser(1);
      await firstSession.setLanguage('vi');
      firstSession.resetForLogin();

      expect(firstSession.state.languageCode, 'en');

      final laterSession = LocaleController(storage);
      await laterSession.activateUser(1);

      expect(laterSession.state.languageCode, 'vi');
      await laterSession.activateUser(2);
      expect(laterSession.state.languageCode, 'en');
    },
  );

  test('an explicit login-screen choice becomes the user preference', () async {
    final storage = _MemoryLocaleStorage();
    final controller = LocaleController(storage);

    await controller.setLanguage('vi');
    await controller.activateUser(3);

    expect(controller.state.languageCode, 'vi');
    expect(storage.values[3], 'vi');
  });
}
