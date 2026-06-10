import 'package:flutter/material.dart';

import '../../../../shared/widgets/feature_placeholder.dart';

/// Reports & export (spec §4.7 / F-15).
class ReportsPage extends StatelessWidget {
  const ReportsPage({super.key});

  @override
  Widget build(BuildContext context) {
    return const FeaturePlaceholder(
      title: 'Reports',
      description:
          'Export attendance by month and by year. Layout is kept flexible so '
          'new formats can be added later.',
      featureIds: ['F-15'],
    );
  }
}
