import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';

/// App internationalization (i18n) — English (primary) and Vietnamese
/// (spec §2). Lightweight and codegen-free: strings live in [_values] and are
/// exposed as getters. Access with `AppLocalizations.of(context)`.
///
/// To add a string: add the key to both locales in [_values] and add a getter.
class AppLocalizations {
  const AppLocalizations(this.locale);

  final Locale locale;

  static const List<Locale> supportedLocales = [Locale('en'), Locale('vi')];

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  static AppLocalizations of(BuildContext context) =>
      Localizations.of<AppLocalizations>(context, AppLocalizations) ??
      const AppLocalizations(Locale('en'));

  static const Map<String, Map<String, String>> _values = {
    'en': {
      'appTitle': 'Attendance & Scheduler',
      'login': 'Log in',
      'logout': 'Log out',
      'username': 'Username',
      'password': 'Password',
      'fieldRequired': 'Required',
      'navSchedule': 'Schedule',
      'navFlights': 'Flights',
      'navLeaves': 'Leaves',
      'navAttendance': 'Attendance',
      'navReports': 'Reports',
      'navUsers': 'Users',
    },
    'vi': {
      'appTitle': 'Xếp lịch & Chấm công',
      'login': 'Đăng nhập',
      'logout': 'Đăng xuất',
      'username': 'Tên đăng nhập',
      'password': 'Mật khẩu',
      'fieldRequired': 'Bắt buộc',
      'navSchedule': 'Lịch làm',
      'navFlights': 'Chuyến bay',
      'navLeaves': 'Nghỉ phép',
      'navAttendance': 'Chấm công',
      'navReports': 'Báo cáo',
      'navUsers': 'Người dùng',
    },
  };

  String _t(String key) =>
      _values[locale.languageCode]?[key] ?? _values['en']![key] ?? key;

  String get appTitle => _t('appTitle');
  String get login => _t('login');
  String get logout => _t('logout');
  String get username => _t('username');
  String get password => _t('password');
  String get fieldRequired => _t('fieldRequired');
  String get navSchedule => _t('navSchedule');
  String get navFlights => _t('navFlights');
  String get navLeaves => _t('navLeaves');
  String get navAttendance => _t('navAttendance');
  String get navReports => _t('navReports');
  String get navUsers => _t('navUsers');
}

class _AppLocalizationsDelegate extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  bool isSupported(Locale locale) => AppLocalizations.supportedLocales
      .any((l) => l.languageCode == locale.languageCode);

  @override
  Future<AppLocalizations> load(Locale locale) =>
      SynchronousFuture(AppLocalizations(locale));

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}
