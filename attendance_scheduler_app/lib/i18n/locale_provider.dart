import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/storage/locale_storage.dart';

/// The language this device last showed, read once before the app starts
/// (`main.dart` overrides it). English until something was ever chosen.
final initialLanguageProvider = Provider<String>((ref) => 'en');

/// The UI language (owner 2026-11-10: "each person's app remembers that
/// person's language").
///
/// Two memories work together:
/// - the device remembers the language it last showed, so the login screen
///   opens in it after a restart or a logout instead of falling back to
///   English;
/// - each user has their own preference, applied when they log in.
class LocaleController extends StateNotifier<Locale> {
  LocaleController(this._storage, {String initialLanguage = 'en'})
    : super(Locale(_supported(initialLanguage) ? initialLanguage : 'en'));

  final LocaleStorage _storage;
  int? _activeUserId;
  bool _guestChangedLanguage = false;

  static bool _supported(String languageCode) =>
      languageCode == 'en' || languageCode == 'vi';

  /// Bind the locale to the user who has just logged in.
  ///
  /// Their stored preference wins normally. If they explicitly switched the
  /// language on the login screen, that newest choice becomes their
  /// preference. Without a preference yet, they keep the language shown.
  Future<void> activateUser(int userId) async {
    _activeUserId = userId;
    final saved = _guestChangedLanguage ? null : await _storage.read(userId);
    if (saved != null) {
      state = Locale(saved);
    } else {
      await _storage.write(userId, state.languageCode);
    }
    _guestChangedLanguage = false;
    await _storage.writeLast(state.languageCode);
  }

  Future<void> setLanguage(String languageCode) async {
    if (!_supported(languageCode)) return;
    state = Locale(languageCode);
    final userId = _activeUserId;
    if (userId == null) {
      _guestChangedLanguage = true;
    } else {
      await _storage.write(userId, languageCode);
    }
    await _storage.writeLast(languageCode);
  }

  /// Logout / session end: nobody is bound any more. The language stays as
  /// it is — the login screen keeps showing what the person was reading —
  /// and the next login applies that user's own preference.
  void resetForLogin() {
    _activeUserId = null;
    _guestChangedLanguage = false;
  }
}

final localeControllerProvider =
    StateNotifierProvider<LocaleController, Locale>(
      (ref) => LocaleController(
        ref.watch(localeStorageProvider),
        initialLanguage: ref.watch(initialLanguageProvider),
      ),
    );
