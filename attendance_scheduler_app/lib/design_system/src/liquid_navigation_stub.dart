import 'package:flutter/material.dart';

import '../navigation_models.dart';
import '../tokens.dart';

class DsLiquidNavigationBar extends StatelessWidget {
  const DsLiquidNavigationBar({
    super.key,
    required this.destinations,
    required this.currentIndex,
    required this.onSelected,
  });

  final List<DsNavigationDestination> destinations;
  final int currentIndex;
  final ValueChanged<int> onSelected;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.fromLTRB(12, 8, 12, 16),
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        color: DsColors.surface.withValues(alpha: 0.94),
        borderRadius: BorderRadius.circular(DsRadius.xxLarge),
        border: Border.all(color: DsColors.border),
      ),
      child: NavigationBar(
        height: 58,
        backgroundColor: Colors.transparent,
        indicatorColor: DsColors.primarySoft,
        selectedIndex: currentIndex,
        onDestinationSelected: onSelected,
        destinations: [
          for (final item in destinations)
            NavigationDestination(
              icon: Icon(item.icon, size: 20),
              label: item.label,
            ),
        ],
      ),
    );
  }
}
