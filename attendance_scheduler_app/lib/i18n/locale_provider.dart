import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/storage/locale_storage.dart';

class LocaleController extends StateNotifier<Locale> {
  LocaleController(this._storage) : super(const Locale('en'));

  final LocaleStorage _storage;
  int? _activeUserId;
  bool _guestChangedLanguage = false;

  /// Bind the locale to the user who has just logged in.
  ///
  /// A stored preference wins normally. If the user explicitly switched the
  /// language on the login screen, that newest choice becomes their preference.
  Future<void> activateUser(int userId) async {
    _activeUserId = userId;
    if (_guestChangedLanguage) {
      await _storage.write(userId, state.languageCode);
    } else {
      final saved = await _storage.read(userId);
      final languageCode = saved ?? 'en';
      state = Locale(languageCode);
      if (saved == null) await _storage.write(userId, languageCode);
    }
    _guestChangedLanguage = false;
  }

  Future<void> setLanguage(String languageCode) async {
    if (languageCode == 'en' || languageCode == 'vi') {
      state = Locale(languageCode);
      final userId = _activeUserId;
      if (userId == null) {
        _guestChangedLanguage = true;
      } else {
        await _storage.write(userId, languageCode);
      }
    }
  }

  /// The unauthenticated screen starts in English. The next successful login
  /// restores the preference belonging to that specific user.
  void resetForLogin() {
    _activeUserId = null;
    _guestChangedLanguage = false;
    state = const Locale('en');
  }
}

final localeControllerProvider =
    StateNotifierProvider<LocaleController, Locale>(
      (ref) => LocaleController(ref.watch(localeStorageProvider)),
    );
