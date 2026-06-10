import 'package:flutter/material.dart';

import '../../../../shared/widgets/feature_placeholder.dart';

/// Core feature — auto-generated monthly schedule (spec §5 / F-07..F-09).
class SchedulePage extends StatelessWidget {
  const SchedulePage({super.key});

  @override
  Widget build(BuildContext context) {
    return const FeaturePlaceholder(
      title: 'Schedule',
      description:
          'Auto-generate the monthly roster (person × day), review balance of '
          'A/D shifts, manually adjust cells, and publish.',
      featureIds: ['F-07', 'F-08', 'F-09'],
    );
  }
}
