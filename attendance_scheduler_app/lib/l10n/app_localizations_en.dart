// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'Attendance & Scheduler';

  @override
  String get login => 'Log in';

  @override
  String get logout => 'Log out';

  @override
  String get username => 'Username';

  @override
  String get password => 'Password';

  @override
  String get navSchedule => 'Schedule';

  @override
  String get navFlights => 'Flights';

  @override
  String get navLeaves => 'Leaves';

  @override
  String get navAttendance => 'Attendance';

  @override
  String get navReports => 'Reports';

  @override
  String get navUsers => 'Users';
}
