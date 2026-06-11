import 'package:flutter/material.dart';

import '../../../../design_system/design_system.dart';

class LeavesPage extends StatefulWidget {
  const LeavesPage({super.key});

  @override
  State<LeavesPage> createState() => _LeavesPageState();
}

class _LeavesPageState extends State<LeavesPage> {
  List<DsLeaveRowData> _rows = const [
    DsLeaveRowData(
      employee: 'Agne',
      role: 'A1',
      type: 'Monthly leave',
      range: '06–07 Jun 2026',
      days: 2,
      status: 'Pending',
      carryComp: 2,
    ),
    DsLeaveRowData(
      employee: 'Vu Le',
      role: 'T',
      type: 'Monthly leave',
      range: '13–14 Jun 2026',
      days: 2,
      status: 'Approved',
      carryComp: 0,
    ),
    DsLeaveRowData(
      employee: 'Thomas',
      role: 'A4',
      type: 'Annual leave',
      range: '22–28 Jun 2026',
      days: 7,
      status: 'Pending',
      carryComp: 1,
    ),
    DsLeaveRowData(
      employee: 'Chi Tran',
      role: 'M',
      type: 'Compensation',
      range: '18 Jun 2026',
      days: 1,
      status: 'Approved',
      carryComp: 3,
    ),
  ];

  void _setStatus(int index, String status) {
    setState(() {
      _rows = [
        for (var itemIndex = 0; itemIndex < _rows.length; itemIndex++)
          itemIndex == index
              ? _rows[itemIndex].copyWith(status: status)
              : _rows[itemIndex],
      ];
    });
    DsFeedback.show(
      context,
      'Request ${status.toLowerCase()}.',
      tone: status == 'Approved' ? DsTone.success : DsTone.danger,
    );
  }

  @override
  Widget build(BuildContext context) {
    return DsLeavesView(
      rows: _rows,
      onNewRequest: () => showDialog<void>(
        context: context,
        builder: (dialogContext) => DsLeaveRequestDialog(
          onCancel: () => Navigator.of(dialogContext).pop(),
          onSubmit: () {
            Navigator.of(dialogContext).pop();
            DsFeedback.show(
              context,
              'Leave request submitted.',
              tone: DsTone.success,
            );
          },
        ),
      ),
      onApprove: (index) => _setStatus(index, 'Approved'),
      onReject: (index) => _setStatus(index, 'Rejected'),
    );
  }
}
