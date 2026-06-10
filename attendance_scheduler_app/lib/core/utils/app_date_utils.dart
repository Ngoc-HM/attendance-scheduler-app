import 'package:intl/intl.dart';

/// Date formatting helpers. Times from the backend are Frankfurt local
/// (LT FRA, spec §8).
class AppDateUtils {
  const AppDateUtils._();

  static String ymd(DateTime date) => DateFormat('yyyy-MM-dd').format(date);

  static String monthLabel(int year, int month) =>
      DateFormat('MMMM yyyy').format(DateTime(year, month));
}
