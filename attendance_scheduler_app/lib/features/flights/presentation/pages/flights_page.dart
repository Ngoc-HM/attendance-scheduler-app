import 'package:flutter/material.dart';

import '../../../../shared/widgets/feature_placeholder.dart';

/// Monthly flight list — manual entry + Excel import (spec §4.2 / F-04, §8).
class FlightsPage extends StatelessWidget {
  const FlightsPage({super.key});

  @override
  Widget build(BuildContext context) {
    return const FeaturePlaceholder(
      title: 'Flights',
      description:
          'Enter the monthly flight pairs per day (0/1/2) manually or import '
          'from Excel. Drives shift staffing for the A1–A4 group.',
      featureIds: ['F-04'],
    );
  }
}
