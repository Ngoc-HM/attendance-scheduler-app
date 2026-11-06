import '../../features/auth/domain/entities/user.dart';

/// Attendance / shift symbols (spec §7). Kept in sync with the backend
/// `AttendanceCode` enum.
enum ShiftCode { a, d, aD, ad, x, cd, oD, t, b, s, al }

extension ShiftCodeX on ShiftCode {
  /// The symbol as shown on the board (e.g. "A/D", "O/D").
  String get code => switch (this) {
    ShiftCode.a => 'A',
    ShiftCode.d => 'D',
    ShiftCode.aD => 'A/D',
    ShiftCode.ad => 'AD',
    ShiftCode.x => 'X',
    ShiftCode.cd => 'CD',
    ShiftCode.oD => 'O/D',
    ShiftCode.t => 'T',
    ShiftCode.b => 'B',
    ShiftCode.s => 'S',
    ShiftCode.al => 'AL',
  };

  /// Whether the code counts as a working day (spec §7).
  bool get isWorking => switch (this) {
    ShiftCode.a ||
    ShiftCode.d ||
    ShiftCode.aD ||
    ShiftCode.ad ||
    ShiftCode.oD ||
    ShiftCode.t ||
    ShiftCode.b => true,
    _ => false,
  };

  /// Working-day weight (A/D counts as 2 — spec §7).
  int get workdayValue => this == ShiftCode.aD ? 2 : (isWorking ? 1 : 0);

  /// Codes a person of [role] may carry on the PLANNED roster (admin cell
  /// edit, shift-change request). Mirrors the backend planned-grid check:
  /// the role's domain plus X / T / B / AL, with A/D for role A as the
  /// emergency code. Sickness S is never offered here — it is recorded on
  /// the admin-only actual-attendance grid.
  static List<ShiftCode> plannedCodesFor(UserRole role) => switch (role) {
    UserRole.a => const [
      ShiftCode.a,
      ShiftCode.d,
      ShiftCode.aD,
      ShiftCode.x,
      ShiftCode.cd,
      ShiftCode.t,
      ShiftCode.b,
      ShiftCode.al,
    ],
    UserRole.t || UserRole.f => const [
      ShiftCode.ad,
      ShiftCode.x,
      ShiftCode.cd,
      ShiftCode.t,
      ShiftCode.b,
      ShiftCode.al,
    ],
    UserRole.m => const [
      ShiftCode.oD,
      ShiftCode.x,
      ShiftCode.cd,
      ShiftCode.t,
      ShiftCode.b,
      ShiftCode.al,
    ],
  };
}
