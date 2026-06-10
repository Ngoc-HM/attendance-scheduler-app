// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Vietnamese (`vi`).
class AppLocalizationsVi extends AppLocalizations {
  AppLocalizationsVi([String locale = 'vi']) : super(locale);

  @override
  String get appTitle => 'Xếp lịch & Chấm công';

  @override
  String get login => 'Đăng nhập';

  @override
  String get logout => 'Đăng xuất';

  @override
  String get username => 'Tên đăng nhập';

  @override
  String get password => 'Mật khẩu';

  @override
  String get navSchedule => 'Lịch làm';

  @override
  String get navFlights => 'Chuyến bay';

  @override
  String get navLeaves => 'Nghỉ phép';

  @override
  String get navAttendance => 'Chấm công';

  @override
  String get navReports => 'Báo cáo';

  @override
  String get navUsers => 'Người dùng';
}
