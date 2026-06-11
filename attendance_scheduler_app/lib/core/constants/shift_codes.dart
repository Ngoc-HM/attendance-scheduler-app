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
}
