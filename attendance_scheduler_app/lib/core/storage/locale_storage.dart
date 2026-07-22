import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

final localeStorageProvider = Provider<LocaleStorage>((ref) => LocaleStorage());

/// Stores one preferred UI language per user on this device.
///
/// Language preferences deliberately survive logout; only the access token is
/// cleared. This is non-sensitive UI state, so platform preferences are more
/// reliable than Keychain/Credential Manager for unsigned development builds.
class LocaleStorage {
  final Map<int, String> _memory = {};

  String _key(int userId) => 'preferred_language_user_$userId';

  Future<String?> read(int userId) async {
    if (_memory.containsKey(userId)) return _memory[userId];
    try {
      final preferences = await SharedPreferences.getInstance();
      final value = preferences.getString(_key(userId));
      if (value == 'en' || value == 'vi') _memory[userId] = value!;
      return value == 'en' || value == 'vi' ? value : null;
    } catch (_) {
      return _memory[userId];
    }
  }

  Future<void> write(int userId, String languageCode) async {
    if (languageCode != 'en' && languageCode != 'vi') return;
    _memory[userId] = languageCode;
    try {
      final preferences = await SharedPreferences.getInstance();
      await preferences.setString(_key(userId), languageCode);
    } catch (_) {
      // Platform preferences unavailable; the current session still works.
    }
  }
}
