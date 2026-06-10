import 'package:flutter/material.dart';

import '../../../../shared/widgets/feature_placeholder.dart';

/// User & role management (spec §3 / F-01, F-03).
class UsersPage extends StatelessWidget {
  const UsersPage({super.key});

  @override
  Widget build(BuildContext context) {
    return const FeaturePlaceholder(
      title: 'Users',
      description:
          'Create users, assign roles (M / T / A1–A4) and approve '
          'self-registered accounts.',
      featureIds: ['F-01', 'F-03'],
    );
  }
}
