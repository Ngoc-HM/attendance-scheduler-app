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

  String? last;

  @override
  Future<String?> readLast() async => last;

  @override
  Future<void> writeLast(String languageCode) async {
    last = languageCode;
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

      final laterSession = LocaleController(storage);
      await laterSession.activateUser(1);

      expect(laterSession.state.languageCode, 'vi');
    },
  );

  // Owner 2026-11-10: the login screen showed English while the person's app
  // was Vietnamese. The device now keeps the language it last showed.
  test('logout keeps the language on the login screen', () async {
    final storage = _MemoryLocaleStorage();
    final controller = LocaleController(storage);
    await controller.activateUser(1);
    await controller.setLanguage('vi');

    controller.resetForLogin();

    expect(controller.state.languageCode, 'vi');
  });

  test('the next start opens in the language last shown', () async {
    final storage = _MemoryLocaleStorage();
    final firstRun = LocaleController(storage);
    await firstRun.activateUser(1);
    await firstRun.setLanguage('vi');

    final nextRun = LocaleController(
      storage,
      initialLanguage: (await storage.readLast())!,
    );

    expect(nextRun.state.languageCode, 'vi');
  });

  test('a login-screen choice is remembered without logging in', () async {
    final storage = _MemoryLocaleStorage();
    await LocaleController(storage).setLanguage('vi');

    expect(await storage.readLast(), 'vi');
  });

  test('a person without a preference keeps the language shown', () async {
    final storage = _MemoryLocaleStorage();
    final controller = LocaleController(storage, initialLanguage: 'vi');

    await controller.activateUser(7);

    expect(controller.state.languageCode, 'vi');
    expect(storage.values[7], 'vi');
  });

  test("another person's own preference still wins at login", () async {
    final storage = _MemoryLocaleStorage()..values[2] = 'en';
    final controller = LocaleController(storage, initialLanguage: 'vi');

    await controller.activateUser(2);

    expect(controller.state.languageCode, 'en');
    expect(await storage.readLast(), 'en');
  });

  test('an unknown stored language falls back to English', () {
    final controller = LocaleController(
      _MemoryLocaleStorage(),
      initialLanguage: 'de',
    );

    expect(controller.state.languageCode, 'en');
  });

  test('an explicit login-screen choice becomes the user preference', () async {
    final storage = _MemoryLocaleStorage();
    final controller = LocaleController(storage);

    await controller.setLanguage('vi');
    await controller.activateUser(3);

    expect(controller.state.languageCode, 'vi');
    expect(storage.values[3], 'vi');
  });
}
