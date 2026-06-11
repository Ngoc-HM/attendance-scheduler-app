import 'package:flutter/material.dart';
import 'package:liquid_glass_bar/liquid_glass_bar.dart';

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
    return LiquidGlassBar(
      items: [
        for (final item in destinations)
          LiquidGlassBarItem(iconData: item.icon, label: item.label),
      ],
      currentIndex: currentIndex,
      onTap: onSelected,
      style: LiquidGlassBarStyle(
        activeColor: DsColors.primary,
        inactiveColor: DsColors.textMuted,
        borderRadius: DsRadius.xxLarge,
        height: 58,
        padding: const EdgeInsets.fromLTRB(12, 8, 12, 16),
        animationDuration: DsDuration.base,
        animationCurve: Curves.easeOutCubic,
        iconSize: 20,
        selectedIconScale: 1.06,
        labelStyle: Theme.of(context).textTheme.bodySmall?.copyWith(
          fontSize: 10,
          fontWeight: FontWeight.w600,
        ),
        liquidGlassSettings: LiquidGlassSettings(
          thickness: 12,
          blur: 12,
          glassColor: DsColors.surface.withValues(alpha: 0.82),
          lightIntensity: 0.35,
          refractiveIndex: 1.25,
        ),
      ),
    );
  }
}
