import 'package:equatable/equatable.dart';

/// Carry-over balances for one user, as stored by the backend when a month is
/// closed (F-14). They seed the next month's schedule generation.
class CarryBalance extends Equatable {
  const CarryBalance({
    required this.userId,
    required this.carryComp,
    required this.carryStreak,
    required this.carryPremiumOff,
  });

  final int userId;

  /// Outstanding compensation days (§5.4).
  final int carryComp;

  /// Consecutive working days at the month boundary (§5.5).
  final int carryStreak;

  /// Premium-off count carried into the next month.
  final int carryPremiumOff;

  @override
  List<Object?> get props => [userId, carryComp, carryStreak, carryPremiumOff];
}

/// Result of POST /calculations/{year}/{month}/close.
class MonthCloseResult extends Equatable {
  const MonthCloseResult({
    required this.year,
    required this.month,
    required this.balances,
  });

  final int year;
  final int month;

  /// One entry per user, sorted by user id.
  final List<CarryBalance> balances;

  @override
  List<Object?> get props => [year, month, balances];
}
