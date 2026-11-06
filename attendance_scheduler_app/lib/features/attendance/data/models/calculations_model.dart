import '../../domain/entities/calculations_entities.dart';

/// JSON → domain converters for the calculations endpoints (F-14).
class CarryBalanceModel extends CarryBalance {
  const CarryBalanceModel({
    required super.userId,
    required super.carryComp,
    required super.carryStreak,
    required super.carryPremiumOff,
  });

  factory CarryBalanceModel.fromJson(int userId, Map<String, dynamic> json) =>
      CarryBalanceModel(
        userId: userId,
        carryComp: (json['carry_comp'] as num?)?.toInt() ?? 0,
        carryStreak: (json['carry_streak'] as num?)?.toInt() ?? 0,
        carryPremiumOff: (json['carry_premium_off'] as num?)?.toInt() ?? 0,
      );

  /// Parses the `{"<user id>": {carry_comp, carry_streak, carry_premium_off}}`
  /// shape shared by the close and summary endpoints. JSON object keys are
  /// always strings, so the id is parsed here; unparsable keys are skipped.
  static List<CarryBalanceModel> listFromUserMap(Map<String, dynamic> json) {
    final balances = <CarryBalanceModel>[
      for (final entry in json.entries)
        if (int.tryParse(entry.key) case final userId?)
          CarryBalanceModel.fromJson(
            userId,
            entry.value as Map<String, dynamic>,
          ),
    ];
    balances.sort((a, b) => a.userId.compareTo(b.userId));
    return balances;
  }
}

class MonthCloseResultModel extends MonthCloseResult {
  const MonthCloseResultModel({
    required super.year,
    required super.month,
    required super.balances,
  });

  factory MonthCloseResultModel.fromJson(Map<String, dynamic> json) =>
      MonthCloseResultModel(
        year: json['year'] as int,
        month: json['month'] as int,
        balances: CarryBalanceModel.listFromUserMap(
          (json['users'] as Map<String, dynamic>?) ?? const {},
        ),
      );
}
