import 'package:flutter/material.dart';

import '../../../../shared/widgets/feature_placeholder.dart';

/// Leave registration (spec §4.3 / F-05, F-06).
class LeavesPage extends StatelessWidget {
  const LeavesPage({super.key});

  @override
  Widget build(BuildContext context) {
    return const FeaturePlaceholder(
      title: 'Leaves',
      description:
          'Register monthly leave (< 5 consecutive days) and annual leave '
          '(>= 5 days). Admins review and approve requests.',
      featureIds: ['F-05', 'F-06'],
    );
  }
}
