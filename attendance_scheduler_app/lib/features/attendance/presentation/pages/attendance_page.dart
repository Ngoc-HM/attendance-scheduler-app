import 'package:flutter/material.dart';

import '../../../../shared/widgets/feature_placeholder.dart';

/// Actual attendance, sick handling & holidays (spec §4.5 / F-10..F-13).
class AttendancePage extends StatelessWidget {
  const AttendancePage({super.key});

  @override
  Widget build(BuildContext context) {
    return const FeaturePlaceholder(
      title: 'Attendance',
      description:
          'Record the actual daily code per person (incl. sick S, holidays X). '
          'Admin updates leave/sick statuses and maintains public holidays.',
      featureIds: ['F-10', 'F-11', 'F-12', 'F-13'],
    );
  }
}
