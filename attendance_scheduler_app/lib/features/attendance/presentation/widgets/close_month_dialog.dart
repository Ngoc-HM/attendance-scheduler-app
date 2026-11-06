import 'package:flutter/material.dart';

import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../../auth/domain/entities/user.dart';
import '../../domain/entities/calculations_entities.dart';

/// Read-only summary shown after an admin closes a month (F-14): one row per
/// user with the carry-over balances the backend has just stored.
class CloseMonthResultDialog extends StatelessWidget {
  const CloseMonthResultDialog({
    super.key,
    required this.result,
    required this.users,
  });

  final MonthCloseResult result;

  /// Users already loaded by the attendance board — used to resolve names.
  /// Anyone missing from it (e.g. a disabled account) is shown by id.
  final List<User> users;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final byId = {for (final u in users) u.id: u};
    String nameOf(int userId) {
      final user = byId[userId];
      if (user == null) return '${l.text('user')} $userId';
      return user.fullName.isNotEmpty ? user.fullName : user.username;
    }

    final rows = [...result.balances]
      ..sort((a, b) => nameOf(a.userId).compareTo(nameOf(b.userId)));

    return DsFormDialog(
      title: l.text('closeMonthResultTitle'),
      width: 560,
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            l.monthYear(DateTime(result.year, result.month)),
            style: Theme.of(context).textTheme.titleSmall,
          ),
          const SizedBox(height: DsSpacing.x3),
          if (rows.isEmpty)
            Text(l.text('closeMonthEmpty'))
          else
            ConstrainedBox(
              constraints: const BoxConstraints(maxHeight: 360),
              child: SingleChildScrollView(
                child: DsDataTable(
                  cellPaddingH: DsSpacing.x3,
                  cellPaddingV: DsSpacing.x2,
                  columns: [
                    DsTableColumn(header: l.text('employee'), flex: 3),
                    DsTableColumn(
                      header: l.text('carryComp'),
                      flex: 2,
                      alignment: Alignment.centerRight,
                    ),
                    DsTableColumn(
                      header: l.text('carryStreak'),
                      flex: 2,
                      alignment: Alignment.centerRight,
                    ),
                    DsTableColumn(
                      header: l.text('carryPremiumOff'),
                      flex: 2,
                      alignment: Alignment.centerRight,
                    ),
                  ],
                  rows: [
                    for (final balance in rows)
                      [
                        Text(
                          nameOf(balance.userId),
                          style: DsType.tableCell,
                          overflow: TextOverflow.ellipsis,
                        ),
                        Text('${balance.carryComp}', style: DsType.tableCell),
                        Text(
                          '${balance.carryStreak}',
                          style: DsType.tableCell,
                        ),
                        Text(
                          '${balance.carryPremiumOff}',
                          style: DsType.tableCell,
                        ),
                      ],
                  ],
                ),
              ),
            ),
        ],
      ),
      actions: [
        DsPrimaryButton(
          label: l.text('close'),
          onPressed: () => Navigator.of(context).pop(),
        ),
      ],
    );
  }
}
