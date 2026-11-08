// UserModel mirrors the backend UserRead, including the annual leave quota
// the admin sets per person (D4).

import 'package:attendance_scheduler_app/features/auth/data/models/user_model.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('reads annual_leave_quota, 0 when an older server omits it', () {
    final withQuota = UserModel.fromJson({
      'id': 1,
      'username': 'anna',
      'role': 'T',
      'annual_leave_quota': 25,
    });
    final without = UserModel.fromJson({'id': 2, 'username': 'ben'});

    expect(withQuota.annualLeaveQuota, 25);
    expect(without.annualLeaveQuota, 0);
  });
}
