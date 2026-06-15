import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class LocaleController extends StateNotifier<Locale> {
  LocaleController() : super(const Locale('en'));

  void setLanguage(String languageCode) {
    if (languageCode == 'en' || languageCode == 'vi') {
      state = Locale(languageCode);
    }
  }
}

final localeControllerProvider =
    StateNotifierProvider<LocaleController, Locale>(
      (ref) => LocaleController(),
    );
