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
      // Auth / registration (F-01)
      'register': 'Register',
      'createAccount': 'Create an account',
      'backToLogin': 'Back to login',
      'fullName': 'Full name',
      'role': 'Role',
      'minThreeChars': 'At least 3 characters',
      'minSixChars': 'At least 6 characters',
      'registerPending': 'Account created. Awaiting admin approval.',
      'registerFailed': 'Registration failed. The username may be taken.',
      // User management (F-01, F-03)
      'createUser': 'Create user',
      'createUserFailed': 'Could not create the user.',
      'cancel': 'Cancel',
      'create': 'Create',
      'refresh': 'Refresh',
      'loadFailed': 'Could not load users.',
      'noUsers': 'No users yet.',
      'status': 'Status',
      'actions': 'Actions',
      'approve': 'Approve',
      'disable': 'Disable',
      'enable': 'Enable',
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
      // Auth / registration (F-01)
      'register': 'Đăng ký',
      'createAccount': 'Tạo tài khoản',
      'backToLogin': 'Quay lại đăng nhập',
      'fullName': 'Họ và tên',
      'role': 'Vai trò',
      'minThreeChars': 'Tối thiểu 3 ký tự',
      'minSixChars': 'Tối thiểu 6 ký tự',
      'registerPending': 'Đã tạo tài khoản. Chờ admin phê duyệt.',
      'registerFailed': 'Đăng ký thất bại. Tên đăng nhập có thể đã tồn tại.',
      // User management (F-01, F-03)
      'createUser': 'Tạo người dùng',
      'createUserFailed': 'Không tạo được người dùng.',
      'cancel': 'Hủy',
      'create': 'Tạo',
      'refresh': 'Tải lại',
      'loadFailed': 'Không tải được danh sách người dùng.',
      'noUsers': 'Chưa có người dùng.',
      'status': 'Trạng thái',
      'actions': 'Thao tác',
      'approve': 'Phê duyệt',
      'disable': 'Vô hiệu hóa',
      'enable': 'Kích hoạt',
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

  // Auth / registration
  String get register => _t('register');
  String get createAccount => _t('createAccount');
  String get backToLogin => _t('backToLogin');
  String get fullName => _t('fullName');
  String get role => _t('role');
  String get minThreeChars => _t('minThreeChars');
  String get minSixChars => _t('minSixChars');
  String get registerPending => _t('registerPending');
  String get registerFailed => _t('registerFailed');

  // User management
  String get createUser => _t('createUser');
  String get createUserFailed => _t('createUserFailed');
  String get cancel => _t('cancel');
  String get create => _t('create');
  String get refresh => _t('refresh');
  String get loadFailed => _t('loadFailed');
  String get noUsers => _t('noUsers');
  String get status => _t('status');
  String get actions => _t('actions');
  String get approve => _t('approve');
  String get disable => _t('disable');
  String get enable => _t('enable');
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  bool isSupported(Locale locale) => AppLocalizations.supportedLocales.any(
    (l) => l.languageCode == locale.languageCode,
  );

  @override
  Future<AppLocalizations> load(Locale locale) =>
      SynchronousFuture(AppLocalizations(locale));

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}
